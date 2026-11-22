from datetime import date, timedelta

import pytest

from app.extensions import db
from app.modules.collaborators import services
from app.modules.collaborators.events import ImmutableProfileError
from app.modules.collaborators.models import Collaborator, CollaboratorProfile
from app.modules.collaborators.rules.prolog_engine import prolog_available


def form_data(**overrides):
    data = {
        "first_name": "Oscar", "second_name": "", "last_name": "Naranjo", "second_last_name": "Zuniga",
        "birthdate": "1995-05-20", "position": "", "department": "", "email": "", "phone": "",
    }
    return {**data, **overrides}


def create(client, **overrides):
    return client.post("/collaborators/create", data=form_data(**overrides))


def only_free_the_first_time(monkeypatch, name):
    """La primera consulta dice "libre" aunque no lo este: simula que otra persona guardo justo antes."""
    real = getattr(services, name)
    calls = []

    def fake(value):
        calls.append(value)
        return False if len(calls) == 1 else real(value)

    monkeypatch.setattr(services, name, fake)


@pytest.fixture
def dcc(login_as):
    return login_as("dcc")


def test_rrhh_cannot_create(client, login_as):
    login_as("rrhh")
    assert create(client).status_code == 403


def test_create_saves_collaborator_and_profile(client, dcc):
    response = create(client, position="Analista", email="Oscar@Empresa.com")

    collaborator = db.session.scalars(db.select(Collaborator)).one()
    assert response.headers["Location"] == "/collaborators/create"
    assert collaborator.profile.initials == "ONZ"
    assert collaborator.profile.signature == "ONaranjo"
    assert collaborator.profile.position == "Analista"
    assert collaborator.profile.email == "oscar@empresa.com"
    assert collaborator.is_active


def test_after_creating_the_form_is_empty_with_a_toast_and_the_recent_list(client, dcc):
    html = client.post("/collaborators/create", data=form_data(), follow_redirects=True).get_data(as_text=True)
    collaborator = db.session.scalars(db.select(Collaborator)).one()

    assert 'class="toast vidrio"' in html
    assert "Colaborador creado" in html and "Oscar Naranjo Zuniga" in html
    assert "<small>Iniciales</small> ONZ" in html and "<small>Firma</small> ONaranjo" in html
    assert 'id="first_name"' in html and 'value="Oscar"' not in html
    assert 'class="reciente-nuevo"' in html
    assert f'href="/collaborators/{collaborator.id_collab}"' in html

    html = client.get("/collaborators/create").get_data(as_text=True)
    assert 'class="toast vidrio"' not in html
    assert 'class="reciente-nuevo"' not in html
    assert "ONZ · ONaranjo" in html


def test_recent_list_is_empty_at_first(client, dcc):
    assert "Todavía no hay colaboradores" in client.get("/collaborators/create").get_data(as_text=True)


def test_names_are_saved_capitalized(client, dcc):
    create(client, first_name="oScAr", second_name="   ", last_name="de LA o", second_last_name="lópez")

    collaborator = db.session.scalars(db.select(Collaborator)).one()
    assert (collaborator.first_name, collaborator.second_name) == ("Oscar", None)
    assert (collaborator.last_name, collaborator.second_last_name) == ("De La O", "Lopez")
    assert (collaborator.profile.initials, collaborator.profile.signature) == ("ODL", "ODelao")


def test_names_are_saved_without_accents_or_special_characters(client, dcc):
    create(
        client, first_name="Josué", second_name="Ángel", last_name="o'neil", second_last_name="Zúñiga",
        position="Analista de Gestión", department="Tecnología",
    )

    collaborator = db.session.scalars(db.select(Collaborator)).one()
    assert collaborator.full_name == "Josue Angel Oneil Zuniga"
    assert (collaborator.profile.position, collaborator.profile.department) == ("Analista de Gestion", "Tecnologia")
    assert (collaborator.profile.initials, collaborator.profile.signature) == ("JOZ", "JOneil")


def test_same_name_gets_the_next_free_values(client, dcc):
    create(client)
    create(client)

    profiles = db.session.scalars(db.select(CollaboratorProfile).order_by(CollaboratorProfile.id_profile)).all()
    assert [(p.initials, p.signature) for p in profiles] == [("ONZ", "ONaranjo"), ("ONZ1", "ONaranjoZ")]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"last_name": "O"}, "El primer apellido debe tener al menos 2 letras."),
        ({"first_name": "A"}, "El primer nombre debe tener al menos 2 letras."),
        ({"birthdate": (date.today() + timedelta(days=1)).isoformat()}, "La fecha de nacimiento no puede ser futura."),
        ({"birthdate": ""}, "Elige la fecha de nacimiento."),
        ({"email": "no-es-correo"}, "Escribe un correo válido."),
        ({"phone": "llamar luego"}, "Usa solo números"),
    ],
)
def test_invalid_data_saves_nothing(client, dcc, overrides, message):
    html = create(client, **overrides).get_data(as_text=True)

    assert message in html
    assert db.session.query(Collaborator).count() == 0


