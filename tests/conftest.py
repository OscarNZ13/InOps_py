import pytest

from app import create_app
from app.extensions import db
from app.modules.auth.models import Role


@pytest.fixture
def app():
    app = create_app("testing")
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
