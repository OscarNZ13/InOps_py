"""Motor en estilo funcional: funciones puras, sin estado y sin acceso a la base de datos."""
from collections.abc import Iterable, Iterator
from itertools import chain, count

from app.modules.collaborators.rules.engine import Exists, RulesEngine
from app.modules.collaborators.rules.text import first_letter, without_spaces, words


def candidates(base: str) -> Iterator[str]:
    """base, base1, base2... Es infinito, pero solo se calcula hasta encontrar uno libre."""
    yield base
    yield from (f"{base}{n}" for n in count(1))


def first_available(options: Iterable[str], exists: Exists) -> str:
    return next(option for option in options if not exists(option))


class PythonEngine(RulesEngine):
    def extra_letter(self, second_last_name: str | None, second_name: str | None, last_name: str) -> str:
        source = next((name for name in (second_last_name, second_name) if words(name)), None)
        if source:
            return first_letter(source)

        letters = without_spaces(last_name)
        if len(letters) < 2:
            raise ValueError("El primer apellido debe tener al menos 2 letras.")
        return letters[1].upper()

    def generate_initials(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str:
        base = first_letter(first_name) + first_letter(last_name) + extra.upper()
        return first_available(candidates(base), exists)

    def generate_signature(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str:
        base = first_letter(first_name) + without_spaces(last_name).capitalize()
        return first_available(chain([base], candidates(base + extra.upper())), exists)
