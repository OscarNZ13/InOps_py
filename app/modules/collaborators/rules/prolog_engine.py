"""Motor en estilo logico: Python normaliza el texto y las reglas de rules.pl deciden."""
import threading
from pathlib import Path

from app.modules.collaborators.rules.engine import Exists, RulesEngine
from app.modules.collaborators.rules.text import words

RULES_FILE = Path(__file__).with_name("rules.pl")

# SWI-Prolog es uno solo para todo el proceso: el lock evita que dos peticiones mezclen su `exists`
_lock = threading.Lock()
_prolog = None
_exists: Exists | None = None
_error: Exception | None = None


def _used(value) -> bool:
    """Predicado foraneo used/1: Prolog lo llama para preguntarle a Python si un valor esta ocupado."""
    global _error
    try:
        return _exists is not None and _exists(str(value))
    except Exception as error:
        _error = error
        return False


def _load_prolog():
    global _prolog
    if _prolog is None:
        from pyswip import Prolog, registerForeign  # aqui y no arriba: sin SWI-Prolog el motor python sigue andando

        registerForeign(_used, name="used", arity=1)
        prolog = Prolog()
        prolog.consult(RULES_FILE.as_posix())
        _prolog = prolog
    return _prolog


def prolog_available() -> bool:
    try:
        _load_prolog()
    except Exception:
        return False
    return True


def _goal(predicate: str, *texts: str | None) -> str:
    """extra_letter('zuniga', '', 'naranjo', Result). Tras normalizar no hay comillas que escapar."""
    atoms = ", ".join("'" + " ".join(words(text)) + "'" for text in texts)
    return f"{predicate}({atoms}, Result)"


class PrologEngine(RulesEngine):
    def __init__(self):
        try:
            self.prolog = _load_prolog()
        except Exception as error:
            raise RuntimeError("El motor prolog necesita SWI-Prolog instalado (ver docs/INSTALACION.md).") from error

    def _solve(self, goal: str, exists: Exists | None = None) -> str | None:
        global _exists, _error
        with _lock:
            _exists, _error = exists, None
            try:
                solutions = list(self.prolog.query(goal, maxresult=1))
                if _error is not None:
                    raise _error
            finally:
                _exists = None
        return solutions[0]["Result"] if solutions else None

    def extra_letter(self, second_last_name: str | None, second_name: str | None, last_name: str) -> str:
        letter = self._solve(_goal("extra_letter", second_last_name, second_name, last_name))
        if letter is None:
            raise ValueError("El primer apellido debe tener al menos 2 letras.")
        return letter

    def generate_initials(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str:
        return self._solve(_goal("initials", first_name, last_name, extra.upper()), exists)

    def generate_signature(self, first_name: str, last_name: str, extra: str, exists: Exists) -> str:
        return self._solve(_goal("signature", first_name, last_name, extra.upper()), exists)
