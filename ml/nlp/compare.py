"""Comparación experimental de NLP en train/validation; jamás abre test."""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version

import numpy as np
import psutil
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from ml.config import PROCESSED_DIR, REPORTS_DIR, ROOT, load_config
from ml.data.download import sha256_file, write_json
from ml.data.validate import iter_reviews, text_key
from ml.nlp.pipeline import build_vectorizer, nlp_settings
from ml.nlp.transformer import NLP_POLICY_VERSION, ReviewTextPreprocessor
from ml.nlp.stopwords import STOPWORDS_VERSION


class MemoryMonitor:
    """RSS total del proceso muestreado; incluye intérprete, corpus y recursos."""
    def __enter__(self):
        self.process = psutil.Process()
        self.peak = self.process.memory_info().rss
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.thread.start()
        return self

    def _sample(self):
        while not self.stop.wait(0.05):
            self.peak = max(self.peak, self.process.memory_info().rss)

    def __exit__(self, *args):
        self.peak = max(self.peak, self.process.memory_info().rss)
        self.stop.set()
        self.thread.join()


def load_comparison_data(train_rows: int, seed: int):
    train_path = PROCESSED_DIR / "train.jsonl"
    validation_path = PROCESSED_DIR / "validation.jsonl"
    if not train_path.exists() or not validation_path.exists():
        raise FileNotFoundError("Ejecuta python -m ml.data.eda antes de comparar NLP.")
    train = list(iter_reviews(train_path))
    validation = list(iter_reviews(validation_path))
    if train_rows < 5 or train_rows > len(train):
        raise ValueError("La muestra debe incluir las cinco clases y caber en train.")
    if train_rows == len(train):
        indices = np.arange(len(train))
    else:
        sampler = StratifiedShuffleSplit(n_splits=1, train_size=train_rows, random_state=seed)
        indices, _ = next(sampler.split(np.zeros(len(train)), [row.label for row in train]))
    selected = [train[index] for index in sorted(indices)]
    heldout_ids = {row.id for row in validation}
    heldout_texts = {text_key(row.text) for row in validation}
    if any(row.id in heldout_ids or text_key(row.text) in heldout_texts for row in train):
        raise ValueError("Train preparado comparte IDs/textos con validation; regenera la Fase B.")
    metadata = {
        "train_rows_available": len(train), "train_rows_sampled": len(selected),
        "validation_rows": len(validation), "seed": seed,
        "sample_label_counts": dict(sorted(Counter(str(row.label) for row in selected).items())),
        "sample_ids_sha256": hashlib.sha256("\n".join(row.id for row in selected).encode()).hexdigest(),
        "train_file_sha256": sha256_file(train_path), "validation_file_sha256": sha256_file(validation_path),
        "test_accessed": False,
    }
    return selected, validation, metadata


def evaluate_method(method: str) -> dict:
    config, settings = load_config(), nlp_settings()
    if settings["comparison"]["classifier"] != "MultinomialNB":
        raise ValueError("Esta comparación fija MultinomialNB como baseline; no selecciona el modelo final.")
    with threadpool_limits(limits=config.n_jobs), MemoryMonitor() as memory:
        train, validation, provenance = load_comparison_data(settings["comparison"]["train_rows"], config.seed)
        train_texts, train_labels = [row.text for row in train], [row.label for row in train]
        validation_texts, validation_labels = [row.text for row in validation], [row.label for row in validation]
        preprocessor = ReviewTextPreprocessor(morphology=method, **settings["preprocessing"])
        wall_start, cpu_start = time.perf_counter(), time.process_time()
        processed_train = preprocessor.fit_transform(train_texts)
        processed_validation = preprocessor.transform(validation_texts)
        preprocess_wall = time.perf_counter() - wall_start
        preprocess_cpu = time.process_time() - cpu_start
        results = []
        for ngrams in settings["ngram_candidates"]:
            wall_start, cpu_start = time.perf_counter(), time.process_time()
            vectorizer = build_vectorizer(tuple(ngrams), **settings["tfidf"])
            matrix = vectorizer.fit_transform(processed_train)
            validation_matrix = vectorizer.transform(processed_validation)
            classifier = MultinomialNB(alpha=settings["comparison"]["alpha"])
            classifier.fit(matrix, train_labels)
            predicted = classifier.predict(validation_matrix)
            # La composición reutiliza los mismos objetos ya ajustados.
            pipeline = Pipeline([("nlp", preprocessor), ("tfidf", vectorizer), ("classifier", classifier)])
            probe = validation_texts[:8]
            if not np.allclose(pipeline.predict_proba(probe), classifier.predict_proba(validation_matrix[:8]), rtol=1e-6):
                raise AssertionError("La composición no coincide con las etapas medidas.")
            results.append({
                "morphology": method, "ngram_min": ngrams[0], "ngram_max": ngrams[1],
                "classifier": "MultinomialNB", "alpha": settings["comparison"]["alpha"],
                "train_rows": len(train), "validation_rows": len(validation),
                "macro_f1_validation": float(f1_score(validation_labels, predicted, average="macro", labels=list(range(5)))),
                "accuracy_validation": float(accuracy_score(validation_labels, predicted)),
                "vocabulary_size": len(vectorizer.vocabulary_), "train_nnz": int(matrix.nnz),
                "train_sparsity": 1.0 - matrix.nnz / (matrix.shape[0] * matrix.shape[1]),
                "train_csr_mib": (matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes) / 1024**2,
                "dtype": str(matrix.dtype),
                "preprocessing_wall_sec": preprocess_wall, "preprocessing_cpu_sec": preprocess_cpu,
                "vectorization_fit_predict_wall_sec": time.perf_counter() - wall_start,
                "vectorization_fit_predict_cpu_sec": time.process_time() - cpu_start,
            })
    for result in results:
        result["method_process_peak_rss_mib"] = memory.peak / 1024**2
    return {"results": results, "provenance": provenance, "stopwords_sha256": preprocessor.stopwords_sha256_}


def run_comparison() -> dict:
    settings = nlp_settings()
    outputs = []
    for method in settings["morphology_candidates"]:
        print(f"Comparando {method} sobre train/validation...", flush=True)
        # Proceso separado por método: no heredar la caché de spaCy ni su RAM.
        environment = os.environ.copy()
        environment.update({key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
        worker = subprocess.run(
            [sys.executable, "-m", "ml.nlp.compare", "--worker", method],
            cwd=ROOT, env=environment, check=True, capture_output=True, text=True, encoding="utf-8",
        )
        outputs.append(json.loads(worker.stdout))
    if any(output["provenance"] != outputs[0]["provenance"] for output in outputs[1:]):
        raise ValueError("Las variantes no usaron exactamente la misma muestra.")
    results = [result for output in outputs for result in output["results"]]
    # Mayor F1; en empate exacto preferir menor CPU de preprocesamiento.
    best = max(results, key=lambda row: (row["macro_f1_validation"], -row["preprocessing_cpu_sec"]))
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "exploratory NLP selection with a fixed MultinomialNB baseline; validation only, not final model metrics",
        "provenance": outputs[0]["provenance"],
        "dataset_revision": load_config().revision,
        "config_sha256": sha256_file(ROOT / "config.json"),
        "versions": {name: version(name) for name in ["scikit-learn", "nltk", "spacy", "es-core-news-sm", "emoji", "numpy"]},
        "preprocessing": settings["preprocessing"], "tfidf": settings["tfidf"],
        "policy": {"version": NLP_POLICY_VERSION, "stopwords_version": STOPWORDS_VERSION, "stopwords_sha256": outputs[0]["stopwords_sha256"]},
        "nlp_source_sha256": {path.name: sha256_file(path) for path in sorted((ROOT / "ml" / "nlp").glob("*.py"))},
        "results": results,
        "experimental_recommendation": {key: best[key] for key in ["morphology", "ngram_min", "ngram_max", "macro_f1_validation"]},
        "measurement": "One CPU process per morphology; preprocessing shared by its two n-gram variants. RSS is the 50ms sampled peak for the entire method process, not per candidate. Wall/CPU excludes interpreter startup; CSR bytes measure the training matrix only.",
        "limitations": "No CV, LogisticRegression comparison, final test evaluation, or deployable artifact. Preprocessing policies were fixed for this experiment, not compared exhaustively. Recommendations may change with the classifier and full train in Phase D.",
    }
    write_json(REPORTS_DIR / "nlp_comparison.json", report)
    with (REPORTS_DIR / "nlp_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=["stemming", "lemmatization"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(evaluate_method(args.worker)))
    else:
        report = run_comparison()
        print(json.dumps(report["experimental_recommendation"], indent=2))


if __name__ == "__main__":
    main()
