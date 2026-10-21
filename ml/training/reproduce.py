"""Un comando desde el corpus fijado hasta paquetes full/quick, sin repetir test."""

import platform
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from threadpoolctl import threadpool_limits

from ml.config import ROOT, RAW_DIR, PROCESSED_DIR, REPORTS_DIR, load_config
from ml.data.download import download_dataset, sha256_file
from ml.data.eda import split_statistics
from ml.data.prepare import prepare_dataset
from ml.data.validate import audit_splits, iter_reviews
from ml.evaluation.evaluate import evaluate_pipeline
from ml.inference.artifacts import canonical_hash, inference_sources, model_state_hash, read_json, runtime_versions, verify_runtime, write_json
from ml.inference.predictor import verify_package
from ml.inference.probes import PROBE_TEXTS
from ml.nlp.compare import MemoryMonitor
from ml.training.export import ARTIFACT
from ml.training.pipelines import model_pipeline


def historical_inputs() -> tuple[dict, dict, dict]:
    reference = read_json(REPORTS_DIR / "frozen_reference.json")
    selection = read_json(REPORTS_DIR / "model_selection.json")
    metrics = read_json(REPORTS_DIR / "test_metrics.json")
    ledger = read_json(REPORTS_DIR / "final_test_ledger.json")
    for value, field in ((selection, "selection_canonical_sha256"), (metrics, "test_metrics_canonical_sha256"), (ledger, "ledger_canonical_sha256")):
        if canonical_hash(value) != reference[field]:
            raise ValueError("La evidencia histórica cambió; no se reproducirá con métricas diferentes.")
    if ledger["status"] != "complete" or selection["model_id"] != reference["model_id"]:
        raise ValueError("Se requiere la selección evaluada de la Fase D.")
    return reference, selection, metrics


def ensure_data(reference: dict, provenance_dir: Path, *, validation: bool) -> dict:
    needed = ("train", "validation") if validation else ("train",)
    cached = all((PROCESSED_DIR / f"{split}.jsonl").exists() and sha256_file(PROCESSED_DIR / f"{split}.jsonl") == reference[f"{split}_file_sha256"] for split in needed)
    if cached:
        return {"prepared_cache_verified": True, "train_sha256": reference["train_file_sha256"]}
    print("Obteniendo y auditando el corpus fijado...", flush=True)
    config = load_config()
    download_dataset(RAW_DIR, provenance_dir, config=config)
    audit = audit_splits({split: RAW_DIR / spec.name for split, spec in config.files.items()}, {split: spec.rows for split, spec in config.files.items()})
    preparation = prepare_dataset(RAW_DIR, PROCESSED_DIR)
    for split in needed:
        if sha256_file(PROCESSED_DIR / f"{split}.jsonl") != reference[f"{split}_file_sha256"]:
            raise ValueError("La preparación no reproduce el corpus de la selección congelada.")
    # EDA mínimo de train; las inspecciones de test se limitan a identidad/esquema.
    report = {"prepared_cache_verified": False, "audit": audit, "preparation": preparation, "train_statistics": split_statistics(PROCESSED_DIR / "train.jsonl", lexical=True), "test_model_scored": False}
    write_json(provenance_dir / "data_audit.json", report)
    return report


def export_package(pipeline, metrics: dict, reference: dict, *, output_dir: Path, mode: str, provenance: dict) -> dict:
    state = model_state_hash(pipeline)
    if mode not in {"quick", "full"}:
        raise ValueError("Modo de paquete inválido.")
    if mode == "full" and (state != reference["model_state_sha256"] or metrics["model_id"] != reference["model_id"]):
        raise ValueError("Un paquete full no puede asociar métricas históricas a otro estado aprendido.")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".joblib.part", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        pipeline.memory = None
        joblib.dump(pipeline, temporary, compress=3)
        restored = joblib.load(temporary)
        with threadpool_limits(limits=1):
            np.testing.assert_allclose(pipeline.predict_proba(list(PROBE_TEXTS)), restored.predict_proba(list(PROBE_TEXTS)), rtol=1e-7, atol=1e-8)
        temporary.replace(output_dir / "pipeline.joblib")
    finally:
        temporary.unlink(missing_ok=True)
    write_json(output_dir / "metrics.json", metrics)
    manifest = {
        "schema_version": "1.0", "model_id": metrics["model_id"], "mode": mode,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_file": "pipeline.joblib", "artifact_sha256": sha256_file(output_dir / "pipeline.joblib"),
        "artifact_bytes": (output_dir / "pipeline.joblib").stat().st_size,
        "model_state_sha256": state, "metric_file": "metrics.json", "metric_path": "metrics.json", "metric_sha256": sha256_file(output_dir / "metrics.json"), "metric_split": metrics["split"],
        "dataset_repository": reference["config"]["dataset"]["repository"], "dataset_revision": reference["config"]["dataset"]["revision"],
        "seed": provenance.get("seed", reference["config"]["seed"]), "nlp_config": "config.json", "config_canonical_sha256": canonical_hash(read_json(ROOT / "config.json")),
        "preprocessing": pipeline.named_steps["nlp"].get_params(deep=False),
        "tfidf": {name: getattr(pipeline.named_steps["tfidf"], name) for name in ("ngram_range", "min_df", "max_df", "max_features", "sublinear_tf")},
        "classifier": {"name": type(pipeline.named_steps["classifier"]).__name__, "parameters": pipeline.named_steps["classifier"].get_params(deep=False)},
        "feature_count": len(pipeline.named_steps["tfidf"].vocabulary_),
        "label_index_to_stars": {str(label): label + 1 for label in range(5)},
        "runtime": runtime_versions(), "python_version": platform.python_version(),
        "sklearn_version": runtime_versions()["scikit-learn"], "nlp_source_sha256": inference_sources(),
        "roundtrip_verified": True, "provenance": provenance,
        "historical_test": {"reused": mode == "full", "evaluated_artifact_sha256": reference["evaluated_artifact_sha256"] if mode == "full" else None, "model_state_matches_evaluated": state == reference["model_state_sha256"] if mode == "full" else False},
    }
    write_json(output_dir / "manifest.json", manifest)  # Publicar manifiesto al final.
    verify_package(output_dir)
    return manifest


