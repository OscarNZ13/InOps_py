import re

import pytest

from app.extensions import db
from app.modules.auth import services
from app.modules.auth.models import User

ROLE_ADMIN, ROLE_RRHH, ROLE_DCC = 1, 2, 3


def update_data(username, id_role, password="", confirm=None):
    return {
        "username": username,
        "id_role": id_role,
        "password": password,
        "confirm_password": password if confirm is None else confirm,
    }


# --- Acceso ---


def test_users_pages_require_login(client):
    for url in ("/users/", "/users/create", "/users/1", "/users/1/update"):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


@pytest.mark.parametrize("role", ["dcc", "rrhh"])
def test_users_pages_forbidden_for_non_admin(client, login_as, role):
    user = login_as(role)
    for url in ("/users/", "/users/create", f"/users/{user.id_user}", f"/users/{user.id_user}/update"):
        response = client.get(url)
        assert response.status_code == 403
        assert "Acceso denegado" in response.get_data(as_text=True)
    for action in ("activate", "deactivate"):
        assert client.post(f"/users/{user.id_user}/{action}").status_code == 403


def test_home_card_links_to_users(client, login_as):
    login_as("admin")
    html = client.get("/").get_data(as_text=True)
    assert 'href="/users/"' in html


# --- list y read ---


