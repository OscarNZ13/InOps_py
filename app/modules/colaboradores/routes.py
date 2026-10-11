"""Rutas (controladores) del módulo de colaboradores."""
from flask import render_template

from app.core.permisos import rol_requerido
from app.modules.colaboradores import bp


@bp.route("/")
def lista():
    return render_template("colaboradores/lista.html")


@bp.route("/nuevo")
@rol_requerido("admin", "dcc")
def nuevo():
    return render_template("colaboradores/nuevo.html")
