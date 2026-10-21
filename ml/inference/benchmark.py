"""Coste real de inferencia local, sin HTTP ni textos del corpus."""

import argparse
import platform
import time
from pathlib import Path

import numpy as np
import psutil

from ml.inference.artifacts import write_json
from ml.inference.predictor import DEFAULT_PACKAGE, Predictor
from ml.inference.probes import PROBE_TEXTS
from ml.nlp.compare import MemoryMonitor


def benchmark(package_dir: Path = DEFAULT_PACKAGE) -> dict:
    process = psutil.Process()
    baseline_rss = process.memory_info().rss
    started = time.perf_counter()
    with MemoryMonitor() as memory:
        predictor = Predictor(package_dir)
        load_wall = time.perf_counter() - started
        # Incluye carga lazy de spaCy; no se mezcla con los percentiles calientes.
        cold_start = time.perf_counter()
        predictor.predict([PROBE_TEXTS[0]])
        cold_predict = time.perf_counter() - cold_start
        for _ in range(3):
            predictor.predict([PROBE_TEXTS[1]])
        single_times = []
        for text in PROBE_TEXTS * 3:
            start = time.perf_counter()
            predictor.predict([text])
            single_times.append((time.perf_counter() - start) * 1000)
        batch = list(PROBE_TEXTS) * 10
        batch_times = []
        for _ in range(7):
            start = time.perf_counter()
            predictor.predict(batch)
            batch_times.append((time.perf_counter() - start) * 1000)
    return {
        "model_id": predictor.manifest["model_id"], "mode": predictor.manifest["mode"],
        "scope": "local Predictor.predict, no HTTP; synthetic phrases; one process and one computation thread",
        "package_load_sec": load_wall, "cold_first_prediction_sec": cold_predict,
        "warmup_single_calls": 3,
        "single": {"calls": len(single_times), "p50_ms": float(np.percentile(single_times, 50)), "p95_ms": float(np.percentile(single_times, 95))},
        "batch_100": {"calls": len(batch_times), "p50_ms": float(np.percentile(batch_times, 50)), "p95_ms": float(np.percentile(batch_times, 95))},
        "baseline_rss_mib": baseline_rss / 1024**2, "idle_loaded_rss_mib": process.memory_info().rss / 1024**2,
        "sampled_process_peak_rss_mib": memory.peak / 1024**2,
        "artifact_bytes": (package_dir / "pipeline.joblib").stat().st_size,
        "machine": {"os": platform.platform(), "python": platform.python_version(), "cpu": platform.processor(), "logical_cpus": psutil.cpu_count(), "ram_total_gib": psutil.virtual_memory().total / 1024**3},
        "limitation": "Not an API benchmark. Batch percentile uses seven observations; RSS is sampled every 50ms and includes the interpreter and loaded libraries.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE)
    args = parser.parse_args()
    report = benchmark(args.package_dir)
    write_json(args.package_dir / "performance.json", report)
    print(report["single"])
