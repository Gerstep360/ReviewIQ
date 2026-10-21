"""Checkpoint del campeón y selección congelada antes de abrir test."""

from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from ml.config import ROOT
from ml.data.download import sha256_file, write_json

ARTIFACT = ROOT / "ml" / "artifacts" / "reviewiq_pipeline.joblib"


def source_hashes() -> dict[str, str]:
    paths = [ROOT / "ml" / "config.py"]
    for package in ("nlp", "training", "evaluation"):
        paths.extend(sorted((ROOT / "ml" / package).glob("*.py")))
    return {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in paths}


def freeze_champion(pipeline, metadata: dict, probe_texts: list[str], *, artifact: Path = ARTIFACT, selection_path: Path) -> dict:
    artifact.parent.mkdir(parents=True, exist_ok=True)
    # El caché de CV no debe convertirse en una dependencia del artefacto.
    pipeline.memory = None
    joblib.dump(pipeline, artifact, compress=3)
    restored = joblib.load(artifact)
    np.testing.assert_allclose(pipeline.predict_proba(probe_texts), restored.predict_proba(probe_texts), rtol=1e-7, atol=1e-8)
    digest = sha256_file(artifact)
    selection = {
        **metadata, "model_id": f"reviewiq-{digest[:16]}",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": artifact.relative_to(ROOT).as_posix() if artifact.is_relative_to(ROOT) else str(artifact),
        "artifact_sha256": digest, "artifact_bytes": artifact.stat().st_size,
        "decision_rule": "argmax over ordered classes 0..4; stars = label + 1; no threshold",
        "label_index_to_stars": {str(label): label + 1 for label in range(5)},
        "config_sha256": sha256_file(ROOT / "config.json"),
        "source_sha256": source_hashes(), "roundtrip_verified": True,
        "test_accessed_during_selection": False,
    }
    write_json(selection_path, selection)
    return selection
