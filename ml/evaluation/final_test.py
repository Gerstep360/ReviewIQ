"""Una sola evaluación del campeón congelado, con registro exclusivo persistente."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from threadpoolctl import threadpool_limits

from ml.config import RAW_DIR, REPORTS_DIR, ROOT, load_config
from ml.data.download import sha256_file, verify_file, write_json
from ml.data.validate import iter_reviews
from ml.evaluation.evaluate import evaluate_pipeline, plot_confusion


def reserve_evaluation(ledger: Path, metadata: dict) -> dict:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    reservation = {**metadata, "status": "started", "started_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with ledger.open("x", encoding="utf-8") as stream:
            json.dump(reservation, stream, indent=2)
    except FileExistsError:
        raise RuntimeError("Test ya fue reservado o evaluado. No se repetirá ni sobrescribirá el registro.") from None
    return reservation


def evaluate_final(*, reports_dir: Path = REPORTS_DIR, root: Path = ROOT, raw_dir: Path = RAW_DIR) -> dict:
    ledger = reports_dir / "final_test_ledger.json"
    if ledger.exists() or (reports_dir / "test_metrics.json").exists():
        raise RuntimeError("Ya existe una evaluación final o su reserva; usa los resultados guardados.")
    selection_path = reports_dir / "model_selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection["mode"] != "full" or selection["final_fit_split"] != "train_only":
        raise ValueError("Solo puede evaluarse el campeón full ajustado exclusivamente con train.")
    artifact = root / selection["artifact"]
    if sha256_file(artifact) != selection["artifact_sha256"]:
        raise ValueError("El pipeline cambió después de congelar la selección.")
    if sha256_file(root / "config.json") != selection["config_sha256"]:
        raise ValueError("La configuración cambió después de congelar la selección.")
    for name, digest in selection["source_sha256"].items():
        if sha256_file(root / name) != digest:
            raise ValueError(f"Código diferente al congelado: {name}.")
    metadata = {"model_id": selection["model_id"], "selection_sha256": sha256_file(selection_path), "artifact_sha256": selection["artifact_sha256"]}
    reservation = reserve_evaluation(ledger, metadata)
    # A partir de la reserva no hay reintento automático, aunque falle el proceso.
    config = load_config(root / "config.json")
    test_path = raw_dir / config.files["test"].name
    verify_file(test_path, config.files["test"])
    reviews = list(iter_reviews(test_path))
    if len(reviews) != config.files["test"].rows:
        raise ValueError("Número de filas test inesperado.")
    pipeline = joblib.load(artifact)
    with threadpool_limits(limits=1):
        metrics, _ = evaluate_pipeline(pipeline, reviews)
    result = {
        **metadata, "split": "test", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_revision": config.revision, "test_file_sha256": sha256_file(test_path),
        "metrics": metrics, "selection_frozen_before_test": True,
        "purpose": "Final estimate only. Do not use these scores to redesign or select the model.",
    }
    write_json(reports_dir / "test_metrics.json", result)
    write_json(ledger, {**reservation, "status": "complete", "evaluated_at_utc": result["evaluated_at_utc"], "test_metrics_sha256": sha256_file(reports_dir / "test_metrics.json")})
    return result


def render_saved_test(reports_dir: Path = REPORTS_DIR) -> None:
    # Regenerar una figura a partir de la matriz guardada no vuelve a predecir test.
    result = json.loads((reports_dir / "test_metrics.json").read_text(encoding="utf-8"))
    plot_confusion(result["metrics"], reports_dir / "confusion_matrix.png", title="Campeón — evaluación final de test")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()
    if args.render_only:
        render_saved_test()
    else:
        result = evaluate_final()
        render_saved_test()
        print(json.dumps({"model_id": result["model_id"], **{key: result["metrics"][key] for key in ("macro_f1", "accuracy", "mae_stars")}}, indent=2))


if __name__ == "__main__":
    main()
