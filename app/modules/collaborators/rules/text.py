"""Normalizacion de nombres. La comparten los motores antes de aplicar las reglas (seccion 5.4)."""
import unicodedata


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def words(text: str | None) -> list[str]:
    """Palabras sin acentos ni signos (O'Neil -> ONeil). None o solo espacios da una lista vacia."""
    letters = "".join(char for char in strip_accents(text or "") if char.isalpha() or char.isspace())
    return letters.split()


def first_letter(text: str) -> str:
    return words(text)[0][0].upper()


def without_spaces(text: str) -> str:
    return "".join(words(text))
