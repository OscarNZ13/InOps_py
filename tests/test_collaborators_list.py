import re
from datetime import date

import pytest

from app.extensions import db
from app.modules.collaborators import services


@pytest.fixture
def people(app):
    def add(first, last, second_last=None, second_name=None, active=True):
        collaborator = services.create_collaborator(
            first, last, date(1990, 1, 1), second_name=second_name, second_last_name=second_last
        )
        collaborator.is_active = active
        db.session.commit()
        return collaborator

    return {
        "oscar": add("Oscar", "Naranjo", "Zúñiga"),
        "oscar2": add("Oscar", "Naranjo", "Zuniga"),
        "ana": add("Ana", "Oneil", second_name="Lucia"),
        "luis": add("Luis", "Mora", active=False),
    }


def listed(client, query, people):
    html = client.get(f"/collaborators/{query}").get_data(as_text=True)
    return {name for name, person in people.items() if f'href="/collaborators/{person.id_collab}"' in html}


@pytest.fixture
def signed_in(client, login_as):
    login_as("rrhh")
    return client


def test_default_shows_only_active_collaborators(signed_in, people):
    assert listed(signed_in, "", people) == {"oscar", "oscar2", "ana"}


def test_filter_by_status(signed_in, people):
    assert listed(signed_in, "?status=inactive", people) == {"luis"}
    assert listed(signed_in, "?status=all", people) == {"oscar", "oscar2", "ana", "luis"}


def test_name_search_is_partial_and_ignores_case_and_accents(signed_in, people):
    assert listed(signed_in, "?by=name&q=ZÚÑ", people) == {"oscar", "oscar2"}
    assert listed(signed_in, "?by=name&q=lucía", people) == {"ana"}


def test_name_search_looks_in_every_name_and_last_name(signed_in, people):
    assert listed(signed_in, "?by=name&q=oscar+zuniga", people) == {"oscar", "oscar2"}
    assert listed(signed_in, "?by=name&q=oscar+mora", people) == set()


def test_search_by_initials_and_signature(signed_in, people):
    assert listed(signed_in, "?by=initials&q=onz", people) == {"oscar", "oscar2"}
    assert listed(signed_in, "?by=initials&q=onz1", people) == {"oscar2"}
    assert listed(signed_in, "?by=signature&q=naranjoz", people) == {"oscar2"}


def test_search_wildcards_are_literal(signed_in, people):
    assert listed(signed_in, "?by=initials&q=%25", people) == set()
    html = signed_in.get("/collaborators/?by=signature&q=_").get_data(as_text=True)
    assert "Ningún colaborador coincide con la búsqueda." in html


def test_name_search_with_only_symbols_is_like_no_search(signed_in, people):
    assert listed(signed_in, "?by=name&q=%25", people) == {"oscar", "oscar2", "ana"}


def test_unknown_filters_fall_back_to_defaults(signed_in, people):
    assert listed(signed_in, "?by=cedula&status=raro&q=oscar", people) == {"oscar", "oscar2"}


def test_filters_are_kept_in_the_form(signed_in, people):
    html = signed_in.get("/collaborators/?by=initials&q=onz&status=all").get_data(as_text=True)
    assert 'value="onz"' in html
    assert re.search(r'value="initials"\s+selected', html)
    assert re.search(r'value="all"\s+checked', html)
    assert "Limpiar filtros" in html


def test_count_and_empty_message(signed_in, app):
    html = signed_in.get("/collaborators/").get_data(as_text=True)
    assert "0 colaboradores" in html
    assert "Todavía no hay colaboradores registrados." in html
    assert "Limpiar filtros" not in html


def test_pagination_keeps_the_filters(signed_in, app):
    for n in range(30):
        services.create_collaborator("Persona", "Prueba", date(1990, 1, 1), second_last_name=f"Apellido {chr(65 + n % 26)}")

    first = signed_in.get("/collaborators/?by=name&q=persona&status=all").get_data(as_text=True)
    second = signed_in.get("/collaborators/?by=name&q=persona&status=all&page=2").get_data(as_text=True)

    assert len(re.findall(r'href="/collaborators/\d+"', first)) == 25
    assert "30 colaboradores" in first
    assert 'aria-current="page">1<' in first
    assert re.search(r'href="/collaborators/\?[^"]*page=2[^"]*"', first)
    assert all(part in re.search(r'href="(/collaborators/\?[^"]*page=2[^"]*)"', first).group(1)
               for part in ("q=persona", "by=name", "status=all"))
    assert second.count("tabla-principal") == 5


def test_new_collaborator_button_only_for_admin_and_dcc(client, login_as):
    login_as("rrhh")
    assert 'href="/collaborators/create"' not in client.get("/collaborators/").get_data(as_text=True)


def test_new_collaborator_button_for_dcc(client, login_as):
    login_as("dcc")
    assert 'href="/collaborators/create"' in client.get("/collaborators/").get_data(as_text=True)
