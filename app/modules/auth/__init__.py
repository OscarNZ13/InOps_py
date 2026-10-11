"""Módulo de autenticación: inicio de sesión, registro y cierre de sesión de los usuarios del sistema."""
from flask import Blueprint

from app.extensions import db, login_manager
from app.modules.auth.models import Role, User  # noqa: F401

bp = Blueprint("auth", __name__)


@login_manager.user_loader
def cargar_usuario(user_id: str) -> User | None:
    """Recupera al usuario de la sesión en cada petición."""
    return db.session.get(User, int(user_id))


from app.modules.auth import routes  # noqa: E402,F401
