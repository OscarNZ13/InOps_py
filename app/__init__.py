import os

from flask import Flask, render_template
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import get_config
from app.core.modulos import modulos_para
from app.extensions import csrf, db, login_manager


def create_app(config_name: str | None = None) -> Flask:
    """Fábrica de la aplicación: carga la configuración, enlaza extensiones y registra módulos."""
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
    from app.modules.auth.routes import mostrar_acceso
    from app.modules.colaboradores import bp as colaboradores_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(colaboradores_bp, url_prefix="/colaboradores")

    @app.route("/")
    def index():
        """Sin sesión muestra el acceso (login/registro); con sesión, la página de inicio."""
        if not current_user.is_authenticated:
            return mostrar_acceso("login")
        return render_template("index.html", modulos=modulos_para(current_user))

    @app.errorhandler(403)
    def acceso_denegado(_error):
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template("errores/404.html"), 404

    return app


@event.listens_for(Engine, "connect")
def _activar_fk_sqlite(dbapi_connection, _record):
    """Activa las llaves foráneas en SQLite, que vienen desactivadas por defecto."""
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
