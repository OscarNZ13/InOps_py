"""Restriccion de rutas por rol, equivalente a [Authorize(Roles = "...")] en .NET."""
from functools import wraps

from flask import abort
from flask_login import current_user

from app.extensions import login_manager


def role_required(*roles: str):
    """Decorador de rutas: sin sesion redirige al login; con un rol no permitido responde 403.

    Uso:
        @bp.route("/create")
        @role_required("admin", "dcc")
        def create(): ...
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.has_role(*roles):
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator
