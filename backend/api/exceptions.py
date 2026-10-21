"""Errores públicos en español, sin incluir texto ni excepciones internas."""

import logging

from django.core.exceptions import RequestDataTooBig
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

logger = logging.getLogger('reviewiq.api')


class ModelUnavailable(APIException):
    status_code = 503
    default_code = 'model_unavailable'
    default_detail = 'El modelo no está disponible. Verifica el paquete y reinicia el servidor.'


class ModelBusy(APIException):
    status_code = 503
    default_code = 'model_busy'
    default_detail = 'El modelo está ocupado. Intenta nuevamente en unos segundos.'


class PayloadTooLarge(APIException):
    status_code = 413
    default_code = 'payload_too_large'
    default_detail = 'El cuerpo JSON supera el límite de 64 KiB.'


def api_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    if isinstance(exc, RequestDataTooBig):
        exc = PayloadTooLarge()
    response = exception_handler(exc, context)
    if response is None:
        # El mensaje de una excepción puede contener la reseña: no registrarlo.
        logger.error('api_error type=%s', type(exc).__name__)
        return Response({'error': {'code': 'internal_error', 'message': 'No se pudo completar la solicitud.'}}, status=500)
    if isinstance(exc, ValidationError):
        error = {'code': 'invalid_input', 'message': 'La solicitud contiene datos inválidos.', 'fields': response.data}
    elif isinstance(exc, (ModelUnavailable, ModelBusy, PayloadTooLarge)):
        error = {'code': exc.default_code, 'message': str(exc.detail)}
    else:
        code, message = {
            400: ('invalid_json', 'El cuerpo debe ser JSON válido con codificación UTF-8.'),
            404: ('not_found', 'La ruta no existe.'),
            405: ('method_not_allowed', 'El método HTTP no está permitido en esta ruta.'),
            406: ('not_acceptable', 'La respuesta está disponible en formato JSON.'),
            415: ('unsupported_media_type', 'Usa Content-Type: application/json.'),
        }.get(response.status_code, ('request_error', 'No se pudo procesar la solicitud.'))
        error = {'code': code, 'message': message}
    response.data = {'error': error}
    if response.status_code == 503:
        response['Retry-After'] = '3'
    return response
