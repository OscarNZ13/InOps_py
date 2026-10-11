"""Catálogo de módulos que se muestran como tarjetas en la página de inicio.

Para activar un módulo, se le asigna el endpoint de su ruta principal (ej. "colaboradores.lista").
Mientras no tenga endpoint, la tarjeta aparece como "Próximamente".
Cada tarjeta solo la ven los roles indicados; deben coincidir con @rol_requerido de su ruta.
"""
from dataclasses import dataclass

TODOS_LOS_ROLES = ("admin", "dcc", "rrhh")


@dataclass(frozen=True)
class Modulo:
    titulo: str
    descripcion: str
    icono: str
    roles: tuple[str, ...]
    endpoint: str | None = None


MODULOS = (
    Modulo(
        titulo="Lista de colaboradores",
        descripcion="Consulta a todos los colaboradores y búscalos por nombre, iniciales o firma.",
        icono="usuarios",
        roles=TODOS_LOS_ROLES,
        endpoint="colaboradores.lista",
    ),
    Modulo(
        titulo="Nuevo colaborador",
        descripcion="Da de alta a una persona y genera sus Iniciales y Firma automáticamente.",
        icono="usuario-nuevo",
        roles=("admin", "dcc"),
        endpoint="colaboradores.nuevo",
    ),
    Modulo(
        titulo="Carga inicial",
        descripcion="Importa los registros del Excel maestro respetando sus Iniciales y Firmas.",
        icono="importar",
        roles=("admin", "dcc"),
    ),
    Modulo(
        titulo="Usuarios",
        descripcion="Administra quién entra al sistema, su rol y su estado.",
        icono="escudo",
        roles=("admin",),
    ),
)


def modulos_para(usuario) -> list[Modulo]:
    return [modulo for modulo in MODULOS if usuario.tiene_rol(*modulo.roles)]
