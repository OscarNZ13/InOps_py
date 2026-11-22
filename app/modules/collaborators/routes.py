"""Rutas (controladores) del modulo de colaboradores."""
from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for

from app.core.permissions import role_required
from app.modules.collaborators import bp, services
from app.modules.collaborators.forms import CreateCollaboratorForm, UpdateCollaboratorForm
from app.modules.collaborators.models import Collaborator


def get_collaborator_or_404(id_collab: int) -> Collaborator:
    collaborator = services.get_collaborator(id_collab)
    if collaborator is None:
        abort(404)
    return collaborator


@bp.route("/", endpoint="list")
def list_view():
    by = request.args.get("by", "name")
    status = request.args.get("status", "active")
    filters = {
        "q": request.args.get("q", "").strip(),
        "by": by if by in services.SEARCH_FIELDS else "name",
        "status": status if status in services.STATUSES else "active",
    }
    page = services.search_collaborators(
        filters["q"], filters["by"], filters["status"], request.args.get("page", 1, type=int)
    )
    return render_template(
        "collaborators/list.html",
        page=page,
        filters=filters,
        filtered=bool(filters["q"] or filters["status"] != "active"),
    )


@bp.route("/create", methods=["GET", "POST"])
@role_required("admin", "dcc")
def create():
    form = CreateCollaboratorForm()
    if form.validate_on_submit():
        try:
            collaborator = services.create_collaborator(**form.values())
        except services.EmailTakenError as error:
            form.email.errors.append(str(error))
        except services.CollaboratorCreateError as error:
            flash(str(error), "danger")
        else:
            # Vuelve al formulario vacio para seguir creando; el resumen sale en una notificacion lateral
            flash(
                {
                    "id": collaborator.id_collab,
                    "title": "Colaborador creado",
                    "name": collaborator.full_name,
                    "values": [("Iniciales", collaborator.profile.initials), ("Firma", collaborator.profile.signature)],
                    "url": url_for("collaborators.read", id_collab=collaborator.id_collab),
                },
                "toast",
            )
            return redirect(url_for("collaborators.create"))

    return render_template(
        "collaborators/create.html",
        form=form,
        today=date.today().isoformat(),
        recent=services.recent_collaborators(),
    )


@bp.route("/<int:id_collab>")
def read(id_collab: int):
    return render_template("collaborators/read.html", collaborator=get_collaborator_or_404(id_collab))


@bp.route("/<int:id_collab>/update", methods=["GET", "POST"])
@role_required("admin", "dcc")
def update(id_collab: int):
    collaborator = get_collaborator_or_404(id_collab)
    form = UpdateCollaboratorForm(collaborator)
    if form.validate_on_submit():
        try:
            services.update_collaborator(collaborator, **form.values())
        except services.EmailTakenError as error:
            form.email.errors.append(str(error))
        else:
            flash("Cambios guardados.", "success")
            return redirect(url_for("collaborators.read", id_collab=id_collab))

    return render_template(
        "collaborators/update.html", form=form, collaborator=collaborator, today=date.today().isoformat()
    )


@bp.route("/<int:id_collab>/activate", methods=["POST"])
def activate(id_collab: int):
    return change_status(id_collab, active=True)


@bp.route("/<int:id_collab>/deactivate", methods=["POST"])
def deactivate(id_collab: int):
    return change_status(id_collab, active=False)


def change_status(id_collab: int, active: bool):
    collaborator = services.set_active(get_collaborator_or_404(id_collab), active)
    flash(f"{collaborator.full_name} quedó {'activo' if active else 'inactivo'}.", "success")
    return redirect(url_for("collaborators.read", id_collab=id_collab))
