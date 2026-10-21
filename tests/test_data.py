"""Pruebas pequeñas de los riesgos de datos, sin red ni corpus externo."""

import hashlib
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from ml.config import DatasetFile, SPLITS, load_config
from ml.data.download import verify_file
from ml.data.prepare import prepare_dataset
from ml.data.validate import audit_splits, iter_reviews, parse_review, text_key


def write_rows(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def fixture(split: str) -> list[dict]:
    return [{"id": f"{split}-{label}", "text": f"Texto {split} clase {label}", "label": label, "label_text": str(label)} for label in range(5)]


class DataTests(unittest.TestCase):
    def test_schema_rejects_invalid_records_and_drops_label_text(self) -> None:
        valid = fixture("train")[0]
        self.assertEqual(set(asdict(parse_review(valid))), {"id", "text", "label"})
        invalid = [{}, {**valid, "text": None}, {**valid, "text": "  "}, {**valid, "id": ""}, {**valid, "label": True}, {**valid, "label": 5}, {**valid, "label": "0"}]
        for record in invalid:
            with self.subTest(record=record), self.assertRaises(ValueError):
                parse_review(record)

    def test_audit_detects_duplicates_and_cross_split_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = {split: Path(directory) / f"{split}.jsonl" for split in SPLITS}
            rows = {split: fixture(split) for split in SPLITS}
            rows["train"].append({**rows["train"][0], "id": "another-id"})
            rows["validation"][0] = {**rows["validation"][0], "id": "train-0", "text": "  TEXTO train   clase 0 "}
            for split in SPLITS:
                write_rows(paths[split], rows[split])
            report = audit_splits(paths, {split: len(rows[split]) for split in SPLITS})
            self.assertEqual(report["splits"]["train"]["duplicate_normalized_text_rows"], 1)
            overlap = report["overlaps"]["train__validation"]
            self.assertEqual((overlap["shared_ids"], overlap["shared_normalized_texts"]), (1, 1))
            with self.assertRaises(ValueError):
                audit_splits(paths, {split: 999 for split in SPLITS})

    def test_preparation_removes_train_leakage_and_preserves_holdouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw"
            processed = Path(directory) / "processed"
            raw.mkdir()
            rows = {split: fixture(split) for split in SPLITS}
            rows["train"] += [
                {"id": "overlap-text", "text": rows["test"][0]["text"].upper(), "label": 0},
                {"id": rows["validation"][0]["id"], "text": "Otro texto", "label": 0},
                {**rows["train"][0], "id": "duplicate"},
                {"id": "conflict-1", "text": "Etiqueta incierta", "label": 1},
                {"id": "conflict-2", "text": "ETIQUETA incierta", "label": 4},
            ]
            for split in SPLITS:
                write_rows(raw / f"{split}.jsonl", rows[split])
            original_bytes = {split: (raw / f"{split}.jsonl").read_bytes() for split in SPLITS}
            result = prepare_dataset(raw, processed)
            prepared = {split: list(iter_reviews(processed / f"{split}.jsonl")) for split in SPLITS}
            self.assertEqual(result["splits"]["train"]["prepared_rows"], 5)
            for split in ("validation", "test"):
                self.assertEqual(prepared[split], [parse_review(row) for row in rows[split]])
                self.assertFalse({text_key(row.text) for row in prepared["train"]} & {text_key(row.text) for row in prepared[split]})
            for split in SPLITS:
                self.assertEqual((raw / f"{split}.jsonl").read_bytes(), original_bytes[split])
            output_record = json.loads((processed / "train.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(set(output_record), {"id", "text", "label"})
            with self.assertRaises(ValueError):
                prepare_dataset(raw, raw)

    def test_checksum_rejects_same_size_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_bytes(b"original")
            spec = DatasetFile(path.name, 1, 8, hashlib.sha256(b"original").hexdigest())
            self.assertEqual(verify_file(path, spec), spec.sha256)
            path.write_bytes(b"modified")
            with self.assertRaises(ValueError):
                verify_file(path, spec)

    def test_config_uses_pinned_revision_and_original_splits(self) -> None:
        config = load_config()
        self.assertEqual((config.seed, config.n_jobs), (42, 1))
        self.assertEqual(len(config.revision), 40)
        self.assertEqual({split: spec.rows for split, spec in config.files.items()}, {"train": 200000, "validation": 5000, "test": 5000})


if __name__ == "__main__":
    unittest.main()
