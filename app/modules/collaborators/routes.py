"""Rutas (controladores) del modulo de colaboradores."""
from datetime import date

from flask import abort, flash, redirect, render_template, url_for

from app.core.permissions import role_required
from app.modules.collaborators import bp, services
from app.modules.collaborators.forms import CreateCollaboratorForm

CREATE_FIELDS = (
    "first_name", "second_name", "last_name", "second_last_name", "birthdate",
    "position", "department", "email", "phone",
)


@bp.route("/", endpoint="list")
def list_view():
    return render_template("collaborators/list.html")


@bp.route("/create", methods=["GET", "POST"])
@role_required("admin", "dcc")
def create():
    form = CreateCollaboratorForm()
    if form.validate_on_submit():
        try:
            collaborator = services.create_collaborator(**{name: form[name].data for name in CREATE_FIELDS})
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
    collaborator = services.get_collaborator(id_collab)
    if collaborator is None:
        abort(404)
    return render_template("collaborators/read.html", collaborator=collaborator)
