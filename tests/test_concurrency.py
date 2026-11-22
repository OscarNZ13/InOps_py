import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.modules.auth import services
from app.modules.auth.models import User
from app.modules.users import services as users_services

ROLE_ADMIN, ROLE_RRHH = 1, 2


@pytest.fixture
def username_race(monkeypatch):
    """Al llamarla, la siguiente validacion ve el nombre libre, como si otra persona lo guardara justo despues."""

    def start():
        real = services.find_by_username
        calls = []

        def free_on_first_call(username):
            calls.append(username)
            return None if len(calls) == 1 else real(username)

        monkeypatch.setattr(services, "find_by_username", free_on_first_call)

    return start


def test_register_race_shows_the_error_in_the_form(client, username_race):
    services.create_user("ana", "clave-segura")
    username_race()
    response = client.post(
        "/register",
        data={"register-username": "ana", "register-password": "clave-segura", "register-confirm_password": "clave-segura"},
    )

    assert response.status_code == 200
    assert "Ese usuario ya existe." in response.get_data(as_text=True)
    assert db.session.query(User).count() == 1


def test_admin_create_race_shows_the_error_in_the_form(client, login_as, username_race):
    login_as("admin")
    services.create_user("luis", "clave-segura")
    username_race()
    response = client.post(
        "/users/create",
        data={"username": "luis", "password": "clave-segura", "confirm_password": "clave-segura", "id_role": ROLE_RRHH},
    )

    assert response.status_code == 200
    assert "Ese usuario ya existe." in response.get_data(as_text=True)
    assert db.session.query(User).count() == 2


def test_rename_race_shows_the_error_and_keeps_the_old_name(client, login_as, username_race):
    login_as("admin")
    ana = services.create_user("ana", "clave-segura")
    services.create_user("luis", "clave-segura")
    username_race()
    response = client.post(
        f"/users/{ana.id_user}/update",
        data={"username": "luis", "id_role": ROLE_RRHH, "password": "", "confirm_password": ""},
    )

    assert response.status_code == 200
    assert "Ese usuario ya existe." in response.get_data(as_text=True)
    assert db.session.get(User, ana.id_user).username == "ana"


def test_other_integrity_errors_are_not_hidden(app):
    with pytest.raises(IntegrityError):
        services.create_user("ana", "clave-segura", id_role=99)


def test_two_admins_cannot_leave_the_system_without_admins(app):
    """Simula que B ya paso el control de permisos cuando A le quito el rol."""
    admin_a = services.create_user("admin-a", "clave-segura", ROLE_ADMIN)
    admin_b = services.create_user("admin-b", "clave-segura", ROLE_ADMIN)

    users_services.update_user(admin_b, admin_a, username="admin-b", id_role=ROLE_RRHH)

    with pytest.raises(users_services.UserRuleError, match="al menos un administrador"):
        users_services.update_user(admin_a, admin_b, username="admin-a", id_role=ROLE_RRHH)
    with pytest.raises(users_services.UserRuleError, match="al menos un administrador"):
        users_services.set_active(admin_a, admin_b, active=False)
    db.session.rollback()
    assert db.session.get(User, admin_a.id_user).role.name == "admin"


def test_an_admin_can_still_remove_another_admin(app):
    admin_a = services.create_user("admin-a", "clave-segura", ROLE_ADMIN)
    admin_b = services.create_user("admin-b", "clave-segura", ROLE_ADMIN)

    users_services.set_active(admin_b, admin_a, active=False)

    assert not db.session.get(User, admin_b.id_user).is_active
