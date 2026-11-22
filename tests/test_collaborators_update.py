from datetime import date, datetime

import pytest

from app.extensions import db
from app.modules.collaborators import services
from app.modules.collaborators.models import Collaborator
from tests.test_collaborators_create import form_data, only_free_the_first_time


@pytest.fixture
def oscar(app):
    return services.create_collaborator(
        "Oscar", "Naranjo", date(1995, 5, 20), second_last_name="Zuniga", position="Analista", email="oscar@empresa.com"
    )


def update(client, collaborator, **overrides):
    return client.post(f"/collaborators/{collaborator.id_collab}/update", data=form_data(**overrides))


def reload(collaborator):
    db.session.expire_all()
    return db.session.get(Collaborator, collaborator.id_collab)


@pytest.mark.parametrize("role, status_code", [("admin", 200), ("dcc", 200), ("rrhh", 403)])
def test_only_admin_and_dcc_can_edit(client, login_as, oscar, role, status_code):
    login_as(role)
    assert client.get(f"/collaborators/{oscar.id_collab}/update").status_code == status_code
    assert update(client, oscar, first_name="Pedro").status_code == (302 if status_code == 200 else 403)


def test_edit_form_starts_with_the_current_data(client, login_as, oscar):
    login_as("dcc")
    html = client.get(f"/collaborators/{oscar.id_collab}/update").get_data(as_text=True)

    for value in ("Oscar", "Naranjo", "Zuniga", "1995-05-20", "Analista", "oscar@empresa.com"):
        assert f'value="{value}"' in html
    assert "ONZ" in html and "ONaranjo" in html


def test_edit_changes_data_but_never_initials_or_signature(client, login_as, oscar):
    login_as("dcc")
    response = update(
        client, oscar, first_name="pedro", second_name="josé", last_name="mora", second_last_name="",
        birthdate="1990-01-15", position="Gerente de Tecnología", department="TI", email="PEDRO@empresa.com",
        phone="+506 8888-8888",
    )

    assert response.headers["Location"] == f"/collaborators/{oscar.id_collab}"
    edited = reload(oscar)
    assert edited.full_name == "Pedro Jose Mora"
    assert edited.birthdate == date(1990, 1, 15)
    profile = edited.profile
    assert (profile.position, profile.department) == ("Gerente de Tecnologia", "TI")
    assert (profile.email, profile.phone) == ("pedro@empresa.com", "+506 8888-8888")
    assert (profile.initials, profile.signature) == ("ONZ", "ONaranjo")


def test_clearing_optional_fields_saves_them_empty(client, login_as, oscar):
    login_as("dcc")
    update(client, oscar, second_last_name="", position="", email="")

    edited = reload(oscar)
    assert (edited.second_last_name, edited.profile.position, edited.profile.email) == (None, None, None)


def test_a_collaborator_can_keep_its_own_email(client, login_as, oscar):
    login_as("dcc")
    assert update(client, oscar, email="OSCAR@empresa.com").status_code == 302


def test_email_of_another_collaborator_is_rejected(client, login_as, oscar):
    services.create_collaborator("Ana", "Mora", date(1990, 1, 1), email="ana@empresa.com")
    login_as("dcc")
    html = update(client, oscar, email="ana@empresa.com").get_data(as_text=True)

    assert "Ese correo ya pertenece a otro colaborador." in html
    assert reload(oscar).profile.email == "oscar@empresa.com"


def test_email_race_on_edit_shows_the_error(client, login_as, oscar, monkeypatch):
    services.create_collaborator("Ana", "Mora", date(1990, 1, 1), email="ana@empresa.com")
    login_as("dcc")
    only_free_the_first_time(monkeypatch, "email_taken")
    html = update(client, oscar, email="ana@empresa.com").get_data(as_text=True)

    assert "Ese correo ya pertenece a otro colaborador." in html
    assert reload(oscar).profile.email == "oscar@empresa.com"


def test_edit_uses_the_same_validations(client, login_as, oscar):
    login_as("dcc")
    html = update(client, oscar, last_name="O").get_data(as_text=True)
    assert "El primer apellido debe tener al menos 2 letras." in html

    html = update(client, oscar, last_name="Perez-Soto", second_last_name="").get_data(as_text=True)
    assert "Parece que escribiste dos apellidos en un campo." in html
    assert reload(oscar).last_name == "Naranjo"


@pytest.mark.parametrize("role", ["admin", "dcc", "rrhh"])
def test_every_role_can_deactivate_and_activate(client, login_as, oscar, role):
    login_as(role)

    html = client.post(f"/collaborators/{oscar.id_collab}/deactivate", follow_redirects=True).get_data(as_text=True)
    assert "Oscar Naranjo Zuniga quedó inactivo." in html
    assert not reload(oscar).is_active

    client.post(f"/collaborators/{oscar.id_collab}/activate")
    assert reload(oscar).is_active


def test_deactivated_collaborator_leaves_the_default_list(client, login_as, oscar):
    login_as("rrhh")
    client.post(f"/collaborators/{oscar.id_collab}/deactivate")

    assert f'href="/collaborators/{oscar.id_collab}"' not in client.get("/collaborators/").get_data(as_text=True)
    assert f'href="/collaborators/{oscar.id_collab}"' in client.get("/collaborators/?status=inactive").get_data(as_text=True)
    assert db.session.query(Collaborator).count() == 1


def test_status_changes_require_post(client, login_as, oscar):
    login_as("rrhh")
    for action in ("activate", "deactivate"):
        assert client.get(f"/collaborators/{oscar.id_collab}/{action}").status_code == 405


@pytest.mark.parametrize("url", ["/collaborators/999/update"])
def test_unknown_collaborator_returns_404(client, login_as, url):
    login_as("dcc")
    assert client.get(url).status_code == 404
    assert client.post("/collaborators/999/deactivate").status_code == 404


def test_detail_shows_edit_only_to_admin_and_dcc(client, login_as, oscar):
    login_as("rrhh")
    html = client.get(f"/collaborators/{oscar.id_collab}").get_data(as_text=True)
    assert f'href="/collaborators/{oscar.id_collab}/update"' not in html
    assert f'action="/collaborators/{oscar.id_collab}/deactivate"' in html


@pytest.mark.parametrize(
    "changes",
    [{"department": "Finanzas"}, {"first_name": "Pedro"}],
    ids=["solo-perfil", "solo-datos-personales"],
)
def test_last_modified_changes_after_any_edit(client, login_as, oscar, changes):
    long_ago = datetime(2020, 1, 1, 8, 0)
    oscar.updated_at = oscar.profile.updated_at = long_ago
    db.session.commit()
    login_as("dcc")

    update(client, oscar, **changes)

    assert reload(oscar).last_modified > long_ago
    html = client.get(f"/collaborators/{oscar.id_collab}").get_data(as_text=True)
    assert date.today().strftime("%d/%m/%Y") in html.split("Última modificación")[1]


def test_birthdate_can_be_removed_and_added_back(client, login_as, oscar):
    login_as("dcc")

    update(client, oscar, birthdate="")
    assert reload(oscar).birthdate is None

    update(client, oscar, birthdate="1995-05-20")
    assert reload(oscar).birthdate == date(1995, 5, 20)
