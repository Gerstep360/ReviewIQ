"""Registra la identidad semántica del checkpoint realmente evaluado en Fase D."""

import joblib
from threadpoolctl import threadpool_limits

from ml.config import ROOT, REPORTS_DIR
from ml.data.download import sha256_file
from ml.inference.artifacts import canonical_hash, inference_sources, model_state_hash, read_json, runtime_versions, write_json
from ml.inference.probes import PROBE_TEXTS


def create_reference() -> dict:
    selection = read_json(REPORTS_DIR / "model_selection.json")
    metrics = read_json(REPORTS_DIR / "test_metrics.json")
    ledger = read_json(REPORTS_DIR / "final_test_ledger.json")
    artifact = ROOT / selection["artifact"]
    if selection["model_id"] != metrics["model_id"] or ledger["status"] != "complete":
        raise ValueError("No existe un campeón con evaluación final completa.")
    if sha256_file(artifact) != selection["artifact_sha256"] or selection["artifact_sha256"] != ledger["artifact_sha256"]:
        raise ValueError("Solo se puede registrar el checkpoint original realmente evaluado.")
    if sha256_file(REPORTS_DIR / "test_metrics.json") != ledger["test_metrics_sha256"] or sha256_file(REPORTS_DIR / "model_selection.json") != ledger["selection_sha256"]:
        raise ValueError("La evidencia histórica no conserva los bytes evaluados.")
    for name in inference_sources():
        relative = f"ml/nlp/{name}"
        if sha256_file(ROOT / relative) != selection["source_sha256"][relative]:
            raise ValueError("El NLP ya no corresponde al checkpoint evaluado.")
    pipeline = joblib.load(artifact)
    with threadpool_limits(limits=1):
        probabilities = pipeline.predict_proba(list(PROBE_TEXTS)).tolist()
    reference = {
        "schema_version": "1.0", "model_id": selection["model_id"],
        "evaluated_artifact_sha256": selection["artifact_sha256"],
        "model_state_sha256": model_state_hash(pipeline),
        "config": read_json(ROOT / "config.json"), "runtime": runtime_versions(),
        "nlp_source_sha256": inference_sources(),
        "test_metrics_canonical_sha256": canonical_hash(metrics),
        "selection_canonical_sha256": canonical_hash(selection),
        "ledger_canonical_sha256": canonical_hash(ledger),
        "train_file_sha256": selection["provenance"]["train_file_sha256"],
        "validation_file_sha256": selection["provenance"]["validation_file_sha256"],
        "train_rows": selection["train_rows"],
        "probes": {"texts": list(PROBE_TEXTS), "probabilities": probabilities, "scope": "synthetic, not validation or test"},
        "identity": "Exact learned-state hash; pickle byte equality is not required. Historical test metrics remain tied to the evaluated state.",
    }
    write_json(REPORTS_DIR / "frozen_reference.json", reference)
    return reference


if __name__ == "__main__":
    print(create_reference()["model_id"])
