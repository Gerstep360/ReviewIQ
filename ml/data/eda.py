"""Genera auditoría y figuras agregadas; no entrena ni publica reseñas."""

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from ml.config import PROCESSED_DIR, RAW_DIR, REPORTS_DIR, ROOT, SPLITS, load_config
from ml.data.download import download_dataset, sha256_file, write_json
from ml.data.prepare import prepare_dataset
from ml.data.validate import audit_splits, iter_reviews

WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)
FEATURES = {
    "numbers": re.compile(r"\d"),
    "urls": re.compile(r"https?://|www\.", re.IGNORECASE),
    "accented_spanish_characters": re.compile(r"[áéíóúüñ]", re.IGNORECASE),
    "emoji_heuristic": re.compile("[\U0001F1E6-\U0001FAFF\u2600-\u27BF]"),
}
HISTOGRAM_EDGES = [0, 50, 100, 200, 400, 800, 1600, 3200, 10000]


def describe(values: list[int]) -> dict:
    ordered = sorted(values)

    def quantile(fraction: float) -> float:
        index = (len(ordered) - 1) * fraction
        lower = int(index)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)

    return {
        "min": ordered[0], "max": ordered[-1], "mean": round(fmean(values), 4),
        "p50": quantile(0.5), "p90": quantile(0.9), "p95": quantile(0.95),
    }


def top_words(counts: Counter, limit: int = 20) -> list[dict]:
    return [{"word": word, "count": count} for word, count in counts.most_common(limit)]


def split_statistics(path: Path, *, lexical: bool) -> dict:
    characters: list[int] = []
    tokens: list[int] = []
    occurrences: Counter = Counter()
    words: Counter = Counter()
    by_label = {label: Counter() for label in range(5)}
    histogram = [0] * (len(HISTOGRAM_EDGES) - 1)
    for review in iter_reviews(path):
        length = len(review.text)
        tokenized = WORDS.findall(review.text.casefold())
        characters.append(length)
        tokens.append(len(tokenized))
        for feature, pattern in FEATURES.items():
            occurrences[feature] += bool(pattern.search(review.text))
        for index, (low, high) in enumerate(zip(HISTOGRAM_EDGES, HISTOGRAM_EDGES[1:])):
            if low <= length < high:
                histogram[index] += 1
                break
        else:
            raise ValueError("Longitud fuera del rango del histograma; revisar sus límites.")
        if lexical:
            words.update(tokenized)
            by_label[review.label].update(tokenized)
    result = {
        "characters": describe(characters),
        "word_tokens": describe(tokens),
        "text_features": {
            feature: {"rows": occurrences[feature], "proportion": occurrences[feature] / len(characters)}
            for feature in FEATURES
        },
        "character_histogram": {"edges": HISTOGRAM_EDGES, "counts": histogram},
    }
    if lexical:
        result["frequent_words"] = top_words(words)
        result["frequent_words_by_label"] = {str(label): top_words(counts) for label, counts in by_label.items()}
    return result


def plot_summary(summary: dict, output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.6), layout="constrained")
    for axis, split in zip(axes, SPLITS):
        counts = summary["audit"]["splits"][split]["label_counts"]
        axis.bar(range(1, 6), list(counts.values()), color="#206b78")
        axis.set(title=split, xlabel="Estrellas (label + 1)", ylabel="Reseñas", xticks=range(1, 6))
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Distribución original de clases")
    figure.savefig(output_dir / "class_distribution.png", dpi=150)
    plt.close(figure)

    histogram = summary["statistics"]["train"]["character_histogram"]
    intervals = [f"{a}–{b - 1}" for a, b in zip(histogram["edges"], histogram["edges"][1:])]
    figure, axis = plt.subplots(figsize=(9, 4), layout="constrained")
    axis.bar(intervals, histogram["counts"], color="#206b78")
    axis.set(title="Longitud de reseñas de train", xlabel="Caracteres por reseña", ylabel="Reseñas")
    axis.tick_params(axis="x", rotation=30)
    axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output_dir / "train_lengths.png", dpi=150)
    plt.close(figure)

    frequent = summary["statistics"]["train"]["frequent_words"][:15]
    figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    axis.barh([entry["word"] for entry in frequent][::-1], [entry["count"] for entry in frequent][::-1], color="#206b78")
    axis.set(title="Palabras más frecuentes en train (sin quitar stop words)", xlabel="Ocurrencias")
    axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output_dir / "train_frequent_words.png", dpi=150)
    plt.close(figure)


def run_eda(raw_dir: Path = RAW_DIR, reports_dir: Path = REPORTS_DIR) -> dict:
    config = load_config()
    manifest = download_dataset(raw_dir, reports_dir, config=config)
    paths = {split: raw_dir / spec.name for split, spec in config.files.items()}
    audit = audit_splits(paths, {split: spec.rows for split, spec in config.files.items()})
    preparation = prepare_dataset(raw_dir, PROCESSED_DIR)
    prepared_audit = audit_splits(
        {split: PROCESSED_DIR / f"{split}.jsonl" for split in SPLITS},
        {split: preparation["splits"][split]["prepared_rows"] for split in SPLITS},
    )
    for pair in ("train__validation", "train__test"):
        overlap = prepared_audit["overlaps"][pair]
        if overlap["shared_ids"] or overlap["shared_normalized_texts"]:
            raise ValueError(f"Persisten solapamientos tras preparar {pair}.")
    preparation["audit_after_preparation"] = prepared_audit
    write_json(reports_dir / "data_preparation.json", preparation)
    summary = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": config.repository,
        "revision": config.revision,
        "seed": config.seed,
        "n_jobs": config.n_jobs,
        "config_sha256": sha256_file(ROOT / "config.json"),
        "source_files": {split: {key: value for key, value in info.items() if key in {"bytes", "sha256"}} for split, info in manifest["files"].items()},
        "audit": audit,
        "statistics": {split: split_statistics(path, lexical=split == "train") for split, path in paths.items()},
        "preparation": preparation,
        "methodology": {
            "word_tokens": "Unicode alphabetic sequences, casefold, without stop-word removal; descriptive EDA only",
            "lexical_scope": "train only; no vocabulary or preprocessing selected from validation/test",
            "holdouts": "Only schema, balance, identity and descriptive length/feature audits. No model fitting or scoring.",
            "emojis": "Approximate Unicode range detection, not grapheme segmentation",
            "future_cv": "Stratified folds, shuffle=True, random_state=42, cleaned train only; not executed in this phase",
        },
    }
    write_json(reports_dir / "eda_summary.json", summary)
    plot_summary(summary, reports_dir / "figures")
    return summary


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    summary = run_eda()
    print(json.dumps({"raw_rows": {s: summary["audit"]["splits"][s]["rows"] for s in SPLITS}, "prepared_train": summary["preparation"]["splits"]["train"]["prepared_rows"], "report": "reports/eda_summary.json"}, indent=2))


if __name__ == "__main__":
    main()
