"""Los dos clasificadores autorizados y su pipeline NLP compartido."""

import json

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ml.config import ROOT
from ml.nlp.pipeline import build_pipeline, nlp_settings

MODEL_NAMES = ("MultinomialNB", "LogisticRegression")


def model_settings() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["models"]


def make_classifier(name: str, *, seed: int = 42, parameter: float = 1.0, max_iter: int = 500):
    if name == "MultinomialNB":
        return MultinomialNB(alpha=parameter)
    if name == "LogisticRegression":
        return LogisticRegression(C=parameter, solver="lbfgs", max_iter=max_iter, random_state=seed)
    raise ValueError("Solo se admiten MultinomialNB y LogisticRegression.")


def model_pipeline(name: str, morphology: str, ngram_range: tuple[int, int], *, seed: int, parameter: float = 1.0) -> Pipeline:
    nlp = nlp_settings()
    return build_pipeline(
        morphology=morphology, ngram_range=ngram_range,
        classifier=make_classifier(name, seed=seed, parameter=parameter, max_iter=model_settings()["logistic_max_iter"]),
        **nlp["preprocessing"], **nlp["tfidf"],
    )