def test_hyphen_without_second_last_name_asks_for_confirmation(client, dcc):
    html = create(client, last_name="Pérez-Soto", second_last_name="").get_data(as_text=True)
    assert "Parece que escribiste dos apellidos en un campo." in html
    assert 'name="single_last_name"' in html
    assert db.session.query(Collaborator).count() == 0

    create(client, last_name="Pérez-Soto", second_last_name="", single_last_name="y")
    profile = db.session.scalars(db.select(CollaboratorProfile)).one()
    assert (profile.initials, profile.signature) == ("OPE", "OPerezsoto")
    assert profile.collaborator.last_name == "Perez Soto"


def test_hyphen_with_second_last_name_needs_no_confirmation(client, dcc):
    create(client, last_name="Pérez-Soto", second_last_name="Mora")
    assert db.session.query(Collaborator).count() == 1


def test_hyphen_in_first_name_asks_for_confirmation(client, dcc):
    html = create(client, first_name="María-José").get_data(as_text=True)
    assert "Parece que escribiste dos nombres en un campo." in html
    assert 'name="single_first_name"' in html


def test_duplicate_email_is_rejected(client, dcc):
    create(client, email="oscar@empresa.com")
    html = create(client, email="OSCAR@empresa.com").get_data(as_text=True)

    assert "Ese correo ya pertenece a otro colaborador." in html
    assert db.session.query(Collaborator).count() == 1


def test_email_race_shows_the_error_in_the_form(client, dcc, monkeypatch):
    create(client, email="oscar@empresa.com")
    only_free_the_first_time(monkeypatch, "email_taken")
    html = create(client, email="oscar@empresa.com").get_data(as_text=True)

    assert "Ese correo ya pertenece a otro colaborador." in html
    assert db.session.query(Collaborator).count() == 1


def test_initials_race_is_retried_with_the_next_value(app, monkeypatch):
    services.create_collaborator("Oscar", "Naranjo", date(1995, 5, 20), second_last_name="Zuniga")
    only_free_the_first_time(monkeypatch, "initials_taken")

    collaborator = services.create_collaborator("Oscar", "Naranjo", date(1990, 1, 1), second_last_name="Zuniga")

    assert collaborator.profile.initials == "ONZ1"
    assert db.session.query(Collaborator).count() == 2


def test_gives_up_after_several_collisions(client, dcc, monkeypatch):
    create(client)
    monkeypatch.setattr(services, "initials_taken", lambda value: False)
    html = create(client).get_data(as_text=True)

    assert "No se pudieron generar Iniciales y Firma libres" in html
    assert db.session.query(Collaborator).count() == 1


def test_initials_and_signature_cannot_change(app):
    collaborator = services.create_collaborator("Oscar", "Naranjo", date(1995, 5, 20))
    profile = collaborator.profile

    profile.position = "Analista"
    db.session.commit()

    for field in ("initials", "signature"):
        setattr(profile, field, "OTRO")
        with pytest.raises(ImmutableProfileError):
            db.session.commit()
        db.session.rollback()
    assert (profile.initials, profile.signature) == ("ONA", "ONaranjo")


def test_read_is_available_to_every_role(client, login_as):
    collaborator = services.create_collaborator("Oscar", "Naranjo", date(1995, 5, 20))
    login_as("rrhh")

    assert client.get(f"/collaborators/{collaborator.id_collab}").status_code == 200
    assert client.get("/collaborators/999").status_code == 404


@pytest.mark.skipif(not prolog_available(), reason="SWI-Prolog no esta instalado")
def test_prolog_engine_creates_the_same_values(app, client, dcc):
    app.config["RULES_ENGINE"] = "prolog"
    create(client)
    create(client, last_name="De la O", second_last_name="López")

    profiles = db.session.scalars(db.select(CollaboratorProfile).order_by(CollaboratorProfile.id_profile)).all()
    assert [(p.initials, p.signature) for p in profiles] == [("ONZ", "ONaranjo"), ("ODL", "ODelao")]
