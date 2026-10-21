"""Factorías para reutilizar las mismas etapas en experimentos y producción."""

import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator

from ml.config import ROOT
from ml.nlp.tokenize import split_tokens
from ml.nlp.transformer import ReviewTextPreprocessor


def nlp_settings() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["nlp"]


def build_vectorizer(ngram_range: tuple[int, int] = (1, 2), *, max_features: int = 50000, min_df: int = 2, max_df: float = 0.98) -> TfidfVectorizer:
    return TfidfVectorizer(
        tokenizer=split_tokens, token_pattern=None, preprocessor=None, lowercase=False,
        strip_accents=None, stop_words=None, ngram_range=ngram_range,
        max_features=max_features, min_df=min_df, max_df=max_df,
        sublinear_tf=True, dtype=np.float32,
    )


def build_pipeline(
    *, morphology: str = "stemming", ngram_range: tuple[int, int] = (1, 2),
    classifier: BaseEstimator | None = None, max_features: int = 50000,
    min_df: int = 2, max_df: float = 0.98, **preprocessing,
) -> Pipeline:
    steps = [
        ("nlp", ReviewTextPreprocessor(morphology=morphology, **preprocessing)),
        ("tfidf", build_vectorizer(ngram_range, max_features=max_features, min_df=min_df, max_df=max_df)),
    ]
    if classifier is not None:
        steps.append(("classifier", classifier))
    return Pipeline(steps)
