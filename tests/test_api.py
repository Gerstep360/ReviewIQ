"""Pruebas enfocadas de contratos HTTP, sin base de datos ni entrenamiento real."""

import json
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

import joblib
import numpy as np
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient
from sklearn.naive_bayes import MultinomialNB

from backend.api.service import ModelService
from ml.config import ROOT
from ml.inference.artifacts import model_state_hash, read_json
from ml.inference.predictor import get_predictor
from ml.nlp.pipeline import build_pipeline
from ml.training.reproduce import export_package


@override_settings(ALLOWED_HOSTS=['testserver'], REVIEWIQ_QUEUE_TIMEOUT_SECONDS=0.01)
class APITests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory = tempfile.TemporaryDirectory()
        cls.package_dir = Path(cls.directory.name)
        cls.pipeline = build_pipeline(min_df=1, max_df=1.0, classifier=MultinomialNB()).fit(
            [f'emojitoken_clase_{chr(97 + label)} producto' for label in range(5)], range(5)
        )
        cls.metrics = {
            'model_id': 'synthetic-api-fixture', 'split': 'test', 'evaluated_at_utc': '2026-10-21T00:00:00Z',
            'metrics': {'rows': 5, 'macro_f1': 1.0, 'accuracy': 1.0, 'mae_stars': 0.0,
                'per_class': [{'label': label, 'stars': label + 1, 'precision': 1., 'recall': 1., 'f1': 1., 'support': 1} for label in range(5)],
                'confusion_matrix': np.eye(5, dtype=int).tolist()},
        }
        reference = {'model_id': cls.metrics['model_id'], 'model_state_sha256': model_state_hash(cls.pipeline), 'config': read_json(ROOT / 'config.json'), 'evaluated_artifact_sha256': '0' * 64}
        export_package(cls.pipeline, cls.metrics, reference, output_dir=cls.package_dir, mode='full', provenance={'scope': 'synthetic unit fixture'})

    @classmethod
    def tearDownClass(cls):
        get_predictor.cache_clear()
        cls.directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(override_settings(REVIEWIQ_MODEL_DIR=self.package_dir))
        self.service = ModelService()
        for name in ('backend.apps.analytics.views', 'backend.apps.predictions.views', 'backend.api.middleware'):
            self.stack.enter_context(patch(f'{name}.model_service', self.service))
        self.client = APIClient()

    def test_startup_loads_once_and_requests_do_not_fit_or_download(self):
        get_predictor.cache_clear()
        with patch('ml.inference.predictor.joblib.load', wraps=joblib.load) as load, patch('sklearn.pipeline.Pipeline.fit', side_effect=AssertionError('No fit')), patch('urllib.request.urlopen', side_effect=AssertionError('No network')):
            self.service.start()
            for _ in range(2):
                response = self.client.get('/api/v1/health/')
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()['model_loaded'])
                self.assertEqual(self.client.post('/api/v1/predict/', {'text': 'emojitoken_clase_a'}, format='json').status_code, 200)
            self.assertEqual(load.call_count, 1)

    def test_missing_or_corrupt_model_returns_503_without_retry(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(REVIEWIQ_MODEL_DIR=Path(directory)), patch('ml.inference.predictor.joblib.load') as load:
            self.service.start()
            health = self.client.get('/api/v1/health/')
            self.assertEqual(health.status_code, 503)
            self.assertFalse(health.json()['model_loaded'])
            for endpoint, method in (('predict/', 'post'), ('nlp/trace/', 'post'), ('metrics/', 'get')):
                response = getattr(self.client, method)('/api/v1/' + endpoint, {'text': 'reseña'}, format='json') if method == 'post' else self.client.get('/api/v1/' + endpoint)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn(directory, response.content.decode())
            load.assert_not_called()
        # Un paquete corrupto tampoco llega a Joblib.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manifest.json').write_bytes((self.package_dir / 'manifest.json').read_bytes())
            (root / 'pipeline.joblib').write_bytes(b'corrupted')
            with override_settings(REVIEWIQ_MODEL_DIR=root), patch('ml.inference.predictor.joblib.load') as load:
                broken = ModelService()
                broken.start()
                self.assertIsNone(broken.model_id)
                load.assert_not_called()

    def test_invalid_input_encoding_size_and_media_type(self):
        payloads = [{}, {'text': ''}, {'text': ' \n\t'}, {'text': None}, {'text': 3}, {'text': True}, {'text': []}, {'text': 'a' * 3001}, {'text': '\0'}, [], {'text': 'bien', 'morphology': 'stemming'}]
        for endpoint in ('predict/', 'nlp/trace/'):
            for payload in payloads:
                with self.subTest(endpoint=endpoint, payload_type=type(payload).__name__):
                    response = self.client.post('/api/v1/' + endpoint, payload, format='json')
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()['error']['code'], 'invalid_input')
            for content in (b'{broken', b'{"text":"\xff"}', b'{"text":"\\ud800"}'):
                self.assertEqual(self.client.generic('POST', '/api/v1/' + endpoint, content, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.generic('POST', '/api/v1/predict/', b'{"text":"bien"}', content_type='application/json; charset=latin-1').status_code, 400)
        self.assertEqual(self.client.generic('POST', '/api/v1/predict/', b' ' * (64 * 1024 + 1), content_type='application/json').status_code, 413)
        self.assertEqual(self.client.generic('POST', '/api/v1/predict/', b'hello', content_type='text/plain').status_code, 415)
        self.assertEqual(self.client.get('/api/v1/predict/').status_code, 405)
        self.assertEqual(self.client.post('/api/v1/predict', {'text': 'bien'}, format='json').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/health').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/unknown').json()['error']['code'], 'not_found')
        self.assertEqual(self.client.post('/api/v1/predict/', {'text': 'a' * 3000}, format='json').status_code, 200)

    def test_class_mapping_probabilities_and_private_error_response(self):
        for token, stars in (('a', 1), ('e', 5)):
            response = self.client.post('/api/v1/predict/', {'text': f'emojitoken_clase_{token}'}, format='json')
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertEqual((result['label'], result['stars']), (stars - 1, stars))
            self.assertEqual(set(result['probabilities']), set('12345'))
            self.assertAlmostEqual(sum(result['probabilities'].values()), 1.)
            self.assertGreaterEqual(result['inference_ms'], 0)
        with patch.object(self.service.require_predictor(), 'predict', side_effect=RuntimeError('private review body')):
            response = self.client.post('/api/v1/predict/', {'text': 'private review body'}, format='json')
            self.assertEqual(response.status_code, 500)
            self.assertNotIn('private', response.content.decode())
        with patch.object(self.service.require_predictor(), 'predict', return_value=[{'stars': 1, 'model_id': 'bad', 'probabilities': dict.fromkeys('12345', 0.1), 'experimental': False}]):
            self.assertEqual(self.client.post('/api/v1/predict/', {'text': 'bien'}, format='json').status_code, 500)
        self.service._inference_slot.acquire()
        try:
            response = self.client.post('/api/v1/predict/', {'text': 'bien'}, format='json')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['error']['code'], 'model_busy')
        finally:
            self.service._inference_slot.release()

    def test_trace_is_shared_and_bounded(self):
        text = 'No funciona, sin garantía 😡'
        response = self.client.post('/api/v1/nlp/trace/', {'text': text}, format='json')
        self.assertEqual(response.status_code, 200)
        trace = response.json()
        direct = self.service.require_predictor().trace(text)
        for key, value in direct.items():
            self.assertEqual(trace[key], value)
        self.assertIn('no', trace['processed_tokens'])
        self.assertFalse(trace['truncated'])
        trace = self.client.post('/api/v1/nlp/trace/', {'text': 'bueno ' * 450}, format='json').json()
        self.assertTrue(trace['truncated'])
        self.assertEqual(len(trace['tokens']), 200)
        self.assertEqual(trace['original_counts']['tokens'], 450)

    def test_metrics_match_active_model_and_exclude_unrelated_comparison(self):
        response = self.client.get('/api/v1/metrics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['model_id'], self.metrics['model_id'])
        self.assertEqual(data['metrics']['confusion_matrix'], self.metrics['metrics']['confusion_matrix'])
        self.assertEqual(data['split'], 'test')
        self.assertIsNone(data['comparison'])  # El informe real de D es de otro modelo.
        comparison = {'model_id': self.metrics['model_id'], 'mode': 'full', 'split': 'validation', 'generated_at_utc': 'synthetic-fixture', 'models': []}
        with patch('ml.inference.artifacts.read_json', return_value=comparison):
            payload = ModelService._build_metrics(self.service.require_predictor())
            self.assertEqual(payload['comparison']['split'], 'validation')

    def test_openapi_docs_and_restricted_cors(self):
        schema = self.client.get('/api/schema/').json()
        self.assertIn('/api/v1/predict/', schema['paths'])
        self.assertIn('413', schema['paths']['/api/v1/predict/']['post']['responses'])
        self.assertEqual(self.client.get('/docs/').status_code, 200)
        for origin, allowed in (('http://localhost:5173', True), ('https://untrusted.invalid', False)):
            response = self.client.options('/api/v1/predict/', HTTP_ORIGIN=origin, HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST', HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type')
            self.assertEqual('Access-Control-Allow-Origin' in response, allowed)
        with self.assertLogs('reviewiq.api', level='INFO') as records:
            self.client.post('/api/v1/predict/?text=do-not-log-this', {'text': 'private review body'}, format='json')
        self.assertNotIn('private review body', str(records.output))
        self.assertNotIn('do-not-log-this', str(records.output))


@override_settings(ALLOWED_HOSTS=['testserver'])
class RealPackageAPITests(SimpleTestCase):
    @unittest.skipUnless((settings.REVIEWIQ_MODEL_DIR / 'manifest.json').exists(), 'Paquete local ausente; genera full según README.')
    def test_frozen_package_api_matches_direct_pipeline_offline(self):
        service = ModelService()
        with ExitStack() as stack:
            for name in ('backend.apps.analytics.views', 'backend.apps.predictions.views', 'backend.api.middleware'):
                stack.enter_context(patch(f'{name}.model_service', service))
            stack.enter_context(patch('sklearn.pipeline.Pipeline.fit', side_effect=AssertionError('No fit')))
            stack.enter_context(patch('urllib.request.urlopen', side_effect=AssertionError('No network')))
            service.start()
            predictor = service.require_predictor()
            # Tres primeras filas de validation si están disponibles; nunca test.
            path = ROOT / 'ml/data/processed/validation.jsonl'
            if path.exists():
                with path.open(encoding='utf-8') as stream:
                    texts = [json.loads(next(stream))['text'] for _ in range(3)]
            else:
                texts = ['No funciona', 'Excelente producto', 'Aceptable, pero esperaba más']
            client = APIClient()
            for text, probabilities in zip(texts, predictor.pipeline.predict_proba(texts)):
                response = client.post('/api/v1/predict/', {'text': text}, format='json')
                self.assertEqual(response.status_code, 200)
                np.testing.assert_allclose(list(response.json()['probabilities'].values()), probabilities, rtol=1e-7, atol=1e-8)
            metrics = client.get('/api/v1/metrics/').json()
            self.assertEqual(metrics['model_id'], predictor.manifest['model_id'])
            self.assertEqual(metrics['metrics']['macro_f1'], predictor.metrics['metrics']['macro_f1'])
            self.assertEqual(metrics['comparison']['model_id'], metrics['model_id'])


if __name__ == '__main__':
    unittest.main()
