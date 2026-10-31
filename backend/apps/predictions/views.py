"""Predicción de estrellas mediante el mismo pipeline serializado."""

import time

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.serializers import (
    BatchPredictionSerializer,
    BatchReviewRequestSerializer,
    ErrorSerializer,
    PredictionSerializer,
    ReviewRequestSerializer,
    checked_output,
)
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


class BatchPredictView(APIView):
    @extend_schema(
        summary='Predecir estrellas para un lote de reseñas', tags=['Predicción'],
        request=BatchReviewRequestSerializer,
        responses={200: BatchPredictionSerializer, 400: ErrorSerializer, 413: ErrorSerializer, 415: ErrorSerializer, 500: ErrorSerializer, 503: ErrorSerializer},
        examples=[OpenApiExample('Lote sintético', value={'texts': ['Excelente producto, muy recomendado.', 'Pésimo servicio, llegó roto.']}, request_only=True)],
    )
    def post(self, request):
        entry = BatchReviewRequestSerializer(data=request.data)
        entry.is_valid(raise_exception=True)
        texts = entry.validated_data['texts']
        with model_service.inference() as predictor:
            started = time.perf_counter()
            raw_predictions = predictor.predict(texts)
            elapsed_ms = (time.perf_counter() - started) * 1000
            for item in raw_predictions:
                if item['model_id'] != predictor.manifest['model_id']:
                    raise RuntimeError('La predicción no corresponde al modelo activo.')
        predictions = [{**item, 'label': item['stars'] - 1, 'inference_ms': elapsed_ms / len(texts)} for item in raw_predictions]
        output = {
            'predictions': predictions,
            'count': len(predictions),
            'total_inference_ms': elapsed_ms,
        }
        return Response(checked_output(BatchPredictionSerializer, output))
