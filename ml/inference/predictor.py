"""Carga local verificada una vez; nunca descarga datos, ajusta NLP ni entrena."""

from functools import lru_cache
from pathlib import Path
from threading import Lock

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from ml.config import ROOT
from ml.data.download import sha256_file
from ml.evaluation.evaluate import labels_to_stars, validate_probabilities
from ml.inference.artifacts import inference_sources, model_state_hash, read_json, verify_runtime
from ml.nlp.trace import trace_pipeline

DEFAULT_PACKAGE = ROOT / "ml" / "artifacts" / "full"


def verify_package(directory: Path) -> tuple[dict, dict]:
    manifest = read_json(directory / "manifest.json")
    if manifest.get("schema_version") != "1.0" or manifest.get("artifact_file") != "pipeline.joblib" or manifest.get("metric_file") != "metrics.json":
        raise ValueError("Esquema o nombres de archivo no permitidos en el paquete.")
    expected_split = {"quick": "validation", "full": "test"}.get(manifest.get("mode"))
    if expected_split is None or manifest["metric_split"] != expected_split:
        raise ValueError("El split de métricas no corresponde al modo del paquete.")
    if manifest["label_index_to_stars"] != {str(label): label + 1 for label in range(5)}:
        raise ValueError("Mapa de estrellas inválido.")
    if manifest["mode"] == "full" and not manifest["historical_test"]["model_state_matches_evaluated"]:
        raise ValueError("El paquete full no reproduce el estado evaluado.")
    for filename, field in (("pipeline.joblib", "artifact_sha256"), ("metrics.json", "metric_sha256")):
        if sha256_file(directory / filename) != manifest[field]:
            raise ValueError(f"Integridad inválida: {filename}.")
    metrics = read_json(directory / "metrics.json")
    if metrics["model_id"] != manifest["model_id"] or metrics["split"] != manifest["metric_split"]:
        raise ValueError("Métricas y manifiesto corresponden a modelos o splits distintos.")
    if manifest["nlp_source_sha256"] != inference_sources():
        raise ValueError("El código NLP cambió; reconstruye un paquete compatible.")
    verify_runtime(manifest["runtime"])
    return manifest, metrics


class Predictor:
    def __init__(self, package_dir: Path = DEFAULT_PACKAGE):
        self.package_dir = Path(package_dir).resolve()
        self.manifest, self.metrics = verify_package(self.package_dir)
        # Solo deserializar después de verificar el paquete local controlado.
        self.pipeline = joblib.load(self.package_dir / "pipeline.joblib")
        if model_state_hash(self.pipeline) != self.manifest["model_state_sha256"]:
            raise ValueError("El estado aprendido no corresponde al manifiesto.")
        if not np.array_equal(self.pipeline.classes_, np.arange(5)):
            raise ValueError("Se requieren las cinco clases en orden 0–4.")
        self._lock = Lock()

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if isinstance(texts, str) or not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Se requiere una lista no vacía de reseñas no vacías.")
        with self._lock, threadpool_limits(limits=1):
            return validate_probabilities(self.pipeline.predict_proba(texts), self.pipeline.classes_)

    def predict(self, texts: list[str]) -> list[dict]:
        probabilities = self.predict_proba(texts)
        labels = self.pipeline.classes_[np.argmax(probabilities, axis=1)]
        stars = labels_to_stars(labels)
        return [{
            "model_id": self.manifest["model_id"], "stars": int(rating),
            "probabilities": {str(index + 1): float(value) for index, value in enumerate(row)},
            "experimental": self.manifest["mode"] == "quick",
        } for rating, row in zip(stars, probabilities)]

    def trace(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("La reseña debe ser texto no vacío.")
        with self._lock, threadpool_limits(limits=1):
            return {"model_id": self.manifest["model_id"], **trace_pipeline(self.pipeline, text)}


@lru_cache(maxsize=2)
def get_predictor(package_dir: str = str(DEFAULT_PACKAGE)) -> Predictor:
    """Un objeto por ruta y proceso. Una futura API debe reutilizarlo."""
    return Predictor(Path(package_dir))
