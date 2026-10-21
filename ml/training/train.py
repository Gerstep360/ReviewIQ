"""Cribado, CV y selección con validación. Este módulo nunca abre test."""

import argparse
import csv
import json
import platform
import tempfile
import time
import warnings
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from ml.config import PROCESSED_DIR, REPORTS_DIR, ROOT, load_config
from ml.data.download import sha256_file, write_json
from ml.data.validate import Review, iter_reviews
from ml.evaluation.evaluate import classification_metrics, evaluate_pipeline, plot_confusion, validate_probabilities
from ml.nlp.compare import MemoryMonitor, load_comparison_data
from ml.nlp.pipeline import build_vectorizer, nlp_settings
from ml.nlp.transformer import ReviewTextPreprocessor
from ml.training.export import ARTIFACT, freeze_champion
from ml.training.pipelines import MODEL_NAMES, make_classifier, model_pipeline, model_settings
from ml.training.tune import tune_model


def select_candidate(candidates: list[dict]) -> dict:
    """Criterio fijado antes de test, independiente del orden de ejecución."""
    return min(candidates, key=lambda row: (-row["metrics"]["macro_f1"], row["metrics"]["mae_stars"], row["model"], row["morphology"], tuple(row["ngram_range"])))


def fit_converged(estimator, X, y) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        estimator.fit(X, y)
    if any(issubclass(item.category, ConvergenceWarning) for item in caught):
        raise RuntimeError("Ajuste sin convergencia: detener selección antes de abrir test.")


def screen_candidates(train: list[Review], validation: list[Review], *, seed: int) -> list[dict]:
    settings = nlp_settings()
    train_texts, validation_texts = [row.text for row in train], [row.text for row in validation]
    labels, actual = [row.label for row in train], [row.label for row in validation]
    results = []
    for method in settings["morphology_candidates"]:
        print(f"Cribado NLP: {method}", flush=True)
        processor = ReviewTextPreprocessor(morphology=method, **settings["preprocessing"])
        processed_train = processor.fit_transform(train_texts)
        processed_validation = processor.transform(validation_texts)
        for ngrams in settings["ngram_candidates"]:
            vectorizer = build_vectorizer(tuple(ngrams), **settings["tfidf"])
            matrix = vectorizer.fit_transform(processed_train)
            heldout = vectorizer.transform(processed_validation)
            for name in MODEL_NAMES:
                classifier = make_classifier(name, seed=seed, max_iter=model_settings()["logistic_max_iter"])
                started = time.perf_counter()
                fit_converged(classifier, matrix, labels)
                probabilities = validate_probabilities(classifier.predict_proba(heldout), classifier.classes_)
                predicted = classifier.classes_[np.argmax(probabilities, axis=1)]
                results.append({"model": name, "morphology": method, "ngram_range": ngrams, "train_rows": len(train), "metrics": classification_metrics(actual, predicted), "vocabulary_size": len(vectorizer.vocabulary_), "classifier_fit_predict_sec": time.perf_counter() - started, "convergence_warnings": 0})
    return results


def write_comparison_csv(path: Path, results: list[dict]) -> None:
    rows = [{"model": item["model"], "morphology": item["morphology"], "ngram_range": str(item["ngram_range"]), "parameter": json.dumps(item.get("best_params", {})), "train_rows": item["train_rows"], **{key: item["metrics"][key] for key in ("macro_f1", "accuracy", "mae_stars")}, "vocabulary_size": item["vocabulary_size"]} for item in results]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def train_models(*, mode: str = "full", seed: int = 42) -> dict:
    if mode not in {"quick", "full"}:
        raise ValueError("Modo permitido: quick o full.")
    if seed != load_config().seed:
        raise ValueError("La semilla debe coincidir con config.json.")
    if mode == "full" and ((REPORTS_DIR / "final_test_ledger.json").exists() or (REPORTS_DIR / "test_metrics.json").exists()):
        raise RuntimeError("La evaluación final ya está reservada/realizada. No se sobrescribirá la selección full.")
    reports = REPORTS_DIR if mode == "full" else REPORTS_DIR / "quick"
    reports.mkdir(parents=True, exist_ok=True)
    settings = model_settings()
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    with threadpool_limits(limits=1), MemoryMonitor() as memory:
        sample, validation, provenance = load_comparison_data(settings["screen_train_rows"], seed)
        # Verificar continuidad con el corpus auditado en las fases B/C.
        previous = json.loads((REPORTS_DIR / "nlp_comparison.json").read_text(encoding="utf-8"))["provenance"]
        for field in ("train_file_sha256", "validation_file_sha256"):
            if provenance[field] != previous[field]:
                raise ValueError("El corpus preparado cambió desde la Fase C; audita los datos antes de entrenar.")
        write_json(reports / "selection_protocol.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "mode": mode, "seed": seed, "config": settings, "provenance": provenance, "test_accessed": False, "decision": "Compare eight fixed NLP/model combinations on sample, pick NLP per model using validation, tune alpha/C with 3-fold train-only CV, refit two finalists on train only, select by validation macro-F1 then MAE then stable model/config name."})
        screening = screen_candidates(sample, validation, seed=seed)
        write_json(reports / "model_screening.json", {"scope": "sample train/validation only", "candidates": screening})
        write_comparison_csv(reports / "model_screening.csv", screening)
        finalists, fitted, cv_reports = [], {}, []
        fit_reviews = sample if mode == "quick" else list(iter_reviews(PROCESSED_DIR / "train.jsonl"))
        for name in MODEL_NAMES:
            candidate = select_candidate([row for row in screening if row["model"] == name])
            print(f"CV 3 folds: {name}, {candidate['morphology']}, {candidate['ngram_range']}", flush=True)
            with tempfile.TemporaryDirectory(dir=ROOT / "ml" / "artifacts", prefix="cv-") as temporary:
                best_params, cv_report = tune_model(candidate, sample, seed=seed, cache_dir=Path(temporary))
            cv_reports.append(cv_report)
            write_json(reports / "cv_results.json", {"scope": "sample train only, all TF-IDF fits inside each fold", "models": cv_reports})
            parameter = next(iter(best_params.values()))
            pipeline = model_pipeline(name, candidate["morphology"], tuple(candidate["ngram_range"]), seed=seed, parameter=parameter)
            print(f"Ajuste {name}: {len(fit_reviews)} filas de train, {best_params}", flush=True)
            fit_start = time.perf_counter()
            fit_converged(pipeline, [row.text for row in fit_reviews], [row.label for row in fit_reviews])
            metrics, _ = evaluate_pipeline(pipeline, validation)
            iterations = getattr(pipeline.named_steps["classifier"], "n_iter_", [])
            result = {"model": name, "morphology": candidate["morphology"], "ngram_range": candidate["ngram_range"], "best_params": best_params, "train_rows": len(fit_reviews), "metrics": metrics, "vocabulary_size": len(pipeline.named_steps["tfidf"].vocabulary_), "fit_and_validation_wall_sec": time.perf_counter() - fit_start, "solver_iterations": np.asarray(iterations).tolist(), "convergence_warnings": 0}
            finalists.append(result)
            fitted[name] = pipeline
            write_comparison_csv(reports / "model_comparison.csv", finalists)
        champion = select_candidate(finalists)
        chosen = fitted[champion["model"]]
        majority = int(np.bincount([row.label for row in fit_reviews], minlength=5).argmax())
        selection = freeze_champion(chosen, {
            "mode": mode, "final_fit_split": "train_only", "train_rows": len(fit_reviews),
            "dataset_revision": load_config().revision, "provenance": provenance,
            "champion": champion, "selection_rule": settings["selection_rule"],
        }, [row.text for row in validation[:10]], artifact=ARTIFACT if mode == "full" else ARTIFACT.with_name("quick_pipeline.joblib"), selection_path=reports / "model_selection.json")
        plot_confusion(champion["metrics"], reports / "validation_confusion_matrix.png", title="Campeón — validación para selección")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "model_id": selection["model_id"],
        "mode": mode, "split": "validation", "models": finalists, "provenance": provenance,
        "majority_baseline": {"trained": False, "predicted_label": majority, "metrics": classification_metrics([row.label for row in validation], [majority] * len(validation))},
        "wall_sec": time.perf_counter() - started_wall, "cpu_sec": time.process_time() - started_cpu,
        "sampled_process_peak_rss_mib": memory.peak / 1024**2,
        "machine": {"os": platform.platform(), "python": platform.python_version(), "processor": platform.processor()},
        "versions": {name: version(name) for name in ("scikit-learn", "numpy", "nltk", "spacy", "es-core-news-sm")},
        "test_accessed": False, "warning": "Validation scores were used for selection; only the frozen champion may be scored once on test. Quick results are experimental.",
    }
    write_json(reports / "model_comparison.json", report)
    return selection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = train_models(mode=args.mode, seed=args.seed)
    print(json.dumps({"model_id": result["model_id"], "champion": result["champion"]["model"], "mode": result["mode"], "test_accessed": False}, indent=2))


if __name__ == "__main__":
    main()
