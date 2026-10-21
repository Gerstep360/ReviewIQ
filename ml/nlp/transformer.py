"""Transformador clonable cuya traza ejecuta las mismas etapas que transform."""

import hashlib
from typing import Iterable

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted

from ml.nlp.normalize import normalize_text, strip_accents
from ml.nlp.stem_lemma import transform_token_batches
from ml.nlp.stopwords import STOPWORDS_VERSION, get_stopwords
from ml.nlp.tokenize import split_tokens

NLP_POLICY_VERSION = "reviewiq-nlp-1"


class ReviewTextPreprocessor(TransformerMixin, BaseEstimator):
    def __init__(
        self, morphology: str = "stemming", preserve_accents: bool = True,
        number_policy: str = "marker", emoji_policy: str = "marker",
        protect_negations: bool = True, extra_stopwords: tuple[str, ...] = (),
        batch_size: int = 128,
    ) -> None:
        self.morphology = morphology
        self.preserve_accents = preserve_accents
        self.number_policy = number_policy
        self.emoji_policy = emoji_policy
        self.protect_negations = protect_negations
        self.extra_stopwords = extra_stopwords
        self.batch_size = batch_size

    def fit(self, X: Iterable[str], y=None) -> "ReviewTextPreprocessor":
        if self.morphology not in {"stemming", "lemmatization"}:
            raise ValueError("Morfología no soportada.")
        if type(self.batch_size) is not int or self.batch_size < 1:
            raise ValueError("batch_size debe ser un entero positivo.")
        normalize_text("", preserve_accents=self.preserve_accents, number_policy=self.number_policy, emoji_policy=self.emoji_policy)
        words = get_stopwords(self.protect_negations, self.extra_stopwords)
        self.stopwords_ = words if self.preserve_accents else frozenset(strip_accents(word) for word in words)
        # Congelar la lista en el objeto serializado; cambiar una política exige fit.
        self.fitted_params_ = self.get_params(deep=False).copy()
        self.stopwords_sha256_ = hashlib.sha256("\n".join(sorted(self.stopwords_)).encode()).hexdigest()
        return self

    def _analyze(self, X: Iterable[str]) -> list[dict]:
        check_is_fitted(self, ["stopwords_", "fitted_params_"])
        if self.get_params(deep=False) != self.fitted_params_:
            raise ValueError("La configuración cambió después de fit; reconstruye y reentrena el pipeline.")
        if isinstance(X, str):
            raise TypeError("Se requiere una colección de reseñas, no un string individual.")
        originals = list(X)
        normalized = [normalize_text(text, preserve_accents=self.preserve_accents, number_policy=self.number_policy, emoji_policy=self.emoji_policy) for text in originals]
        batches = [split_tokens(text) for text in normalized]
        morphology = transform_token_batches(batches, self.morphology, protect_negations=self.protect_negations, batch_size=self.batch_size)
        traces = []
        for original, clean, tokens, morphed in zip(originals, normalized, batches, morphology):
            processed = [value for token, value in zip(tokens, morphed) if token not in self.stopwords_]
            # Un lema no puede introducir una segunda política de tokenización.
            processed = [value.replace(" ", "_") for value in processed if value]
            traces.append({
                "original": original, "normalized": clean, "tokens": tokens,
                "removed_stopwords": [token for token in tokens if token in self.stopwords_],
                "tokens_after_stopwords": [token for token in tokens if token not in self.stopwords_],
                "processed_tokens": processed, "processed_text": " ".join(processed),
                "method": self.morphology, "policy_version": NLP_POLICY_VERSION,
                "stopwords_version": STOPWORDS_VERSION, "stopwords_sha256": self.stopwords_sha256_,
            })
        return traces

    def transform(self, X: Iterable[str]) -> list[str]:
        return [trace["processed_text"] for trace in self._analyze(X)]

    def trace(self, text: str) -> dict:
        return self._analyze([text])[0]
