"""Predicción de estrellas mediante el mismo pipeline serializado."""

import time

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.serializers import ErrorSerializer, PredictionSerializer, ReviewRequestSerializer, checked_output
from backend.api.service import model_service


class PredictView(APIView):
    @extend_schema(
        summary='Predecir estrellas para una reseña', tags=['Predicción'],
        request=ReviewRequestSerializer,
        responses={200: PredictionSerializer, 400: ErrorSerializer, 413: ErrorSerializer, 415: ErrorSerializer, 500: ErrorSerializer, 503: ErrorSerializer},
        examples=[OpenApiExample('Reseña sintética', value={'text': 'El producto funciona, pero la entrega fue lenta.'}, request_only=True)],
    )
    def post(self, request):
        entry = ReviewRequestSerializer(data=request.data)
        entry.is_valid(raise_exception=True)
        with model_service.inference() as predictor:
            started = time.perf_counter()
            result = predictor.predict([entry.validated_data['text']])[0]
            elapsed_ms = (time.perf_counter() - started) * 1000
            if result['model_id'] != predictor.manifest['model_id']:
                raise RuntimeError('La predicción no corresponde al modelo activo.')
        result = {**result, 'label': result['stars'] - 1, 'inference_ms': elapsed_ms}
        return Response(checked_output(PredictionSerializer, result))
