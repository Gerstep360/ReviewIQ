"""Registrar metadatos, sin cuerpo, query string ni texto de reseñas."""

import logging
import time

from backend.api.service import model_service

logger = logging.getLogger('reviewiq.api')


class APIMetadataLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/v1/'):
            return self.get_response(request)
        started = time.perf_counter()
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store'
        logger.info('api method=%s status=%s duration_ms=%.3f model_id=%s', request.method, response.status_code, (time.perf_counter() - started) * 1000, model_service.model_id or 'unavailable')
        return response
