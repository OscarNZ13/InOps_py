"""Restricción de rutas por rol, equivalente a [Authorize(Roles = "...")] en .NET."""
from functools import wraps

from flask import abort
from flask_login import current_user

from app.extensions import login_manager


def rol_requerido(*roles: str):
    """Decorador de rutas: sin sesión redirige al login; con un rol no permitido responde 403.

    Uso:
        @bp.route("/nuevo")
        @rol_requerido("admin", "dcc")
        def nuevo(): ...
    """

    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.tiene_rol(*roles):
                abort(403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador
