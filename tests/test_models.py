"""Controles pequeños de leakage, cinco clases y evaluación final única."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.naive_bayes import MultinomialNB

from ml.data.download import sha256_file
from ml.evaluation.evaluate import classification_metrics, labels_to_stars, validate_probabilities
from ml.evaluation.final_test import evaluate_final, reserve_evaluation
from ml.nlp.pipeline import build_pipeline
from ml.training.train import select_candidate


class ModelTests(unittest.TestCase):
    def test_stars_mapping_and_ordinal_metrics(self):
        np.testing.assert_array_equal(labels_to_stars([0, 1, 2, 3, 4]), [1, 2, 3, 4, 5])
        for invalid in ([5], [-1], [True], [0.5]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                labels_to_stars(invalid)
        metrics = classification_metrics([0, 1, 2, 3, 4], [0, 2, 2, 3, 0])
        self.assertAlmostEqual(metrics["mae_stars"], 1.0)
        self.assertAlmostEqual(metrics["accuracy"], 0.6)
        self.assertEqual(np.asarray(metrics["confusion_matrix"]).shape, (5, 5))
        self.assertEqual([row["stars"] for row in metrics["per_class"]], [1, 2, 3, 4, 5])

    def test_probabilities_require_five_ordered_classes_and_unit_sum(self):
        probabilities = np.full((2, 5), 0.2)
        validate_probabilities(probabilities, range(5))
        for values, classes in ((probabilities, [4, 3, 2, 1, 0]), (probabilities * 2, range(5)), (np.full((2, 5), np.nan), range(5)), (np.ones((2, 2)), range(5))):
            with self.subTest(), self.assertRaises(ValueError):
                validate_probabilities(values, classes)

    def test_cv_never_learns_vocabulary_from_heldout_fold(self):
        texts = [f"emojitoken_unique_{chr(97 + index)} clase{chr(97 + index % 5)}" for index in range(15)]
        labels = np.array([index % 5 for index in range(15)])
        folds = list(StratifiedKFold(3, shuffle=True, random_state=42).split(texts, labels))
        pipeline = build_pipeline(min_df=1, max_df=1.0, classifier=MultinomialNB())
        results = cross_validate(pipeline, texts, labels, cv=folds, return_estimator=True)
        for estimator, (train, heldout) in zip(results["estimator"], folds):
            vocabulary = estimator.named_steps["tfidf"].vocabulary_
            self.assertTrue(set(train).isdisjoint(heldout))
            for index in heldout:
                self.assertNotIn(f"emojitoken_unique_{chr(97 + index)}", vocabulary)
            for index in train:
                self.assertIn(f"emojitoken_unique_{chr(97 + index)}", vocabulary)

    def test_selection_uses_validation_f1_then_mae_and_ignores_test_scores(self):
        def candidate(name, f1, mae, test):
            return {"model": name, "morphology": "stemming", "ngram_range": [1, 2], "metrics": {"macro_f1": f1, "mae_stars": mae}, "test_f1": test}
        weaker = candidate("MultinomialNB", 0.4, 0.5, 0.99)
        stronger = candidate("LogisticRegression", 0.5, 0.8, 0.1)
        self.assertIs(select_candidate([weaker, stronger]), stronger)
        tied = candidate("MultinomialNB", 0.5, 0.6, 0.0)
        self.assertIs(select_candidate([stronger, tied]), tied)

    def test_incomplete_evaluation_reservation_also_blocks_repetition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reserve_evaluation(root / "final_test_ledger.json", {"model_id": "synthetic"})
            with self.assertRaises(RuntimeError):
                reserve_evaluation(root / "final_test_ledger.json", {"model_id": "synthetic"})
            with patch("ml.evaluation.final_test.joblib.load") as load:
                with self.assertRaises(RuntimeError):
                    evaluate_final(reports_dir=root, root=root, raw_dir=root)
                load.assert_not_called()

    def test_frozen_synthetic_champion_is_evaluated_only_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports, raw = root / "reports", root / "raw"
            reports.mkdir()
            raw.mkdir()
            texts = [f"emojitoken_clase_{chr(97 + label)}" for label in range(5)]
            pipeline = build_pipeline(min_df=1, max_df=1.0, classifier=MultinomialNB()).fit(texts, range(5))
            artifact = root / "pipeline.joblib"
            joblib.dump(pipeline, artifact)
            rows = [{"id": f"synthetic-{label}", "text": text, "label": label} for label, text in enumerate(texts)]
            (raw / "test.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            spec = {"name": "test.jsonl", "rows": 5, "bytes": (raw / "test.jsonl").stat().st_size, "sha256": sha256_file(raw / "test.jsonl")}
            config = {"seed": 42, "runtime": {"n_jobs": 1}, "dataset": {"repository": "synthetic/fixture", "revision": "a" * 40, "files": {split: {**spec, "name": f"{split}.jsonl"} for split in ("train", "validation", "test")}}}
            (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
            selection = {"mode": "full", "final_fit_split": "train_only", "artifact": artifact.name, "artifact_sha256": sha256_file(artifact), "config_sha256": sha256_file(root / "config.json"), "source_sha256": {}, "model_id": "synthetic-model"}
            (reports / "model_selection.json").write_text(json.dumps(selection), encoding="utf-8")
            first = evaluate_final(reports_dir=reports, root=root, raw_dir=raw)
            self.assertEqual(first["metrics"]["rows"], 5)
            self.assertEqual(json.loads((reports / "final_test_ledger.json").read_text())["status"], "complete")
            before = (reports / "test_metrics.json").read_bytes()
            with self.assertRaises(RuntimeError):
                evaluate_final(reports_dir=reports, root=root, raw_dir=raw)
            self.assertEqual((reports / "test_metrics.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
