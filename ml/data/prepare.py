"""Proyecta columnas y limpia solamente train; conserva las particiones oficiales."""

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from ml.config import PROCESSED_DIR, RAW_DIR, REPORTS_DIR, SPLITS, load_config
from ml.data.download import download_dataset, write_json
from ml.data.validate import iter_reviews, text_key


def prepare_dataset(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> dict:
    if raw_dir.resolve() == processed_dir.resolve():
        raise ValueError("Los datos preparados no pueden sobrescribir el origen.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    heldout_ids: set[str] = set()
    heldout_texts: set[str] = set()
    for split in ("validation", "test"):
        for review in iter_reviews(raw_dir / f"{split}.jsonl"):
            heldout_ids.add(review.id)
            heldout_texts.add(text_key(review.text))

    labels_by_text: dict[str, set[int]] = defaultdict(set)
    for review in iter_reviews(raw_dir / "train.jsonl"):
        labels_by_text[text_key(review.text)].add(review.label)
    conflicting = {key for key, labels in labels_by_text.items() if len(labels) > 1}

    results = {}
    for split in SPLITS:
        removed: Counter = Counter()
        labels: Counter = Counter()
        seen_ids: set[str] = set()
        seen_texts: set[str] = set()
        source_rows = 0
        output = processed_dir / f"{split}.jsonl"
        with output.open("w", encoding="utf-8", newline="\n") as stream:
            for review in iter_reviews(raw_dir / f"{split}.jsonl"):
                source_rows += 1
                key = text_key(review.text)
                if split == "train":
                    if review.id in heldout_ids or key in heldout_texts:
                        removed["overlap_with_validation_or_test"] += 1
                        continue
                    if key in conflicting:
                        removed["conflicting_labels_for_same_text"] += 1
                        continue
                    if review.id in seen_ids or key in seen_texts:
                        removed["duplicate_within_train"] += 1
                        continue
                    seen_ids.add(review.id)
                    seen_texts.add(key)
                labels[review.label] += 1
                stream.write(json.dumps(asdict(review), ensure_ascii=False) + "\n")
        results[split] = {
            "source_rows": source_rows,
            "prepared_rows": sum(labels.values()),
            "removed_rows_by_reason": dict(removed),
            "label_counts": {str(label): labels[label] for label in range(5)},
        }
    return {
        "policy": "Remove train overlaps with either holdout, all train text groups with conflicting labels, then keep first train ID/text. Preserve holdout rows, order, text and labels; drop only unused columns.",
        "columns": ["id", "text", "label"],
        "splits": results,
        "selection": "No predictions or holdout scores used; only identity checks across splits.",
    }


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    config = load_config()
    download_dataset(config=config)
    # Validar el corpus completo antes de producir las salidas preparadas.
    from ml.data.validate import audit_splits

    audit_splits(
        {split: RAW_DIR / spec.name for split, spec in config.files.items()},
        {split: spec.rows for split, spec in config.files.items()},
    )
    report = prepare_dataset()
    write_json(REPORTS_DIR / "data_preparation.json", report)
    print(json.dumps(report["splits"], indent=2))


if __name__ == "__main__":
    main()
