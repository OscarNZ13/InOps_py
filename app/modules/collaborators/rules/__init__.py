"""Motores de reglas para generar Iniciales y Firma. Se elige con RULES_ENGINE en el .env."""
from flask import current_app

from app.modules.collaborators.rules.engine import RulesEngine
from app.modules.collaborators.rules.prolog_engine import PrologEngine
from app.modules.collaborators.rules.python_engine import PythonEngine

ENGINES: dict[str, type[RulesEngine]] = {"python": PythonEngine, "prolog": PrologEngine}


def get_engine(name: str | None = None) -> RulesEngine:
    name = name or current_app.config["RULES_ENGINE"]
    if name not in ENGINES:
        raise ValueError(f"Motor de reglas desconocido: {name!r}. Opciones: {', '.join(ENGINES)}.")
    return ENGINES[name]()
