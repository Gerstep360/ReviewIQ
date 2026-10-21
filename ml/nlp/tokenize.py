"""Contrato único: la normalización produce tokens separados por espacios."""


def split_tokens(text: str) -> list[str]:
    # Función importable también usada por TfidfVectorizer y Joblib.
    return text.split()
