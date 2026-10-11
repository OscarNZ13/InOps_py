"""Lógica de negocio de usuarios: las rutas la usan sin tocar la base de datos directamente."""
from sqlalchemy import func

from app.extensions import db
from app.modules.auth.models import User


def normalizar_username(username: str) -> str:
    return (username or "").strip()


def buscar_por_username(username: str) -> User | None:
    """Busca sin distinguir mayúsculas, igual que la collation de SQL Server."""
    username = normalizar_username(username)
    return db.session.scalar(
        db.select(User).where(func.lower(User.username) == username.lower())
    )


def crear_usuario(username: str, password: str) -> User:
    usuario = User(username=normalizar_username(username))
    usuario.set_password(password)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def autenticar(username: str, password: str) -> User | None:
    """Devuelve el usuario si la contraseña es correcta; si no, None."""
    usuario = buscar_por_username(username)
    if usuario and usuario.check_password(password):
        return usuario
    return None
