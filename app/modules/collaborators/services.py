"""Logica de negocio de colaboradores: las rutas la usan sin tocar la base de datos directamente."""
from datetime import date

from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager

from app.extensions import db
from app.modules.collaborators.models import Collaborator, CollaboratorProfile
from app.modules.collaborators.rules import get_engine
from app.modules.collaborators.rules.text import strip_accents, words

MAX_ATTEMPTS = 3
PER_PAGE = 25
SEARCH_FIELDS = ("name", "initials", "signature")
STATUSES = ("active", "inactive", "all")
NAME_COLUMNS = (
    Collaborator.first_name, Collaborator.second_name, Collaborator.last_name, Collaborator.second_last_name
)


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


def _contains(column, text: str):
    return func.lower(column).contains(text.lower(), autoescape=True)


def search_collaborators(text: str = "", by: str = "name", status: str = "active", page: int = 1) -> Pagination:
    """Lista paginada (seccion 8.1). Busqueda parcial sin distinguir mayusculas ni acentos.

    Por nombre, cada palabra debe aparecer en algun nombre o apellido: "oscar zuniga" encuentra a
    Oscar Naranjo Zuniga.
    """
    query = (
        db.select(Collaborator)
        .join(Collaborator.profile)
        .options(contains_eager(Collaborator.profile))
        .order_by(
            Collaborator.last_name, Collaborator.second_last_name, Collaborator.first_name, Collaborator.id_collab
        )
    )

    if by == "name":
        for word in words(text):
            query = query.where(or_(*(_contains(column, word) for column in NAME_COLUMNS)))
    else:
        value = "".join(strip_accents(text).split())
        if value:
            column = CollaboratorProfile.initials if by == "initials" else CollaboratorProfile.signature
            query = query.where(_contains(column, value))

    if status == "active":
        query = query.where(Collaborator.is_active == True)  # noqa: E712
    elif status == "inactive":
        query = query.where(Collaborator.is_active == False)  # noqa: E712

    return db.paginate(query, page=page, per_page=PER_PAGE, error_out=False)


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
