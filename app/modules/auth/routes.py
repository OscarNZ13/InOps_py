"""Rutas (controladores) del módulo: reciben la petición, usan forms y services, y responden."""
from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth import bp, services
from app.modules.auth.forms import LoginForm, RegistroForm


def mostrar_acceso(activo: str = "login", login_form=None, registro_form=None):
    """Dibuja la tarjeta de acceso con las dos pestañas; `activo` indica cuál se abre."""
    return render_template(
        "auth/acceso.html",
        activo=activo,
        login_form=login_form or LoginForm(prefix="login"),
        registro_form=registro_form or RegistroForm(prefix="register"),
    )


def destino_seguro(destino: str | None) -> str:
    """Solo permite redirigir a rutas internas, para que ?next= no mande a otro sitio."""
    if destino and destino.startswith("/") and not destino.startswith("//") and not urlsplit(destino).netloc:
        return destino
    return url_for("index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm(prefix="login")
    if form.validate_on_submit():
        usuario = services.autenticar(form.username.data, form.password.data)
        if usuario is None:
            flash("Usuario o contraseña incorrectos.", "danger")
        elif not login_user(usuario):
            flash("Tu usuario está inactivo. Contacta a un administrador.", "warning")
        else:
            flash(f"Bienvenido, {usuario.username}.", "success")
            return redirect(destino_seguro(request.args.get("next")))

    return mostrar_acceso("login", login_form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistroForm(prefix="register")
    if form.validate_on_submit():
        usuario = services.crear_usuario(form.username.data, form.password.data)
        login_user(usuario)
        flash("Cuenta creada correctamente.", "success")
        return redirect(url_for("index"))

    return mostrar_acceso("register", registro_form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión.", "success")
    return redirect(url_for("index"))
