import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración común a todos los entornos, leída desde .env."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    """Pruebas: usa TEST_DATABASE_URL o, si no existe, SQLite en memoria."""

    TESTING = True
    SECRET_KEY = "solo-para-pruebas"
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    """Devuelve la clase de configuración por nombre o según FLASK_ENV_NAME."""
    return CONFIGS[name or os.getenv("FLASK_ENV_NAME", "development")]
