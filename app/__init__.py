import os

from flask import Flask, render_template
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import get_config
from app.core.modules import modules_for
from app.extensions import csrf, db, login_manager


def create_app(config_name: str | None = None) -> Flask:
    """Fabrica de la aplicacion: carga la configuracion, enlaza extensiones y registra modulos."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Falta SECRET_KEY. Copia .env.example como .env y define una.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Falta DATABASE_URL en .env (ver .env.example).")

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.modules.auth import bp as auth_bp
    from app.modules.auth.routes import render_access
    from app.modules.collaborators import bp as collaborators_bp
    from app.modules.users import bp as users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(collaborators_bp, url_prefix="/collaborators")
    app.register_blueprint(users_bp, url_prefix="/users")

    @app.route("/")
    def index():
        """Sin sesion muestra el acceso (login/registro); con sesion, la pagina de inicio."""
        if not current_user.is_authenticated:
            return render_access("login")
        return render_template("index.html", modules=modules_for(current_user))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    return app


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    """Activa las llaves foraneas en SQLite, que vienen desactivadas por defecto."""
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
