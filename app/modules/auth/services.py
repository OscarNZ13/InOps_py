"""Logica de negocio de usuarios: las rutas la usan sin tocar la base de datos directamente."""
from sqlalchemy import func

from app.extensions import db
from app.modules.auth.models import DEFAULT_ROLE, User


def normalize_username(username: str) -> str:
    return (username or "").strip()


def find_by_username(username: str) -> User | None:
    """Busca sin distinguir mayusculas, igual que la collation de SQL Server."""
    username = normalize_username(username)
    return db.session.scalar(
        db.select(User).where(func.lower(User.username) == username.lower())
    )


def create_user(username: str, password: str, id_role: int = DEFAULT_ROLE) -> User:
    user = User(username=normalize_username(username), id_role=id_role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(username: str, password: str) -> User | None:
    """Devuelve el usuario si la contrasena es correcta; si no, None."""
    user = find_by_username(username)
    if user and user.check_password(password):
        return user
    return None
