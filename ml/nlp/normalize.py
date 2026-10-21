"""Políticas explícitas de normalización; ninguna URL se visita."""

import re
import unicodedata

import emoji

URL = re.compile(r"(?:https?://|www\.)[^\s<>]+", re.IGNORECASE)
NUMBER_OR_MARKER = re.compile(r"emojitoken_\w+|\d+(?:[.,]\d+)*", re.UNICODE)
NON_TOKEN = re.compile(r"[^\w\s]", re.UNICODE)


def _emoji_marker(chars: str, data: dict) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", emoji.demojize(chars, language="en").casefold()).strip("_")
    return f" emojitoken_{name} "


def strip_accents(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))


def normalize_text(
    text: str,
    *,
    preserve_accents: bool = True,
    number_policy: str = "marker",
    emoji_policy: str = "marker",
) -> str:
    if not isinstance(text, str):
        raise TypeError("La reseña debe ser texto.")
    if number_policy not in {"marker", "keep"} or emoji_policy not in {"marker", "remove"}:
        raise ValueError("Política de números o emojis inválida.")
    text = unicodedata.normalize("NFKC", text).casefold()
    text = URL.sub(" urltoken ", text)
    # Separar emojis completos antes de números/signos (incluye secuencias ZWJ).
    text = emoji.replace_emoji(text, replace=_emoji_marker if emoji_policy == "marker" else " ")
    if number_policy == "marker":
        # No alterar dígitos que formen parte de nombres de marcadores de emoji.
        text = NUMBER_OR_MARKER.sub(lambda match: match[0] if match[0].startswith("emojitoken_") else " numerotoken ", text)
    if not preserve_accents:
        text = strip_accents(text)
    text = NON_TOKEN.sub(" ", text)
    return " ".join(text.split())
