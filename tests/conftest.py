import pytest
from flask import g

from app import create_app
from app.extensions import db
from app.modules.auth import services
from app.modules.auth.models import Role

ROLE_IDS = {"admin": 1, "rrhh": 2, "dcc": 3}


@pytest.fixture
def app():
    app = create_app("testing")

    @app.before_request
    def forget_cached_user():
        # Las pruebas comparten app context; sin esto Flask-Login reusaria en `g` el usuario de otro cliente
        g.pop("_login_user", None)

    with app.app_context():
        db.create_all()
        db.session.add_all(
            [
                Role(id_role=1, name="admin", description="Administrador del sistema"),
                Role(id_role=2, name="rrhh", description="Recursos Humanos"),
                Role(id_role=3, name="dcc", description="DCC"),
            ]
        )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login_as(client):
    """Crea un usuario con el rol indicado e inicia sesion con el. Uso: login_as("admin")."""

    def _login_as(role):
        user = services.create_user(f"usuario-{role}", "clave-segura")
        user.id_role = ROLE_IDS[role]
        db.session.commit()
        client.post("/login", data={"login-username": user.username, "login-password": "clave-segura"})
        return user

    return _login_as
