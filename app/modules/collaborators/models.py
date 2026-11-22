from app.core.models_base import TimestampMixin
from app.extensions import db


class Collaborator(TimestampMixin, db.Model):
    """Persona registrada en la empresa (dbo.Collaborators). Nunca se borra: se desactiva."""

    __tablename__ = "Collaborators"

    id_collab = db.Column("id_collab", db.Integer, primary_key=True)
    first_name = db.Column("FirstName", db.Unicode(50), nullable=False)
    second_name = db.Column("SecondName", db.Unicode(50))
    last_name = db.Column("LastName", db.Unicode(50), nullable=False)
    second_last_name = db.Column("SecondLastName", db.Unicode(50))
    birthdate = db.Column("Birthdate", db.Date, nullable=False)
    is_active = db.Column("IsActive", db.Boolean, nullable=False, default=True)

    profile = db.relationship("CollaboratorProfile", back_populates="collaborator", uselist=False)

    @property
    def full_name(self) -> str:
        names = (self.first_name, self.second_name, self.last_name, self.second_last_name)
        return " ".join(name for name in names if name)


class CollaboratorProfile(TimestampMixin, db.Model):
    """Perfil 1 a 1 del colaborador (dbo.CollaboratorProfiles). Initials y Signature no cambian."""

    __tablename__ = "CollaboratorProfiles"
    __table_args__ = (
        # Correo unico solo cuando tiene valor, igual que ux_CollaboratorProfiles_Email en el SQL
        db.Index(
            "ux_CollaboratorProfiles_Email",
            "Email",
            unique=True,
            mssql_where=db.text("Email IS NOT NULL"),
            sqlite_where=db.text("Email IS NOT NULL"),
        ),
    )

    id_profile = db.Column("id_profile", db.Integer, primary_key=True)
    id_collab = db.Column(
        "id_collab", db.Integer, db.ForeignKey("Collaborators.id_collab"), nullable=False, unique=True
    )
    initials = db.Column("Initials", db.Unicode(20), nullable=False, unique=True)
    signature = db.Column("Signature", db.Unicode(60), nullable=False, unique=True)
    position = db.Column("Position", db.Unicode(100))
    department = db.Column("Department", db.Unicode(100))
    email = db.Column("Email", db.Unicode(100))
    phone = db.Column("Phone", db.Unicode(20))

    collaborator = db.relationship(Collaborator, back_populates="profile")
