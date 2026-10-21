"""Verificaciones enfocadas del paquete, identidad del modelo y carga única."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
from sklearn.naive_bayes import MultinomialNB

from ml.config import ROOT
from ml.data.download import sha256_file
from ml.inference.artifacts import canonical_hash, model_state_hash, read_json, write_json
from ml.inference.predictor import Predictor, get_predictor, verify_package
from ml.nlp.pipeline import build_pipeline
from ml.training.reproduce import export_package, historical_inputs


class ArtifactTests(unittest.TestCase):
    def make_pipeline(self):
        texts = [f"emojitoken_clase_{chr(97 + label)} funciona producto" for label in range(5)]
        return build_pipeline(min_df=1, max_df=1.0, classifier=MultinomialNB()).fit(texts, range(5))

    def package(self, directory):
        pipeline = self.make_pipeline()
        reference = {"model_id": "synthetic-model", "model_state_sha256": model_state_hash(pipeline), "config": read_json(ROOT / "config.json"), "evaluated_artifact_sha256": "a" * 64}
        metrics = {"model_id": "synthetic-model", "split": "test", "metrics": {"scope": "synthetic unit fixture"}}
        export_package(pipeline, metrics, reference, output_dir=directory, mode="full", provenance={"scope": "synthetic"})
        return pipeline, reference, metrics

    def test_state_identity_ignores_joblib_encoding_but_detects_changed_weights(self):
        pipeline = self.make_pipeline()
        before = model_state_hash(pipeline)
        with tempfile.TemporaryDirectory() as directory:
            plain, compressed = Path(directory) / "plain", Path(directory) / "compressed"
            joblib.dump(pipeline, plain, compress=0)
            joblib.dump(pipeline, compressed, compress=3)
            self.assertNotEqual(sha256_file(plain), sha256_file(compressed))
            self.assertEqual(model_state_hash(joblib.load(plain)), before)
            self.assertEqual(model_state_hash(joblib.load(compressed)), before)
        pipeline.named_steps["classifier"].feature_log_prob_[0, 0] += 0.01
        self.assertNotEqual(model_state_hash(pipeline), before)

    def test_corruption_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root)
            (root / "pipeline.joblib").write_bytes(b"corrupted")
            with patch("ml.inference.predictor.joblib.load") as load:
                with self.assertRaises(ValueError):
                    Predictor(root)
                load.assert_not_called()

    def test_model_metric_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root)
            metrics = read_json(root / "metrics.json")
            metrics["model_id"] = "another-model"
            write_json(root / "metrics.json", metrics)
            manifest = read_json(root / "manifest.json")
            manifest["metric_sha256"] = sha256_file(root / "metrics.json")
            write_json(root / "manifest.json", manifest)
            with self.assertRaises(ValueError):
                verify_package(root)

    def test_predictor_loads_once_and_never_trains_or_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline, _, _ = self.package(root)
            get_predictor.cache_clear()
            original_load = joblib.load
            with patch("ml.inference.predictor.joblib.load", wraps=original_load) as load, patch("sklearn.pipeline.Pipeline.fit", side_effect=AssertionError("No fitting during inference")), patch("urllib.request.urlopen", side_effect=AssertionError("No network during inference")):
                first = get_predictor(str(root))
                self.assertIs(first, get_predictor(str(root)))
                texts = ["emojitoken_clase_a funciona", "sin producto"]
                np.testing.assert_allclose(first.predict_proba(texts), pipeline.predict_proba(texts))
                response = first.predict(texts)
                self.assertEqual(set(response[0]["probabilities"]), {"1", "2", "3", "4", "5"})
                self.assertAlmostEqual(sum(response[0]["probabilities"].values()), 1.0)
                self.assertEqual(first.trace(texts[0])["model_id"], "synthetic-model")
                self.assertEqual(load.call_count, 1)
            get_predictor.cache_clear()

    def test_full_cannot_attach_test_metrics_to_different_learned_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline, reference, metrics = self.package(root)
            pipeline.named_steps["classifier"].feature_log_prob_[0, 0] += 0.02
            with self.assertRaises(ValueError):
                export_package(pipeline, metrics, reference, output_dir=root, mode="full", provenance={})
            quick = export_package(pipeline, {"model_id": "synthetic-quick", "split": "validation"}, reference, output_dir=root / "quick", mode="quick", provenance={"seed": 17})
            self.assertEqual(quick["seed"], 17)
            self.assertEqual(quick["metric_split"], "validation")
            self.assertFalse(quick["historical_test"]["reused"])

    def test_historical_evidence_is_canonical_and_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection = {"model_id": "synthetic-model"}
            metrics = {"model_id": "synthetic-model", "score": 0.5}
            ledger = {"status": "complete"}
            reference = {"model_id": "synthetic-model", "selection_canonical_sha256": canonical_hash(selection), "test_metrics_canonical_sha256": canonical_hash(metrics), "ledger_canonical_sha256": canonical_hash(ledger)}
            for name, value in (("model_selection", selection), ("test_metrics", metrics), ("final_test_ledger", ledger), ("frozen_reference", reference)):
                write_json(root / f"{name}.json", value)
            with patch("ml.training.reproduce.REPORTS_DIR", root):
                historical_inputs()
                metrics["score"] = 0.9
                write_json(root / "test_metrics.json", metrics)
                with self.assertRaises(ValueError):
                    historical_inputs()


if __name__ == "__main__":
    unittest.main()
