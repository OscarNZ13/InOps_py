"""Logica de negocio de colaboradores: las rutas la usan sin tocar la base de datos directamente."""
from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.modules.collaborators.models import Collaborator, CollaboratorProfile
from app.modules.collaborators.rules import get_engine
from app.modules.collaborators.rules.text import strip_accents, words

MAX_ATTEMPTS = 3


class EmailTakenError(Exception):
    """Otra persona guardo ese correo entre la validacion y el guardado."""


class CollaboratorCreateError(Exception):
    """No se consiguieron Iniciales y Firma libres despues de varios intentos."""


def clean_name(text: str | None) -> str | None:
    """Sin acentos ni signos y con mayuscula inicial (seccion 4). Vacio o solo espacios -> None.

    dE lA o -> De La O, Zúñiga -> Zuniga, Pérez-Soto -> Perez Soto, O'Neil -> Oneil.
    """
    return " ".join(words((text or "").replace("-", " "))).title() or None


def clean(text: str | None) -> str | None:
    return (text or "").strip() or None


def clean_plain(text: str | None) -> str | None:
    """Puesto o departamento: sin acentos y sin espacios de mas."""
    return " ".join(strip_accents(text or "").split()) or None


def _taken(condition) -> bool:
    """Compara contra todos los perfiles: activos, inactivos y migrados (seccion 6)."""
    return db.session.scalar(db.select(CollaboratorProfile.id_profile).where(condition)) is not None


def initials_taken(value: str) -> bool:
    return _taken(CollaboratorProfile.initials == value)


def signature_taken(value: str) -> bool:
    return _taken(CollaboratorProfile.signature == value)


def email_taken(email: str) -> bool:
    return _taken(func.lower(CollaboratorProfile.email) == email.lower())


def get_collaborator(id_collab: int) -> Collaborator | None:
    return db.session.get(Collaborator, id_collab)


def recent_collaborators(limit: int = 8) -> list[Collaborator]:
    query = (
        db.select(Collaborator)
        .options(db.joinedload(Collaborator.profile))
        .order_by(Collaborator.created_at.desc(), Collaborator.id_collab.desc())
        .limit(limit)
    )
    return list(db.session.scalars(query))


def create_collaborator(
    first_name: str,
    last_name: str,
    birthdate: date,
    second_name: str | None = None,
    second_last_name: str | None = None,
    position: str | None = None,
    department: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> Collaborator:
    """Guarda colaborador y perfil en una sola transaccion (seccion 6).

    Si otra persona se gana las mismas Iniciales o Firma justo antes de guardar, se generan de nuevo
    (seccion 7.1).
    """
    names = {
        "first_name": clean_name(first_name),
        "second_name": clean_name(second_name),
        "last_name": clean_name(last_name),
        "second_last_name": clean_name(second_last_name),
    }
    email = (clean(email) or "").lower() or None
    engine = get_engine()
    extra = engine.extra_letter(names["second_last_name"], names["second_name"], names["last_name"])

    for _ in range(MAX_ATTEMPTS):
        profile = CollaboratorProfile(
            initials=engine.generate_initials(names["first_name"], names["last_name"], extra, initials_taken),
            signature=engine.generate_signature(names["first_name"], names["last_name"], extra, signature_taken),
            position=clean_plain(position),
            department=clean_plain(department),
            email=email,
            phone=clean(phone),
        )
        collaborator = Collaborator(birthdate=birthdate, profile=profile, **names)
        db.session.add(collaborator)
        try:
            db.session.commit()
            return collaborator
        except IntegrityError:
            db.session.rollback()
            if email and email_taken(email):
                raise EmailTakenError("Ese correo ya pertenece a otro colaborador.") from None

    raise CollaboratorCreateError("No se pudieron generar Iniciales y Firma libres. Intenta de nuevo.")
