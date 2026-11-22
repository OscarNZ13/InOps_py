"""Rutas (controladores) del modulo de colaboradores."""
from flask import render_template

from app.core.permissions import role_required
from app.modules.collaborators import bp


@bp.route("/", endpoint="list")
def list_view():
    return render_template("collaborators/list.html")


@bp.route("/create")
@role_required("admin", "dcc")
def create():
    return render_template("collaborators/create.html")
