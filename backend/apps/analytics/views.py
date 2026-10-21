"""Estado y evidencia precalculada; traza de los objetos NLP del paquete."""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.exceptions import ModelUnavailable
from backend.api.serializers import ErrorSerializer, HealthSerializer, MetricsSerializer, ReviewRequestSerializer, TraceSerializer, UnavailableHealthSerializer, checked_output
from backend.api.service import model_service


class HealthView(APIView):
    @extend_schema(summary='Comprobar modelo listo para inferencia', tags=['Estado'], responses={200: HealthSerializer, 503: UnavailableHealthSerializer})
    def get(self, request):
        try:
            predictor = model_service.require_predictor()
        except ModelUnavailable as exc:
            return Response({'status': 'unavailable', 'model_loaded': False, 'model_id': None, 'error': {'code': exc.default_code, 'message': str(exc.detail)}}, status=503, headers={'Retry-After': '3'})
        return Response(checked_output(HealthSerializer, {'status': 'ok', 'model_loaded': True, 'model_id': predictor.manifest['model_id'], 'mode': predictor.manifest['mode']}))


class MetricsView(APIView):
    @extend_schema(summary='Consultar métricas guardadas del modelo activo', tags=['Métricas'], responses={200: MetricsSerializer, 500: ErrorSerializer, 503: ErrorSerializer})
    def get(self, request):
        return Response(checked_output(MetricsSerializer, model_service.metrics()))


class TraceView(APIView):
    @extend_schema(
        summary='Inspeccionar los pasos reales del preprocesador guardado', tags=['NLP'],
        description='Cada lista se limita a 200 elementos y cada cadena a 12000 caracteres. Se informan truncamiento y longitudes originales.',
        request=ReviewRequestSerializer,
        responses={200: TraceSerializer, 400: ErrorSerializer, 413: ErrorSerializer, 415: ErrorSerializer, 500: ErrorSerializer, 503: ErrorSerializer},
    )
    def post(self, request):
        entry = ReviewRequestSerializer(data=request.data)
        entry.is_valid(raise_exception=True)
        with model_service.inference() as predictor:
            trace = predictor.trace(entry.validated_data['text'])
        counts, truncated = {}, False
        for key, value in trace.items():
            if isinstance(value, list):
                counts[key] = len(value)
                trace[key] = value[:settings.REVIEWIQ_TRACE_MAX_ITEMS]
                truncated |= len(value) > settings.REVIEWIQ_TRACE_MAX_ITEMS
            elif isinstance(value, str):
                counts[key] = len(value)
                trace[key] = value[:settings.REVIEWIQ_TRACE_MAX_CHARACTERS]
                truncated |= len(value) > settings.REVIEWIQ_TRACE_MAX_CHARACTERS
        trace.update({'truncated': truncated, 'original_counts': counts, 'limits': {'items_per_list': settings.REVIEWIQ_TRACE_MAX_ITEMS, 'characters_per_string': settings.REVIEWIQ_TRACE_MAX_CHARACTERS}})
        return Response(checked_output(TraceSerializer, trace))
