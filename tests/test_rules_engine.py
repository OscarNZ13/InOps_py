from itertools import islice

import pytest

from app.modules.collaborators.rules import get_engine
from app.modules.collaborators.rules.engine import RulesEngine
from app.modules.collaborators.rules.python_engine import PythonEngine, candidates, first_available
from app.modules.collaborators.rules.text import first_letter, strip_accents, without_spaces


# Cuando exista el motor Prolog se agrega aqui y todas las pruebas corren contra los dos
@pytest.fixture(params=[PythonEngine], ids=["python"])
def engine(request):
    return request.param()


def occupied(*values):
    return lambda value: value in values


# Tabla de la seccion 5.5: cada valor es el esperado cuando los anteriores ya estan ocupados
CASES = [
    (("Oscar", "Josue", "Naranjo", "Zuniga"), "Z",
     ["ONZ", "ONZ1", "ONZ2"], ["ONaranjo", "ONaranjoZ", "ONaranjoZ1", "ONaranjoZ2"]),
    (("Oscar", None, "Naranjo", "Zuniga"), "Z",
     ["ONZ", "ONZ1", "ONZ2"], ["ONaranjo", "ONaranjoZ", "ONaranjoZ1", "ONaranjoZ2"]),
    (("Oscar", "Josue", "Naranjo", None), "J",
     ["ONJ", "ONJ1", "ONJ2"], ["ONaranjo", "ONaranjoJ", "ONaranjoJ1", "ONaranjoJ2"]),
    (("Oscar", None, "Naranjo", None), "A",
     ["ONA", "ONA1", "ONA2"], ["ONaranjo", "ONaranjoA", "ONaranjoA1", "ONaranjoA2"]),
    (("Oscar", None, "De la O", "Lopez"), "L",
     ["ODL", "ODL1", "ODL2"], ["ODelao", "ODelaoL", "ODelaoL1", "ODelaoL2"]),
    (("Ángel", None, "Muñoz", None), "U", ["AMU"], ["AMunoz"]),
]


@pytest.mark.parametrize("names, extra, initials, signatures", CASES, ids=lambda value: str(value))
def test_section_5_5_cases(engine, names, extra, initials, signatures):
    first_name, second_name, last_name, second_last_name = names

    assert engine.extra_letter(second_last_name, second_name, last_name) == extra
    for i, expected in enumerate(initials):
        assert engine.generate_initials(first_name, last_name, extra, occupied(*initials[:i])) == expected
    for i, expected in enumerate(signatures):
        assert engine.generate_signature(first_name, last_name, extra, occupied(*signatures[:i])) == expected


def test_one_letter_last_name_is_rejected(engine):
    with pytest.raises(ValueError, match="al menos 2 letras"):
        engine.extra_letter(None, None, "O")


def test_blank_optional_names_count_as_missing(engine):
    assert engine.extra_letter("   ", "", "Naranjo") == "A"


def test_case_and_accents_in_the_input_do_not_matter(engine):
    none_taken = occupied()
    assert engine.extra_letter(None, None, "naRANjo") == "A"
    assert engine.generate_initials("óscar", "naRANjo", "a", none_taken) == "ONA"
    assert engine.generate_signature("óscar", "naRANjo", "a", none_taken) == "ONaranjo"


def test_multiword_names_count_as_one(engine):
    assert engine.extra_letter("De la Cruz", None, "Naranjo") == "D"
    assert engine.generate_initials("Maria Jose", "Naranjo", "D", occupied()) == "MND"


@pytest.mark.parametrize(
    "last_name, second_last_name, extra, initials, signature",
    [
        ("O'Neil", None, "N", "OON", "OOneil"),
        ("Pérez-Soto", None, "E", "OPE", "OPerezsoto"),
        ("D'Angelo", "Ruiz", "R", "ODR", "ODangelo"),
    ],
)
def test_apostrophes_and_hyphens_are_removed(engine, last_name, second_last_name, extra, initials, signature):
    assert engine.extra_letter(second_last_name, None, last_name) == extra
    assert engine.generate_initials("Oscar", last_name, extra, occupied()) == initials
    assert engine.generate_signature("Oscar", last_name, extra, occupied()) == signature


def test_uses_the_first_free_value(engine):
    assert engine.generate_initials("Oscar", "Naranjo", "Z", occupied("ONZ1")) == "ONZ"
    assert engine.generate_initials("Oscar", "Naranjo", "Z", occupied("ONZ", "ONZ2")) == "ONZ1"


def test_candidates_are_infinite_but_lazy():
    assert list(islice(candidates("ONZ"), 4)) == ["ONZ", "ONZ1", "ONZ2", "ONZ3"]


def test_first_available_stops_at_the_first_free():
    asked = []

    def exists(value):
        asked.append(value)
        return value in {"ONZ", "ONZ1"}

    assert first_available(candidates("ONZ"), exists) == "ONZ2"
    assert asked == ["ONZ", "ONZ1", "ONZ2"]


def test_text_normalization():
    assert strip_accents("Ángel Muñoz Güell") == "Angel Munoz Guell"
    assert without_spaces("  De la   O ") == "DelaO"
    assert without_spaces("O'Neil-Smith") == "ONeilSmith"
    assert first_letter("  ángel ") == "A"


def test_rules_engine_is_abstract():
    with pytest.raises(TypeError):
        RulesEngine()


def test_get_engine_uses_the_configured_engine(app):
    assert isinstance(get_engine(), PythonEngine)
    with pytest.raises(ValueError, match="desconocido"):
        get_engine("cobol")
