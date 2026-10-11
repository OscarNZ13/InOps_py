import pytest

from app.extensions import db
from app.modules.auth import services

ID_ROLES = {"admin": 1, "rrhh": 2, "dcc": 3}


def entrar_como(client, rol):
    usuario = services.crear_usuario(f"usuario-{rol}", "clave-segura")
    usuario.id_role = ID_ROLES[rol]
    db.session.commit()
    client.post("/login", data={"login-username": usuario.username, "login-password": "clave-segura"})


@pytest.mark.parametrize(
    "rol, visibles, ocultos",
    [
        ("admin", ["Lista de colaboradores", "Nuevo colaborador", "Carga inicial", "Usuarios"], []),
        ("dcc", ["Lista de colaboradores", "Nuevo colaborador", "Carga inicial"], ["Usuarios"]),
        ("rrhh", ["Lista de colaboradores"], ["Nuevo colaborador", "Carga inicial", "Usuarios"]),
    ],
)
def test_tarjetas_segun_rol(client, app, rol, visibles, ocultos):
    entrar_como(client, rol)
    html = client.get("/").get_data(as_text=True)
    for titulo in visibles:
        assert f"<h2>{titulo}</h2>" in html
    for titulo in ocultos:
        assert f"<h2>{titulo}</h2>" not in html


def test_modulos_sin_ruta_aparecen_como_proximamente(client, app):
    entrar_como(client, "admin")
    html = client.get("/").get_data(as_text=True)
    assert html.count("Próximamente") == 2


def test_paginas_de_colaboradores_exigen_sesion(client):
    for url in ("/colaboradores/", "/colaboradores/nuevo"):
        respuesta = client.get(url)
        assert respuesta.status_code == 302
        assert "/login" in respuesta.headers["Location"]


@pytest.mark.parametrize("rol, codigo", [("admin", 200), ("dcc", 200), ("rrhh", 403)])
def test_nuevo_colaborador_restringido_por_rol(client, app, rol, codigo):
    entrar_como(client, rol)
    respuesta = client.get("/colaboradores/nuevo")
    assert respuesta.status_code == codigo
    if codigo == 403:
        assert "Acceso denegado" in respuesta.get_data(as_text=True)


@pytest.mark.parametrize("rol", ["admin", "dcc", "rrhh"])
def test_lista_disponible_para_todos(client, app, rol):
    entrar_como(client, rol)
    html = client.get("/colaboradores/").get_data(as_text=True)
    assert 'role="search"' in html
    for opcion in ("nombre", "iniciales", "firma", "activos", "inactivos", "todos"):
        assert f'value="{opcion}"' in html
