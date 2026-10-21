"""Validación estricta y auditoría de duplicados sin publicar textos ni IDs."""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterator, Mapping

from ml.config import SPLITS


@dataclass(frozen=True)
class Review:
    id: str
    text: str
    label: int


def parse_review(record: object, location: str = "registro") -> Review:
    if not isinstance(record, dict) or not {"id", "text", "label"}.issubset(record):
        raise ValueError(f"{location}: faltan id, text o label.")
    if not isinstance(record["id"], str) or not record["id"].strip():
        raise ValueError(f"{location}: ID nulo, vacío o de tipo incorrecto.")
    if not isinstance(record["text"], str) or not record["text"].strip():
        raise ValueError(f"{location}: texto nulo, vacío o de tipo incorrecto.")
    if type(record["label"]) is not int or record["label"] not in range(5):
        raise ValueError(f"{location}: label debe ser un entero entre 0 y 4.")
    # label_text y cualquier otra columna nunca entran al registro preparado.
    return Review(record["id"], record["text"], record["label"])


def iter_reviews(path: Path) -> Iterator[Review]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            location = f"{path.name}:{line_number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"{location}: JSON inválido.") from None
            yield parse_review(record, location)


def text_key(text: str) -> str:
    """Identidad para auditoría; no transforma la entrada futura al modelo."""
    normalized = " ".join(text.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def audit_splits(
    paths: Mapping[str, Path], expected_rows: Mapping[str, int] | None = None
) -> dict:
    if set(paths) != set(SPLITS):
        raise ValueError("Se requieren train, validation y test sin recombinarlos.")
    ids: dict[str, Counter] = {}
    texts: dict[str, Counter] = {}
    exact_texts: dict[str, Counter] = {}
    summaries = {}
    conflicts = {}
    for split in SPLITS:
        id_counts: Counter = Counter()
        text_counts: Counter = Counter()
        exact_counts: Counter = Counter()
        labels: Counter = Counter()
        labels_by_text: dict[str, set[int]] = {}
        count = 0
        for review in iter_reviews(paths[split]):
            count += 1
            id_counts[review.id] += 1
            key = text_key(review.text)
            text_counts[key] += 1
            exact_counts[hashlib.sha256(review.text.encode("utf-8")).hexdigest()] += 1
            labels_by_text.setdefault(key, set()).add(review.label)
            labels[review.label] += 1
        if expected_rows and count != expected_rows[split]:
            raise ValueError(f"{split}: {count} filas; se esperaban {expected_rows[split]}.")
        if set(labels) != set(range(5)):
            raise ValueError(f"{split}: faltan clases de 0 a 4.")
        ids[split], texts[split], exact_texts[split] = id_counts, text_counts, exact_counts
        conflicts[split] = sum(len(values) > 1 for values in labels_by_text.values())
        summaries[split] = {
            "rows": count,
            "label_counts": {str(label): labels[label] for label in range(5)},
            "class_proportions": {str(label): labels[label] / count for label in range(5)},
            "null_empty_or_invalid_records": 0,
            "duplicate_id_rows": count - len(id_counts),
            "duplicate_exact_text_rows": count - len(exact_counts),
            "duplicate_normalized_text_rows": count - len(text_counts),
            "normalized_text_groups_with_conflicting_labels": conflicts[split],
        }
    overlaps = {}
    for left, right in combinations(SPLITS, 2):
        shared_ids = ids[left].keys() & ids[right].keys()
        shared_texts = texts[left].keys() & texts[right].keys()
        overlaps[f"{left}__{right}"] = {
            "shared_ids": len(shared_ids),
            "shared_exact_texts": len(exact_texts[left].keys() & exact_texts[right].keys()),
            "shared_normalized_texts": len(shared_texts),
            f"{left}_rows_with_shared_text": sum(texts[left][key] for key in shared_texts),
            f"{right}_rows_with_shared_text": sum(texts[right][key] for key in shared_texts),
        }
    return {
        "splits": summaries,
        "overlaps": overlaps,
        "text_identity": "casefold + collapse whitespace + SHA-256; accents and punctuation preserved",
        "validation": "fail-fast on invalid records; zero invalid rows means every row passed",
    }
