import pytest


@pytest.mark.parametrize(
    "role, visible, hidden",
    [
        ("admin", ["Lista de colaboradores", "Nuevo colaborador", "Carga inicial", "Usuarios"], []),
        ("dcc", ["Lista de colaboradores", "Nuevo colaborador", "Carga inicial"], ["Usuarios"]),
        ("rrhh", ["Lista de colaboradores"], ["Nuevo colaborador", "Carga inicial", "Usuarios"]),
    ],
)
def test_cards_by_role(client, login_as, role, visible, hidden):
    login_as(role)
    html = client.get("/").get_data(as_text=True)
    for title in visible:
        assert f"<h2>{title}</h2>" in html
    for title in hidden:
        assert f"<h2>{title}</h2>" not in html


def test_modules_without_route_show_coming_soon(client, login_as):
    login_as("admin")
    html = client.get("/").get_data(as_text=True)
    assert html.count("Próximamente") == 1


def test_collaborator_pages_require_login(client):
    for url in ("/collaborators/", "/collaborators/create"):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


@pytest.mark.parametrize("role, status_code", [("admin", 200), ("dcc", 200), ("rrhh", 403)])
def test_create_collaborator_restricted_by_role(client, login_as, role, status_code):
    login_as(role)
    response = client.get("/collaborators/create")
    assert response.status_code == status_code
    if status_code == 403:
        assert "Acceso denegado" in response.get_data(as_text=True)


@pytest.mark.parametrize("role", ["admin", "dcc", "rrhh"])
def test_list_available_to_all_roles(client, login_as, role):
    login_as(role)
    html = client.get("/collaborators/").get_data(as_text=True)
    assert 'role="search"' in html
    for option in ("name", "initials", "signature", "active", "inactive", "all"):
        assert f'value="{option}"' in html
