"""Modulo de usuarios: el admin consulta quien entra al sistema, con que rol y en que estado."""
from flask import Blueprint

from app.core.permissions import role_required

bp = Blueprint("users", __name__)


@bp.before_request
@role_required("admin")
def require_admin():
    """Todas las rutas de este modulo son solo para admin."""


from app.modules.users import routes  # noqa: E402,F401
