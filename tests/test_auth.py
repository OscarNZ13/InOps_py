from app.extensions import db
from app.modules.auth import services
from app.modules.auth.models import User


def registrar(client, username="ana", password="clave-segura", confirmar=None):
    return client.post(
        "/register",
        data={
            "register-username": username,
            "register-password": password,
            "register-confirmar_password": confirmar or password,
        },
    )


def iniciar_sesion(client, username="ana", password="clave-segura", **kwargs):
    return client.post(
        "/login",
        data={"login-username": username, "login-password": password},
        **kwargs,
    )


def test_index_sin_sesion_muestra_acceso(client):
    html = client.get("/").get_data(as_text=True)
    assert "Iniciar sesión" in html and "Registrarse" in html


def test_registro_crea_usuario_con_hash(client, app):
    respuesta = registrar(client)
    assert respuesta.status_code == 302

    usuario = services.buscar_por_username("ana")
    assert usuario is not None
    assert usuario.password_hash != "clave-segura"
    assert usuario.check_password("clave-segura")
    assert usuario.role.name == "rrhh"


def test_registro_inicia_sesion(client):
    registrar(client, username="ana")
    html = client.get("/").get_data(as_text=True)
    assert "Hola, ana" in html


def test_registro_rechaza_usuario_repetido(client):
    registrar(client, username="ana")
    client.post("/logout")
    html = registrar(client, username="ANA").get_data(as_text=True)
    assert "Ese usuario ya existe." in html
    assert db.session.query(User).count() == 1


def test_registro_rechaza_contrasenas_distintas(client):
    html = registrar(client, password="clave-segura", confirmar="otra-clave").get_data(as_text=True)
    assert "Las contraseñas no coinciden." in html
    assert db.session.query(User).count() == 0


def test_registro_rechaza_contrasena_corta(client):
    html = registrar(client, password="corta").get_data(as_text=True)
    assert "al menos 8 caracteres" in html


def test_login_correcto(client, app):
    services.crear_usuario("ana", "clave-segura")
    html = iniciar_sesion(client, follow_redirects=True).get_data(as_text=True)
    assert "Hola, ana" in html


def test_login_contrasena_incorrecta(client, app):
    services.crear_usuario("ana", "clave-segura")
    html = iniciar_sesion(client, password="equivocada").get_data(as_text=True)
    assert "Usuario o contraseña incorrectos." in html
    assert "Hola, ana" not in client.get("/").get_data(as_text=True)


def test_login_usuario_inactivo(client, app):
    usuario = services.crear_usuario("ana", "clave-segura")
    usuario.is_active = False
    db.session.commit()
    html = iniciar_sesion(client).get_data(as_text=True)
    assert "inactivo" in html


def test_login_ignora_next_externo(client, app):
    services.crear_usuario("ana", "clave-segura")
    respuesta = client.post(
        "/login?next=https://otro-sitio.com",
        data={"login-username": "ana", "login-password": "clave-segura"},
    )
    assert respuesta.headers["Location"] == "/"


def test_logout(client, app):
    services.crear_usuario("ana", "clave-segura")
    iniciar_sesion(client)
    html = client.post("/logout", follow_redirects=True).get_data(as_text=True)
    assert "Cerraste sesión." in html
    assert "Hola, ana" not in html
