"""Eventos del ORM del modulo de colaboradores."""
from sqlalchemy import event, inspect

from app.modules.collaborators.models import CollaboratorProfile


class ImmutableProfileError(Exception):
    """Alguien intento cambiar las Iniciales o la Firma de un perfil ya guardado (seccion 5.6)."""


@event.listens_for(CollaboratorProfile, "before_update")
def prevent_identifier_changes(_mapper, _connection, profile):
    state = inspect(profile)
    for field in ("initials", "signature"):
        if state.attrs[field].history.has_changes():
            raise ImmutableProfileError(f"No se puede modificar '{field}' de un perfil existente.")
