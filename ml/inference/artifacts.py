"""Identidad del estado aprendido, independiente de los bytes de Joblib."""

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import numpy as np

from ml.config import ROOT

RUNTIME_DISTRIBUTIONS = ("scikit-learn", "numpy", "scipy", "joblib", "nltk", "spacy", "es-core-news-sm", "emoji")
NLP_SOURCES = ("normalize.py", "tokenize.py", "stopwords.py", "stem_lemma.py", "transformer.py", "pipeline.py")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def runtime_versions() -> dict:
    return {"python_major_minor": ".".join(platform.python_version_tuple()[:2]), **{name: version(name) for name in RUNTIME_DISTRIBUTIONS}}


def inference_sources() -> dict:
    # Git puede convertir LF/CRLF al clonar: la identidad del código se normaliza.
    return {name: hashlib.sha256((ROOT / "ml" / "nlp" / name).read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest() for name in NLP_SOURCES}


def model_state_hash(pipeline) -> str:
    """Incluye vocabulario, IDF, pesos, clases, parámetros y stop words ajustadas."""
    preprocessor, vectorizer, classifier = (pipeline.named_steps[name] for name in ("nlp", "tfidf", "classifier"))
    digest = hashlib.sha256()
    metadata = {
        "preprocessing": preprocessor.get_params(deep=False),
        "stopwords": sorted(preprocessor.stopwords_),
        "vocabulary": sorted((word, int(index)) for word, index in vectorizer.vocabulary_.items()),
        "tfidf": {name: getattr(vectorizer, name) for name in ("ngram_range", "min_df", "max_df", "max_features", "sublinear_tf", "norm", "use_idf", "smooth_idf")},
        "classifier": type(classifier).__name__, "classifier_params": classifier.get_params(deep=False),
    }
    digest.update(canonical_hash(metadata).encode("ascii"))
    arrays = {"idf_": vectorizer.idf_, "classes_": classifier.classes_}
    for name in ("coef_", "intercept_", "class_count_", "feature_count_", "class_log_prior_", "feature_log_prob_"):
        if hasattr(classifier, name):
            arrays[name] = getattr(classifier, name)
    for name, values in sorted(arrays.items()):
        array = np.asarray(values)
        array = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
        digest.update(canonical_hash({"name": name, "shape": array.shape, "dtype": array.dtype.str}).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def verify_runtime(expected: dict) -> None:
    if runtime_versions() != expected:
        raise ValueError("Versiones incompatibles con el paquete; instala las dependencias fijadas.")
