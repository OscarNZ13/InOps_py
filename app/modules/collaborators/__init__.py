"""Modulo de colaboradores: consulta y alta de las personas registradas en la empresa."""
from flask import Blueprint
from flask_login import login_required

from app.modules.collaborators.models import Collaborator, CollaboratorProfile  # noqa: F401

bp = Blueprint("collaborators", __name__)


@bp.before_request
@login_required
def require_login():
    """Todas las rutas de este modulo exigen haber iniciado sesion."""


from app.modules.collaborators import routes  # noqa: E402,F401
