"""Logica de negocio del modulo: las rutas la usan sin tocar la base de datos directamente."""
from sqlalchemy import func

from app.extensions import db
from app.modules.auth import services as auth_services
from app.modules.auth.models import ROLE_ADMIN, Role, User

STATUSES = ("all", "active", "inactive")


class UserRuleError(Exception):
    """Una regla de negocio impide la operacion; el mensaje se muestra al usuario."""


def list_users(search: str = "", role: str = "", status: str = "all") -> list[User]:
    """Usuarios ordenados por nombre. Los filtros vacios no se aplican."""
    query = db.select(User).join(User.role).order_by(User.username)

    search = (search or "").strip().lower()
    if search:
        query = query.where(func.lower(User.username).contains(search, autoescape=True))
    if role:
        query = query.where(Role.name == role)
    if status == "active":
        query = query.where(User.is_active == True)  # noqa: E712
    elif status == "inactive":
        query = query.where(User.is_active == False)  # noqa: E712

    return list(db.session.scalars(query))


def list_roles() -> list[Role]:
    return list(
        db.session.scalars(db.select(Role).where(Role.is_active == True).order_by(Role.id_role))  # noqa: E712
    )


def get_user(id_user: int) -> User | None:
    return db.session.get(User, id_user)


def create_user(username: str, password: str, id_role: int) -> User:
    return auth_services.create_user(username, password, id_role)


def ensure_another_admin_remains(user: User) -> None:
    """Bloquea las filas de los admins activos hasta el commit (UPDLOCK en SQL Server).

    Asi, si dos admins se quitan el rol entre si al mismo tiempo, el segundo espera al primero
    y ya ve que no quedaria ningun admin.
    """
    admins = db.session.scalars(
        db.select(User.id_user)
        .where(User.id_role == ROLE_ADMIN, User.is_active == True)  # noqa: E712
        .order_by(User.id_user)
        .with_hint(User, "WITH (UPDLOCK)", "mssql")
    )
    if not set(admins) - {user.id_user}:
        raise UserRuleError("Debe quedar al menos un administrador activo.")


def update_user(user: User, actor: User, username: str, id_role: int, password: str | None = None) -> User:
    """`actor` es quien hace el cambio. La contrasena solo cambia si viene una nueva."""
    if user.id_user == actor.id_user and id_role != ROLE_ADMIN:
        raise UserRuleError("No puedes quitarte el rol de administrador.")
    if id_role != ROLE_ADMIN:
        ensure_another_admin_remains(user)

    user.username = auth_services.normalize_username(username)
    user.id_role = id_role
    if password:
        user.set_password(password)
    auth_services.commit_user(user.username)
    return user


def set_active(user: User, actor: User, active: bool) -> User:
    if not active and user.id_user == actor.id_user:
        raise UserRuleError("No puedes desactivar tu propio usuario.")
    if not active:
        ensure_another_admin_remains(user)

    user.is_active = active
    db.session.commit()
    return user
