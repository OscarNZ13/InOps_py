from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.models_base import DateTime2, TimestampMixin, TinyInt, now
from app.extensions import db

ROLE_ADMIN = 1
ROLE_RRHH = 2
DEFAULT_ROLE = ROLE_RRHH


class Role(db.Model):
    """Catalogo de roles (dbo.Roles). Los ids se asignan a mano: 1 admin, 2 rrhh, 3 dcc."""

    __tablename__ = "Roles"

    id_role = db.Column("id_role", TinyInt, primary_key=True, autoincrement=False)
    name = db.Column("name", db.String(20), nullable=False, unique=True)
    description = db.Column("Description", db.Unicode(100))
    is_active = db.Column("IsActive", db.Boolean, nullable=False, default=True)
    created_at = db.Column("CreatedAt", DateTime2, nullable=False, default=now)


class User(UserMixin, TimestampMixin, db.Model):
    """Usuario que inicia sesion en InOps (dbo.Users). No confundir con un colaborador."""

    __tablename__ = "Users"

    id_user = db.Column("id_user", db.Integer, primary_key=True)
    username = db.Column("username", db.Unicode(50), nullable=False, unique=True)
    password_hash = db.Column("password_hash", db.String(255), nullable=False)
    id_role = db.Column(
        "id_role", TinyInt, db.ForeignKey("Roles.id_role"), nullable=False, default=DEFAULT_ROLE
    )
    is_active = db.Column("IsActive", db.Boolean, nullable=False, default=True)

    role = db.relationship(Role)

    def get_id(self) -> str:
        return str(self.id_user)

    def set_password(self, password: str) -> None:
        """Guarda solo el hash de la contrasena, nunca el texto original."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles: str) -> bool:
        """True si el rol del usuario esta entre los indicados. Ej: user.has_role("admin", "dcc")."""
        return self.role.name in roles
