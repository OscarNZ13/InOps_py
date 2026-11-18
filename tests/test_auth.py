from app.extensions import db
from app.modules.auth import services
from app.modules.auth.models import User


def register(client, username="ana", password="clave-segura", confirm=None):
    return client.post(
        "/register",
        data={
            "register-username": username,
            "register-password": password,
            "register-confirm_password": confirm or password,
        },
    )


def login(client, username="ana", password="clave-segura", **kwargs):
    return client.post(
        "/login",
        data={"login-username": username, "login-password": password},
        **kwargs,
    )


def test_index_without_session_shows_access(client):
    html = client.get("/").get_data(as_text=True)
    assert "Iniciar sesión" in html and "Registrarse" in html


def test_register_creates_user_with_hash(client, app):
    response = register(client)
    assert response.status_code == 302

    user = services.find_by_username("ana")
    assert user is not None
    assert user.password_hash != "clave-segura"
    assert user.check_password("clave-segura")
    assert user.role.name == "rrhh"


def test_register_logs_in(client):
    register(client, username="ana")
    html = client.get("/").get_data(as_text=True)
    assert "Hola, ana" in html


def test_register_rejects_duplicate_username(client):
    register(client, username="ana")
    client.post("/logout")
    html = register(client, username="ANA").get_data(as_text=True)
    assert "Ese usuario ya existe." in html
    assert db.session.query(User).count() == 1


def test_register_rejects_mismatched_passwords(client):
    html = register(client, password="clave-segura", confirm="otra-clave").get_data(as_text=True)
    assert "Las contraseñas no coinciden." in html
    assert db.session.query(User).count() == 0


def test_register_rejects_short_password(client):
    html = register(client, password="corta").get_data(as_text=True)
    assert "al menos 8 caracteres" in html


def test_login_success(client, app):
    services.create_user("ana", "clave-segura")
    html = login(client, follow_redirects=True).get_data(as_text=True)
    assert "Hola, ana" in html


def test_login_wrong_password(client, app):
    services.create_user("ana", "clave-segura")
    html = login(client, password="equivocada").get_data(as_text=True)
    assert "Usuario o contraseña incorrectos." in html
    assert "Hola, ana" not in client.get("/").get_data(as_text=True)


def test_login_inactive_user(client, app):
    user = services.create_user("ana", "clave-segura")
    user.is_active = False
    db.session.commit()
    html = login(client).get_data(as_text=True)
    assert "inactivo" in html


def test_login_ignores_external_next(client, app):
    services.create_user("ana", "clave-segura")
    response = client.post(
        "/login?next=https://otro-sitio.com",
        data={"login-username": "ana", "login-password": "clave-segura"},
    )
    assert response.headers["Location"] == "/"


def test_logout(client, app):
    services.create_user("ana", "clave-segura")
    login(client)
    html = client.post("/logout", follow_redirects=True).get_data(as_text=True)
    assert "Cerraste sesión." in html
    assert "Hola, ana" not in html
