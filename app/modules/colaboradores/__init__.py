"""Módulo de colaboradores: consulta y alta de las personas registradas en la empresa."""
from flask import Blueprint
from flask_login import login_required

bp = Blueprint("colaboradores", __name__)


@bp.before_request
@login_required
def requerir_sesion():
    """Todas las rutas de este módulo exigen haber iniciado sesión."""


from app.modules.colaboradores import routes  # noqa: E402,F401
