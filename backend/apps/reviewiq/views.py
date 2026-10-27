"""
Vistas API REST para el módulo de Diagnóstico y Reputación Comercial.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Entidad, ComentarioCrudo, DiagnosticoIQ
from .dimensions import calcular_semaforo_entidad
from .scraper import sincronizar_app_playstore
from .serializers import (
    EntidadSerializer,
    ComentarioCrudoSerializer,
    SyncPlayStoreRequestSerializer,
)

DIMENSION_LABELS = {
    'atencion_cliente': 'Atención al Cliente',
    'envio_logistica': 'Envío y Logística',
    'calidad_producto': 'Calidad de Producto/Servicio',
    'precio_valor': 'Precio y Valor',
    'ux_bugs': 'Estabilidad y UX/Bugs',
}


class EntityListView(APIView):
    """
    GET /api/v1/reputation/entities/
    Devuelve la lista de entidades/apps registradas con opción de filtrar por categoría.
    """
    def get(self, request):
        categoria = request.query_params.get('categoria')
        queryset = Entidad.objects.all().order_by('-fecha_creacion')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        serializer = EntidadSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class EntityDiagnosticView(APIView):
    """
    GET /api/v1/reputation/entities/<uuid:entidad_id>/diagnostic/
    Devuelve el semáforo de 5 dimensiones calculado en tiempo real para una entidad.
    """
    def get(self, request, entidad_id):
        entidad = get_object_or_404(Entidad, pk=entidad_id)
        diagnosticos = DiagnosticoIQ.objects.filter(comentario__entidad=entidad)
        semaforo_raw = calcular_semaforo_entidad(diagnosticos)
        
        # Enriquecer semáforo con etiquetas legibles
        semaforo = {}
        for dim_k, dim_v in semaforo_raw.items():
            semaforo[dim_k] = {
                'etiqueta': DIMENSION_LABELS.get(dim_k, dim_k),
                'porcentaje': dim_v['score'],
                'color': dim_v['badge'],
                'menciones': dim_v['menciones'],
            }

        # Distribución de estrellas predichas por ReviewIQ
        distribucion = {str(i): 0 for i in range(1, 6)}
        for diag in diagnosticos:
            estrellas = str(diag.estrellas_predichas)
            distribucion[estrellas] = distribucion.get(estrellas, 0) + 1

        return Response({
            'status': 'success',
            'entidad': EntidadSerializer(entidad).data,
            'distribucion_estrellas_ia': distribucion,
            'semaforo': semaforo,
        }, status=status.HTTP_200_OK)


class EntityReviewsView(APIView):
    """
    GET /api/v1/reputation/entities/<uuid:entidad_id>/reviews/
    Lista las reseñas procesadas de una entidad, con filtros opcionales.
    """
    def get(self, request, entidad_id):
        entidad = get_object_or_404(Entidad, pk=entidad_id)
        queryset = entidad.comentarios.select_related('diagnostico').order_by('-fecha_captura')

        # Filtro por estrellas predichas (1..5)
        estrellas = request.query_params.get('estrellas')
        if estrellas and estrellas.isdigit():
            queryset = queryset.filter(diagnostico__estrellas_predichas=int(estrellas))

        # Filtro por sentimiento (positivo / neutro / negativo)
        sentimiento = request.query_params.get('sentimiento')
        if sentimiento:
            queryset = queryset.filter(diagnostico__sentimiento_global=sentimiento.lower())

        # Filtro por dimensión (ej: atencion_cliente)
        dimension = request.query_params.get('dimension')
        if dimension and dimension in DIMENSION_LABELS:
            campo = f'diagnostico__{dimension}_score'
            queryset = queryset.exclude(**{campo: 0.0})

        # Límite de reseñas (por defecto 50)
        try:
            limit = min(int(request.query_params.get('limit', 50)), 100)
        except ValueError:
            limit = 50

        queryset = queryset[:limit]
        serializer = ComentarioCrudoSerializer(queryset, many=True)

        return Response({
            'status': 'success',
            'total_mostradas': len(serializer.data),
            'reviews': serializer.data
        }, status=status.HTTP_200_OK)


class VersusComparisonView(APIView):
    """
    GET /api/v1/reputation/versus/?e1=<id1>&e2=<id2>
    Compara dos entidades cara a cara enfrentando sus semáforos de 5 dimensiones.
    """
    def get(self, request):
        e1_id = request.query_params.get('e1')
        e2_id = request.query_params.get('e2')

        if not e1_id or not e2_id:
            return Response({
                'status': 'error',
                'message': 'Debes enviar los parámetros e1 y e2 con los IDs de las entidades a comparar.'
            }, status=status.HTTP_400_BAD_REQUEST)

        entidad1 = get_object_or_404(Entidad, pk=e1_id)
        entidad2 = get_object_or_404(Entidad, pk=e2_id)

        diag1 = DiagnosticoIQ.objects.filter(comentario__entidad=entidad1)
        diag2 = DiagnosticoIQ.objects.filter(comentario__entidad=entidad2)

        sem1 = calcular_semaforo_entidad(diag1)
        sem2 = calcular_semaforo_entidad(diag2)

        comparativa = {}
        for dim_key, dim_label in DIMENSION_LABELS.items():
            pct1 = sem1[dim_key]['score']
            pct2 = sem2[dim_key]['score']

            if pct1 > pct2:
                ganador = entidad1.nombre
            elif pct2 > pct1:
                ganador = entidad2.nombre
            else:
                ganador = 'Empate'

            comparativa[dim_key] = {
                'dimension': dim_label,
                'entidad1': {'nombre': entidad1.nombre, 'porcentaje': pct1, 'color': sem1[dim_key]['badge']},
                'entidad2': {'nombre': entidad2.nombre, 'porcentaje': pct2, 'color': sem2[dim_key]['badge']},
                'ganador': ganador,
            }

        return Response({
            'status': 'success',
            'entidad1': EntidadSerializer(entidad1).data,
            'entidad2': EntidadSerializer(entidad2).data,
            'comparativa_dimensiones': comparativa,
        }, status=status.HTTP_200_OK)


class SyncPlayStoreView(APIView):
    """
    POST /api/v1/reputation/sync/playstore/
    Dispara la sincronización en tiempo real de una aplicación de Google Play Store.
    """
    def post(self, request):
        serializer = SyncPlayStoreRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        try:
            resultado = sincronizar_app_playstore(
                app_id=datos['app_id'],
                nombre=datos.get('nombre') or None,
                categoria=datos.get('categoria', 'delivery'),
                pais=datos.get('pais', 'bo'),
                cantidad_resenas=datos.get('cantidad', 20),
            )
            return Response({
                'status': 'success',
                'message': f"Se sincronizaron exitosamente las reseñas de '{resultado['entidad'].nombre}'.",
                'entidad': EntidadSerializer(resultado['entidad']).data,
                'total_procesadas': resultado['total_procesadas'],
                'calificacion_promedio': resultado['calificacion_promedio'],
                'semaforo': resultado['semaforo'],
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f"Error al sincronizar con Google Play Store: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
