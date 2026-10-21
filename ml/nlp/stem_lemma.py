"""Morfología en CPU, con recursos cacheados por proceso y tokenización fija."""

from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from typing import Iterator

from nltk.stem.snowball import SnowballStemmer

from ml.nlp.stopwords import NEGATIONS

SPANISH_MODEL = "es_core_news_sm"
SPANISH_MODEL_VERSION = "3.8.0"


def is_protected(token: str, protect_negations: bool) -> bool:
    return token in {"urltoken", "numerotoken"} or token.startswith("emojitoken_") or (protect_negations and token in NEGATIONS)


@lru_cache(maxsize=1)
def spanish_stemmer() -> SnowballStemmer:
    return SnowballStemmer("spanish")


@lru_cache(maxsize=1)
def spanish_model():
    import spacy

    try:
        installed = version(SPANISH_MODEL)
    except PackageNotFoundError:
        raise RuntimeError("Instala el modelo español fijado mediante requirements.txt; no se descarga durante inferencia.") from None
    if installed != SPANISH_MODEL_VERSION:
        raise RuntimeError(f"Se requiere {SPANISH_MODEL}=={SPANISH_MODEL_VERSION}; instalado: {installed}.")
    spacy.require_cpu()
    return spacy.load(SPANISH_MODEL, exclude=["parser", "senter", "ner"])


def transform_token_batches(
    batches: list[list[str]], method: str, *, protect_negations: bool = True, batch_size: int = 128
) -> Iterator[list[str]]:
    if method == "stemming":
        stemmer = spanish_stemmer()
        for tokens in batches:
            yield [token if is_protected(token, protect_negations) else stemmer.stem(token) for token in tokens]
    elif method == "lemmatization":
        from spacy.tokens import Doc

        nlp = spanish_model()
        # Doc conserva exactamente los tokens del normalizador. Los auxiliares
        # permanecen como contexto del lematizador hasta filtrar stop words.
        docs = (Doc(nlp.vocab, words=tokens) for tokens in batches)
        for tokens, doc in zip(batches, nlp.pipe(docs, batch_size=batch_size, n_process=1)):
            yield [original if is_protected(original, protect_negations) else (token.lemma_.casefold() or original) for original, token in zip(tokens, doc)]
    else:
        raise ValueError("Morfología permitida: stemming o lemmatization.")
