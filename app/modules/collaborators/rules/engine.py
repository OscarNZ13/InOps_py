from abc import ABC, abstractmethod
from collections.abc import Callable

# Responde si un valor ya esta ocupado: un set en las pruebas, una consulta a la base en la app
Exists = Callable[[str], bool]


class RulesEngine(ABC):
    """Interfaz comun de los motores que generan Iniciales y Firma (seccion 5 del contexto)."""

    @abstractmethod
    def extra_letter(self, second_last_name: str | None, second_name: str | None, last_name: str) -> str: ...

    @abstractmethod
    def generate_initials(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str: ...

    @abstractmethod
    def generate_signature(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str: ...
