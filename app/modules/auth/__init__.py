"""Modulo de autenticacion: inicio de sesion, registro y cierre de sesion de los usuarios del sistema."""
from flask import Blueprint

from app.extensions import db, login_manager
from app.modules.auth.models import Role, User  # noqa: F401

bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Recupera al usuario de la sesion en cada peticion. Si esta inactivo, lo saca de la sesion."""
    user = db.session.get(User, int(user_id))
    return user if user and user.is_active else None


from app.modules.auth import routes  # noqa: E402,F401
