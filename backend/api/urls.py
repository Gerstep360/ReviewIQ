from django.urls import path, re_path
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from backend.apps.analytics.views import HealthView, MetricsView, TraceView
from backend.apps.predictions.views import BatchPredictView, PredictView
from backend.apps.reviewiq.views import (
    EntityListView,
    EntityDiagnosticView,
    EntityReviewsView,
    VersusComparisonView,
    SyncPlayStoreView,
)

app_name = 'api'


@extend_schema(exclude=True)
class UnknownRouteView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        raise NotFound()


urlpatterns = [
    # Rutas originales de prediccion y analitica
    re_path(r'^health/?$', HealthView.as_view(), name='health'),
    re_path(r'^predict/batch/?$', BatchPredictView.as_view(), name='predict-batch'),
    re_path(r'^predict/?$', PredictView.as_view(), name='predict'),
    re_path(r'^metrics/?$', MetricsView.as_view(), name='metrics'),
    re_path(r'^nlp/trace/?$', TraceView.as_view(), name='nlp-trace'),

    # Rutas del modulo de Diagnostico y Reputacion (ReviewIQ)
    path('reputation/entities/', EntityListView.as_view(), name='reputation-entities'),
    path('reputation/entities/<uuid:entidad_id>/diagnostic/', EntityDiagnosticView.as_view(), name='reputation-diagnostic'),
    path('reputation/entities/<uuid:entidad_id>/reviews/', EntityReviewsView.as_view(), name='reputation-reviews'),
    path('reputation/versus/', VersusComparisonView.as_view(), name='reputation-versus'),
    path('reputation/sync/playstore/', SyncPlayStoreView.as_view(), name='reputation-sync-playstore'),

    # Captura de rutas desconocidas (siempre debe ir al final)
    re_path(r'^.*$', UnknownRouteView.as_view()),
]
