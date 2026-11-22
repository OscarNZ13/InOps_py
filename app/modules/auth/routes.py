"""Rutas (controladores) del modulo: reciben la peticion, usan forms y services, y responden."""
from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth import bp, services
from app.modules.auth.forms import LoginForm, RegisterForm


def render_access(active: str = "login", login_form=None, register_form=None):
    """Dibuja la tarjeta de acceso con las dos pestanas; `active` indica cual se abre."""
    return render_template(
        "auth/access.html",
        active=active,
        login_form=login_form or LoginForm(prefix="login"),
        register_form=register_form or RegisterForm(prefix="register"),
    )


def safe_next_url(target: str | None) -> str:
    """Solo permite redirigir a rutas internas, para que ?next= no mande a otro sitio."""
    if target and target.startswith("/") and not target.startswith("//") and not urlsplit(target).netloc:
        return target
    return url_for("index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm(prefix="login")
    if form.validate_on_submit():
        user = services.authenticate(form.username.data, form.password.data)
        if user is None:
            flash("Usuario o contraseña incorrectos.", "danger")
        elif not login_user(user):
            flash("Tu usuario está inactivo. Contacta a un administrador.", "warning")
        else:
            flash(f"Bienvenido, {user.username}.", "success")
            return redirect(safe_next_url(request.args.get("next")))

    return render_access("login", login_form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm(prefix="register")
    if form.validate_on_submit():
        user = services.create_user(form.username.data, form.password.data)
        login_user(user)
        flash("Cuenta creada correctamente.", "success")
        return redirect(url_for("index"))

    return render_access("register", register_form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión.", "success")
    return redirect(url_for("index"))