def test_list_shows_every_user_with_role_and_status(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")
    ana.is_active = False
    db.session.commit()

    html = client.get("/users/").get_data(as_text=True)
    assert "usuario-admin" in html and "ana" in html
    assert "Administrador del sistema" in html and "Recursos Humanos" in html
    assert "Activo" in html and "Inactivo" in html
    assert f'href="/users/{ana.id_user}"' in html
    assert 'href="/users/create"' in html


def test_read_shows_user_detail(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    html = client.get(f"/users/{ana.id_user}").get_data(as_text=True)
    assert "<h1>ana</h1>" in html
    assert "Recursos Humanos" in html
    assert f'href="/users/{ana.id_user}/update"' in html
    assert f'action="/users/{ana.id_user}/deactivate"' in html


def test_read_hides_deactivate_for_own_user(client, login_as):
    admin = login_as("admin")
    html = client.get(f"/users/{admin.id_user}").get_data(as_text=True)
    assert "/deactivate" not in html


@pytest.mark.parametrize("url", ["/users/999", "/users/999/update"])
def test_unknown_user_returns_404(client, login_as, url):
    login_as("admin")
    assert client.get(url).status_code == 404


# --- create ---


def test_create_user_with_chosen_role(client, login_as):
    login_as("admin")
    response = client.post(
        "/users/create",
        data={"username": "luis", "password": "clave-segura", "confirm_password": "clave-segura", "id_role": ROLE_DCC},
    )

    luis = services.find_by_username("luis")
    assert response.status_code == 302
    assert response.headers["Location"] == f"/users/{luis.id_user}"
    assert luis.role.name == "dcc"
    assert luis.is_active
    assert luis.check_password("clave-segura")


def test_create_rejects_duplicate_username(client, login_as):
    login_as("admin")
    services.create_user("luis", "clave-segura")
    html = client.post(
        "/users/create",
        data={"username": "LUIS", "password": "clave-segura", "confirm_password": "clave-segura", "id_role": ROLE_DCC},
    ).get_data(as_text=True)

    assert "Ese usuario ya existe." in html
    assert db.session.query(User).count() == 2


def test_create_validates_password(client, login_as):
    login_as("admin")
    html = client.post(
        "/users/create",
        data={"username": "luis", "password": "corta", "confirm_password": "otra", "id_role": ROLE_DCC},
    ).get_data(as_text=True)

    assert "al menos 8 caracteres" in html
    assert services.find_by_username("luis") is None


# --- update ---


def test_update_changes_username_and_role_keeping_password(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    response = client.post(f"/users/{ana.id_user}/update", data=update_data("ana.dcc", ROLE_DCC))

    assert response.headers["Location"] == f"/users/{ana.id_user}"
    assert ana.username == "ana.dcc"
    assert ana.role.name == "dcc"
    assert ana.check_password("clave-segura")


def test_update_changes_password_when_given(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    client.post(f"/users/{ana.id_user}/update", data=update_data("ana", ROLE_RRHH, password="nueva-clave"))

    assert ana.check_password("nueva-clave")


def test_update_rejects_mismatched_passwords(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    html = client.post(
        f"/users/{ana.id_user}/update", data=update_data("ana", ROLE_RRHH, password="nueva-clave", confirm="otra")
    ).get_data(as_text=True)

    assert "Las contraseñas no coinciden." in html
    assert ana.check_password("clave-segura")


def test_update_rejects_username_of_another_user(client, login_as):
    login_as("admin")
    services.create_user("luis", "clave-segura")
    ana = services.create_user("ana", "clave-segura")

    html = client.post(f"/users/{ana.id_user}/update", data=update_data("Luis", ROLE_RRHH)).get_data(as_text=True)

    assert "Ese usuario ya existe." in html
    assert ana.username == "ana"


def test_update_allows_keeping_own_username(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    response = client.post(f"/users/{ana.id_user}/update", data=update_data("ana", ROLE_DCC))

    assert response.status_code == 302
    assert ana.role.name == "dcc"


def test_admin_cannot_remove_own_admin_role(client, login_as):
    admin = login_as("admin")

    html = client.post(
        f"/users/{admin.id_user}/update", data=update_data(admin.username, ROLE_RRHH)
    ).get_data(as_text=True)

    assert "No puedes quitarte el rol de administrador." in html
    assert admin.role.name == "admin"


# --- activate / deactivate ---


def test_deactivate_and_activate_user(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")

    response = client.post(f"/users/{ana.id_user}/deactivate", follow_redirects=True)
    assert "Usuario ana desactivado." in response.get_data(as_text=True)
    assert not ana.is_active

    response = client.post(f"/users/{ana.id_user}/activate", follow_redirects=True)
    assert "Usuario ana activado." in response.get_data(as_text=True)
    assert ana.is_active


def test_admin_cannot_deactivate_self(client, login_as):
    admin = login_as("admin")

    html = client.post(f"/users/{admin.id_user}/deactivate", follow_redirects=True).get_data(as_text=True)

    assert "No puedes desactivar tu propio usuario." in html
    assert admin.is_active


def test_status_changes_require_post(client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")
    for action in ("activate", "deactivate"):
        assert client.get(f"/users/{ana.id_user}/{action}").status_code == 405


def test_deactivated_user_loses_open_session(app, client, login_as):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")
    ana_client = app.test_client()
    ana_client.post("/login", data={"login-username": "ana", "login-password": "clave-segura"})
    assert "Hola, ana" in ana_client.get("/").get_data(as_text=True)

    client.post(f"/users/{ana.id_user}/deactivate")

    response = ana_client.get("/collaborators/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert "Hola, ana" not in ana_client.get("/").get_data(as_text=True)


# --- filtros de la lista ---


@pytest.fixture
def sample_users(login_as):
    admin = login_as("admin")
    ana = services.create_user("Ana", "clave-segura", ROLE_RRHH)
    andres = services.create_user("andres", "clave-segura", ROLE_DCC)
    luis = services.create_user("luis", "clave-segura", ROLE_DCC)
    andres.is_active = False
    db.session.commit()
    return {"admin": admin, "ana": ana, "andres": andres, "luis": luis}


def listed(client, query, users):
    """Nombres (claves de `users`) que aparecen como fila en la lista con esos filtros."""
    html = client.get(f"/users/{query}").get_data(as_text=True)
    return {name for name, user in users.items() if f'href="/users/{user.id_user}"' in html}


def test_list_without_filters_shows_everyone(client, sample_users):
    assert listed(client, "", sample_users) == {"admin", "ana", "andres", "luis"}


def test_filter_by_name_is_partial_and_case_insensitive(client, sample_users):
    assert listed(client, "?q=AN", sample_users) == {"ana", "andres"}


def test_filter_by_role(client, sample_users):
    assert listed(client, "?role=dcc", sample_users) == {"andres", "luis"}
    assert listed(client, "?role=admin", sample_users) == {"admin"}


def test_filter_by_status(client, sample_users):
    assert listed(client, "?status=active", sample_users) == {"admin", "ana", "luis"}
    assert listed(client, "?status=inactive", sample_users) == {"andres"}


def test_filters_combine(client, sample_users):
    assert listed(client, "?q=an&role=dcc&status=inactive", sample_users) == {"andres"}
    assert listed(client, "?q=an&status=active", sample_users) == {"ana"}


def test_unknown_filter_values_are_ignored(client, sample_users):
    assert listed(client, "?role=nada&status=raro", sample_users) == {"admin", "ana", "andres", "luis"}


def test_search_wildcards_are_literal(client, sample_users):
    assert listed(client, "?q=%25", sample_users) == set()
    html = client.get("/users/?q=_").get_data(as_text=True)
    assert "Ningún usuario coincide con los filtros." in html


def test_filters_are_kept_in_the_form(client, sample_users):
    html = client.get("/users/?q=an&role=dcc&status=inactive").get_data(as_text=True)
    assert 'value="an"' in html
    assert re.search(r'value="dcc"\s+selected', html)
    assert re.search(r'value="inactive"\s+checked', html)


def test_count_and_clear_link(client, sample_users):
    html = client.get("/users/").get_data(as_text=True)
    assert "4 usuarios" in html
    assert "Limpiar filtros" not in html

    html = client.get("/users/?status=inactive").get_data(as_text=True)
    assert "1 usuario" in html
    assert "Limpiar filtros" in html
