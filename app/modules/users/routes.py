"""Rutas (controladores) del modulo de usuarios. El acceso solo para admin lo da before_request."""
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.modules.auth.models import User
from app.modules.auth.services import UsernameTakenError
from app.modules.users import bp, services
from app.modules.users.forms import CreateUserForm, UpdateUserForm


def get_user_or_404(id_user: int) -> User:
    user = services.get_user(id_user)
    if user is None:
        abort(404)
    return user


@bp.route("/", endpoint="list")
def list_view():
    roles = services.list_roles()
    role = request.args.get("role", "")
    status = request.args.get("status", "all")
    filters = {
        "search": request.args.get("q", "").strip(),
        "role": role if role in {r.name for r in roles} else "",
        "status": status if status in services.STATUSES else "all",
    }
    return render_template(
        "users/list.html",
        users=services.list_users(**filters),
        roles=roles,
        filters=filters,
        filtered=bool(filters["search"] or filters["role"] or filters["status"] != "all"),
    )


@bp.route("/create", methods=["GET", "POST"])
def create():
    form = CreateUserForm()
    if form.validate_on_submit():
        try:
            user = services.create_user(form.username.data, form.password.data, form.id_role.data)
        except UsernameTakenError as error:
            form.username.errors.append(str(error))
        else:
            flash(f"Usuario {user.username} creado.", "success")
            return redirect(url_for("users.read", id_user=user.id_user))

    return render_template("users/create.html", form=form)


@bp.route("/<int:id_user>")
def read(id_user: int):
    return render_template("users/read.html", user=get_user_or_404(id_user))


@bp.route("/<int:id_user>/update", methods=["GET", "POST"])
def update(id_user: int):
    user = get_user_or_404(id_user)
    form = UpdateUserForm(user)
    if form.validate_on_submit():
        try:
            services.update_user(
                user,
                current_user,
                username=form.username.data,
                id_role=form.id_role.data,
                password=form.password.data,
            )
        except UsernameTakenError as error:
            form.username.errors.append(str(error))
        except services.UserRuleError as error:
            flash(str(error), "danger")
        else:
            flash("Cambios guardados.", "success")
            return redirect(url_for("users.read", id_user=user.id_user))

    return render_template("users/update.html", form=form, user=user)


@bp.route("/<int:id_user>/activate", methods=["POST"])
def activate(id_user: int):
    return change_status(id_user, active=True)


@bp.route("/<int:id_user>/deactivate", methods=["POST"])
def deactivate(id_user: int):
    return change_status(id_user, active=False)


def change_status(id_user: int, active: bool):
    user = get_user_or_404(id_user)
    try:
        services.set_active(user, current_user, active)
    except services.UserRuleError as error:
        flash(str(error), "danger")
    else:
        flash(f"Usuario {user.username} {'activado' if active else 'desactivado'}.", "success")
    return redirect(url_for("users.read", id_user=user.id_user))
