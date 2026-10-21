"""Verificaciones enfocadas en negaciones, trazabilidad y ausencia de leakage."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
from scipy.sparse import isspmatrix_csr
from sklearn.base import clone
from sklearn.naive_bayes import MultinomialNB

from ml.nlp.compare import load_comparison_data
from ml.nlp.normalize import normalize_text
from ml.nlp.pipeline import build_pipeline
from ml.nlp.trace import trace_pipeline
from ml.nlp.transformer import ReviewTextPreprocessor


class NLPTests(unittest.TestCase):
    def test_normalization_unicode_urls_numbers_and_complete_emojis(self):
        normalized = normalize_text("ＭＡＬÍＳＩＭＯ envió 2,5 días!!! https://ejemplo.invalid/a?b=1 😡 👩‍🚀")
        self.assertTrue(normalized.startswith("malísimo envió numerotoken días urltoken"))
        self.assertEqual(normalized.count("numerotoken"), 1)
        self.assertEqual(sum(word.startswith("emojitoken_") for word in normalized.split()), 2)
        self.assertNotIn("ejemplo", normalized)
        self.assertEqual(normalize_text("envió envío", preserve_accents=False), "envio envio")
        self.assertEqual(normalize_text("128 GB", number_policy="keep"), "128 gb")
        self.assertEqual(normalize_text("bien 😍", emoji_policy="remove"), "bien")

    def test_negations_markers_and_trace_share_the_transform_in_both_methods(self):
        text = "No me gustó ni funciona, sin garantía, nunca jamás. 2 días 😡"
        for method in ("stemming", "lemmatization"):
            with self.subTest(method=method):
                processor = ReviewTextPreprocessor(morphology=method, extra_stopwords=("no",)).fit([])
                trace = processor.trace(text)
                for word in ("no", "ni", "sin", "nunca", "jamás", "numerotoken"):
                    self.assertIn(word, trace["processed_tokens"])
                self.assertIn("me", trace["removed_stopwords"])
                self.assertEqual(processor.transform([text]), [trace["processed_text"]])
                self.assertEqual(len(trace["processed_tokens"]), len(trace["tokens_after_stopwords"]))

    def test_spanish_lemma_is_real_and_stemming_reduces_inflections(self):
        lemma = ReviewTextPreprocessor(morphology="lemmatization").fit([])
        self.assertIn("comprar", lemma.trace("Ayer compré un producto nuevo")["processed_tokens"])
        stem = ReviewTextPreprocessor().fit([])
        tokens = stem.trace("funcionando funciona")["processed_tokens"]
        self.assertEqual(tokens[0], tokens[1])

    def test_sklearn_cloning_and_changes_require_refit(self):
        processor = ReviewTextPreprocessor(extra_stopwords=("producto",)).fit([])
        cloned = clone(processor)
        self.assertEqual(cloned.get_params(), processor.get_params())
        self.assertFalse(hasattr(cloned, "stopwords_"))
        processor.set_params(number_policy="keep")
        with self.assertRaises(ValueError):
            processor.transform(["2 días"])
        processor.fit([])
        self.assertIn("2", processor.transform(["2 días"])[0])

    def test_tfidf_matches_trace_is_sparse_float32_and_does_not_fit_holdout(self):
        pipeline = build_pipeline(min_df=1, max_df=1.0)
        train = ["No funciona la batería", "Funciona muy bien", "Sin garantía llegó roto"]
        matrix = pipeline.fit_transform(train)
        self.assertTrue(isspmatrix_csr(matrix))
        self.assertEqual(matrix.dtype, np.float32)
        trace = trace_pipeline(pipeline, train[0])
        vectorizer = pipeline.named_steps["tfidf"]
        self.assertIn("no funcion", trace["ngrams"])
        self.assertEqual(trace["ngrams"], vectorizer.build_analyzer()(pipeline.named_steps["nlp"].transform([train[0]])[0]))
        before = dict(vectorizer.vocabulary_)
        pipeline.transform(["palabraexclusivadevalidacion"])
        self.assertEqual(vectorizer.vocabulary_, before)
        self.assertNotIn("palabraexclusivadevalidacion", before)

    def test_serialization_preserves_prediction_probabilities_and_trace(self):
        texts = ["No funciona, llegó roto 😡", "Sin garantía no sirve", "Excelente producto funciona bien 😍", "Muy bueno, lo recomiendo"]
        for method in ("stemming", "lemmatization"):
            with self.subTest(method=method), tempfile.TemporaryDirectory() as directory:
                pipeline = build_pipeline(morphology=method, min_df=1, max_df=1.0, classifier=MultinomialNB())
                pipeline.fit(texts, [0, 0, 4, 4])
                path = Path(directory) / "trusted-local-test.joblib"
                joblib.dump(pipeline, path)
                restored = joblib.load(path)
                np.testing.assert_allclose(pipeline.predict_proba(texts), restored.predict_proba(texts), rtol=1e-7)
                self.assertEqual(trace_pipeline(pipeline, texts[0]), trace_pipeline(restored, texts[0]))

    def test_comparison_sampling_is_reproducible_without_a_test_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split, repeats in (("train", 4), ("validation", 1)):
                records = [{"id": f"{split}-{label}-{index}", "text": f"Texto único {split} {label} {index}", "label": label} for label in range(5) for index in range(repeats)]
                (root / f"{split}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
            with patch("ml.nlp.compare.PROCESSED_DIR", root):
                selected, _, metadata = load_comparison_data(10, 42)
                repeated, _, repeated_metadata = load_comparison_data(10, 42)
            self.assertEqual(selected, repeated)
            self.assertEqual(metadata, repeated_metadata)
            self.assertEqual(set(row.label for row in selected), set(range(5)))
            self.assertFalse(metadata["test_accessed"])


if __name__ == "__main__":
    unittest.main()