def reproduce(*, mode: str, seed: int, output_dir: Path | None = None, rebuild: bool = False, morphology: str | None = None, ngram_max: int | None = None) -> dict:
    if mode not in {"quick", "full"} or seed != load_config().seed:
        raise ValueError("Modo o semilla incompatibles con la configuración.")
    if mode == "full" and (morphology is not None or ngram_max is not None):
        raise ValueError("Los cambios de NLP son experimentales: usa --mode quick.")
    reference, selection, historical_metrics = historical_inputs()
    if mode == "full":
        if canonical_hash(read_json(ROOT / "config.json")) != canonical_hash(reference["config"]) or inference_sources() != reference["nlp_source_sha256"]:
            raise ValueError("La configuración o NLP difieren del modelo evaluado; usa quick para experimentar.")
        verify_runtime(reference["runtime"])
    output_dir = output_dir or ROOT / "ml" / "artifacts" / mode
    if mode == "full" and not rebuild and (output_dir / "manifest.json").exists():
        manifest, _ = verify_package(output_dir)
        if manifest["model_state_sha256"] != reference["model_state_sha256"] or manifest["mode"] != "full":
            raise ValueError("El paquete existente no corresponde al campeón congelado.")
        print("Paquete full existente verificado.", flush=True)
        return manifest
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    with threadpool_limits(limits=1), MemoryMonitor() as memory:
        local_evaluated = mode == "full" and not rebuild and ARTIFACT.exists() and sha256_file(ARTIFACT) == reference["evaluated_artifact_sha256"]
        if local_evaluated:
            print("Empaquetando el checkpoint evaluado...", flush=True)
            pipeline = joblib.load(ARTIFACT)
            provenance = {"path": "evaluated_checkpoint_verified", "train_rows": reference["train_rows"]}
        else:
            data = ensure_data(reference, output_dir / "provenance", validation=mode == "quick")
            reviews = list(iter_reviews(PROCESSED_DIR / "train.jsonl"))
            if mode == "quick":
                size = reference["config"]["models"]["screen_train_rows"]
                indices, _ = next(StratifiedShuffleSplit(n_splits=1, train_size=size, random_state=seed).split(np.zeros(len(reviews)), [row.label for row in reviews]))
                reviews = [reviews[index] for index in sorted(indices)]
            chosen = selection["champion"]
            pipeline = model_pipeline(chosen["model"], morphology or chosen["morphology"], (1, ngram_max or chosen["ngram_range"][1]), seed=seed, parameter=next(iter(chosen["best_params"].values())))
            print(f"Ajustando {mode}: {len(reviews)} filas, {pipeline.named_steps['nlp'].morphology}...", flush=True)
            from ml.training.train import fit_converged

            fit_converged(pipeline, [row.text for row in reviews], [row.label for row in reviews])
            provenance = {"path": "retrained_frozen_parameters" if mode == "full" else "experimental_train_sample", "train_rows": len(reviews), "data_cache_verified": data["prepared_cache_verified"]}
        state = model_state_hash(pipeline)
        if mode == "full":
            if state != reference["model_state_sha256"]:
                raise ValueError("El estado aprendido no reproduce exactamente el campeón; no se asociarán sus métricas de test.")
            np.testing.assert_allclose(pipeline.predict_proba(reference["probes"]["texts"]), reference["probes"]["probabilities"], rtol=1e-7, atol=1e-8)
            metrics = historical_metrics
        else:
            validation = list(iter_reviews(PROCESSED_DIR / "validation.jsonl"))
            values, _ = evaluate_pipeline(pipeline, validation)
            metrics = {"model_id": f"reviewiq-quick-{state[:16]}", "split": "validation", "experimental": True, "metrics": values, "test_evaluated": False}
        provenance.update({"seed": seed, "wall_sec": time.perf_counter() - started_wall, "cpu_sec": time.process_time() - started_cpu, "test_evaluation_repeated": False})
        manifest = export_package(pipeline, metrics, reference, output_dir=output_dir, mode=mode, provenance=provenance)
    report = {"model_id": manifest["model_id"], "mode": mode, **provenance, "sampled_process_peak_rss_mib": memory.peak / 1024**2, "artifact_sha256": manifest["artifact_sha256"], "model_state_sha256": state}
    write_json(output_dir / "build_report.json", report)
    # Medir inferencia en otro proceso, sin conservar el corpus ni el entrenador.
    environment = os.environ.copy()
    environment.update({name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    subprocess.run([sys.executable, "-m", "ml.inference.benchmark", "--package-dir", str(output_dir.resolve())], cwd=ROOT, env=environment, check=True)
    return manifest
