from django.urls import re_path
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from backend.apps.analytics.views import HealthView, MetricsView, TraceView
from backend.apps.predictions.views import PredictView

app_name = 'api'


@extend_schema(exclude=True)
class UnknownRouteView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        raise NotFound()


urlpatterns = [
    re_path(r'^health/?$', HealthView.as_view(), name='health'),
    re_path(r'^predict/?$', PredictView.as_view(), name='predict'),
    re_path(r'^metrics/?$', MetricsView.as_view(), name='metrics'),
    re_path(r'^nlp/trace/?$', TraceView.as_view(), name='nlp-trace'),
    re_path(r'^.*$', UnknownRouteView.as_view()),
]
