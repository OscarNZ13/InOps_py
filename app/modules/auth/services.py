"""Logica de negocio de usuarios: las rutas la usan sin tocar la base de datos directamente."""
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.modules.auth.models import DEFAULT_ROLE, User


class UsernameTakenError(Exception):
    """Otra persona guardo ese nombre de usuario entre la validacion y el guardado."""


def normalize_username(username: str) -> str:
    return (username or "").strip()


def find_by_username(username: str) -> User | None:
    """Busca sin distinguir mayusculas, igual que la collation de SQL Server."""
    username = normalize_username(username)
    return db.session.scalar(
        db.select(User).where(func.lower(User.username) == username.lower())
    )


def commit_user(username: str) -> None:
    """Confirma los cambios. Si la base rechaza el nombre porque se lo ganaron, deshace y avisa."""
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if find_by_username(username):
            raise UsernameTakenError("Ese usuario ya existe.") from None
        raise


def create_user(username: str, password: str, id_role: int = DEFAULT_ROLE) -> User:
    user = User(username=normalize_username(username), id_role=id_role)
    user.set_password(password)
    db.session.add(user)
    commit_user(user.username)
    return user


def authenticate(username: str, password: str) -> User | None:
    """Devuelve el usuario si la contrasena es correcta; si no, None."""
    user = find_by_username(username)
    if user and user.check_password(password):
        return user
    return None
