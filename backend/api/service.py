"""Cargar un paquete confiable una vez por proceso, fuera de las vistas."""

import logging
from contextlib import contextmanager
from threading import BoundedSemaphore, Lock

from django.conf import settings

from backend.api.exceptions import ModelBusy, ModelUnavailable

logger = logging.getLogger('reviewiq.api')


class ModelService:
    def __init__(self):
        self._startup_lock = Lock()
        self._inference_slot = BoundedSemaphore(1)
        self._initialized = False
        self._predictor = None
        self._metrics = None

    @property
    def model_id(self):
        return self._predictor.manifest['model_id'] if self._predictor is not None else None

    def start(self):
        with self._startup_lock:
            if self._initialized:
                return
            self._initialized = True
            try:
                # Import diferido: manage.py check y la generación de schema no cargan ML.
                from ml.inference.predictor import get_predictor

                predictor = get_predictor(str(settings.REVIEWIQ_MODEL_DIR.resolve()))
                predictor.predict(['Producto de ejemplo para inicializar el servicio.'])
                metrics = self._build_metrics(predictor)
                self._metrics = metrics
                self._predictor = predictor
                logger.info('model_ready model_id=%s mode=%s', self.model_id, predictor.manifest['mode'])
            except Exception as exc:
                logger.error('model_unavailable type=%s; verifica el paquete y reinicia el servidor', type(exc).__name__)

    @staticmethod
    def _build_metrics(predictor):
        from ml.inference.artifacts import read_json

        manifest, stored = predictor.manifest, predictor.metrics
        steps = predictor.pipeline.named_steps
        comparison = None
        path = settings.BASE_DIR / 'reports/model_comparison.json'
        if manifest['mode'] == 'full' and path.exists():
            candidate = read_json(path)
            if candidate.get('model_id') == manifest['model_id'] and candidate.get('mode') == 'full' and candidate.get('split') == 'validation':
                comparison = {key: candidate[key] for key in ('model_id', 'split', 'generated_at_utc', 'models')}
        return {
            'model_id': manifest['model_id'], 'mode': manifest['mode'],
            'split': stored['split'], 'experimental': manifest['mode'] == 'quick',
            'evaluated_at_utc': stored.get('evaluated_at_utc'),
            'packaged_at_utc': manifest['created_at_utc'],
            'dataset': {'repository': manifest['dataset_repository'], 'revision': manifest['dataset_revision']},
            'configuration': {
                'preprocessing': steps['nlp'].get_params(deep=False),
                'tfidf': {key: getattr(steps['tfidf'], key) for key in ('ngram_range', 'max_features', 'min_df', 'max_df', 'sublinear_tf')},
                'classifier': {'name': type(steps['classifier']).__name__, 'parameters': steps['classifier'].get_params(deep=False)},
                'feature_count': manifest['feature_count'], 'seed': manifest['seed'],
            },
            'metrics': {key: value for key, value in stored['metrics'].items() if key != 'error_analysis'},
            'comparison': comparison,
            'probability_notice': 'Las probabilidades son estimaciones del modelo; no representan certeza calibrada.',
        }

    def require_predictor(self):
        self.start()  # Respaldo para TestClient/embebidos; WSGI/ASGI lo llama al iniciar.
        if self._predictor is None:
            raise ModelUnavailable()
        return self._predictor

    @contextmanager
    def inference(self):
        predictor = self.require_predictor()
        if not self._inference_slot.acquire(timeout=settings.REVIEWIQ_QUEUE_TIMEOUT_SECONDS):
            raise ModelBusy()
        try:
            yield predictor
        finally:
            self._inference_slot.release()

    def metrics(self):
        self.require_predictor()
        return self._metrics


model_service = ModelService()
