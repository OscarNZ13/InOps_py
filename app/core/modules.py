"""Catalogo de modulos que se muestran como tarjetas en la pagina de inicio.

Para activar un modulo, se le asigna el endpoint de su ruta principal (ej. "collaborators.list").
Mientras no tenga endpoint, la tarjeta aparece como "Proximamente".
Cada tarjeta solo la ven los roles indicados; deben coincidir con @role_required de su ruta.
"""
from dataclasses import dataclass

ALL_ROLES = ("admin", "dcc", "rrhh")


@dataclass(frozen=True)
class Module:
    title: str
    description: str
    icon: str
    roles: tuple[str, ...]
    endpoint: str | None = None


MODULES = (
    Module(
        title="Lista de colaboradores",
        description="Consulta a todos los colaboradores y búscalos por nombre, iniciales o firma.",
        icon="user",
        roles=ALL_ROLES,
        endpoint="collaborators.list",
    ),
    Module(
        title="Nuevo colaborador",
        description="Da de alta a una persona y genera sus Iniciales y Firma automáticamente.",
        icon="user-plus",
        roles=("admin", "dcc"),
        endpoint="collaborators.create",
    ),
    Module(
        title="Carga inicial",
        description="Importa los registros del Excel maestro respetando sus Iniciales y Firmas.",
        icon="import",
        roles=("admin", "dcc"),
    ),
    Module(
        title="Usuarios",
        description="Administra quién entra al sistema, su rol y su estado.",
        icon="shield",
        roles=("admin",),
        endpoint="users.list",
    ),
)


def modules_for(user) -> list[Module]:
    return [module for module in MODULES if user.has_role(*module.roles)]
