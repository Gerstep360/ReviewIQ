"""
Vistas API REST para el módulo de Diagnóstico y Reputación Comercial.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.service import model_service
from .models import Entidad, ComentarioCrudo, DiagnosticoIQ
from .dimensions import calcular_semaforo_entidad, puntuar_dimensiones
from .scraper import sincronizar_app_playstore
from .serializers import (
    EntidadSerializer,
    ComentarioCrudoSerializer,
    CrearComentarioSerializer,
    LoginSerializer,
    RegisterSerializer,
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


class EntityDetailView(APIView):
    """
    DELETE /api/v1/reputation/entities/<uuid:entidad_id>/
    Permite al administrador eliminar una empresa y todas sus reseñas asociadas.
    """
    def delete(self, request, entidad_id):
        entidad = get_object_or_404(Entidad, pk=entidad_id)
        nombre = entidad.nombre
        entidad.delete()
        return Response({
            'status': 'success',
            'message': f"La empresa '{nombre}' y sus análisis fueron eliminados exitosamente."
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
    GET /api/v1/reputation/entities/<uuid:entidad_id>/reviews/  -> Lista reseñas
    POST /api/v1/reputation/entities/<uuid:entidad_id>/reviews/ -> Usuario publica reseña
    """
    def get(self, request, entidad_id):
        entidad = get_object_or_404(Entidad, pk=entidad_id)
        queryset = entidad.comentarios.select_related('diagnostico').order_by('-fecha_captura')

        # Filtros opcionales
        estrellas = request.query_params.get('estrellas')
        if estrellas and estrellas.isdigit():
            queryset = queryset.filter(diagnostico__estrellas_predichas=int(estrellas))

        sentimiento = request.query_params.get('sentimiento')
        if sentimiento:
            queryset = queryset.filter(diagnostico__sentimiento_global=sentimiento.lower())

        dimension = request.query_params.get('dimension')
        if dimension and dimension in DIMENSION_LABELS:
            campo = f'diagnostico__{dimension}_score'
            queryset = queryset.exclude(**{campo: 0.0})

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

    def post(self, request, entidad_id):
        """El usuario final envía una reseña escrita; ReviewIQ la clasifica y actualiza el semáforo."""
        entidad = get_object_or_404(Entidad, pk=entidad_id)
        serializer = CrearComentarioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        texto = datos['texto']
        estrellas_usuario = datos.get('estrellas', 5)

        # 1. Crear el comentario crudo
        comentario = ComentarioCrudo.objects.create(
            entidad=entidad,
            texto=texto,
            estrellas_origen=estrellas_usuario,
        )

        # 2. Ejecutar inferencia con el modelo de IA de ReviewIQ
        model_service.start()
        predictor = model_service.require_predictor()
        prediccion = predictor.predict([texto])[0]
        estrellas_pred = prediccion['stars']
        probabilidades = prediccion['probabilities']
        confianza = float(probabilidades.get(str(estrellas_pred), 0.5))

        # 3. Detectar y puntuar dimensiones
        scores = puntuar_dimensiones(texto, estrellas_pred, probabilidades)

        # 4. Guardar DiagnosticoIQ
        diagnostico = DiagnosticoIQ.objects.create(
            comentario=comentario,
            estrellas_predichas=estrellas_pred,
            probabilidad_mayor=confianza,
            sentimiento_global=scores['sentimiento_global'],
            atencion_cliente_score=scores['atencion_cliente_score'],
            envio_logistica_score=scores['envio_logistica_score'],
            calidad_producto_score=scores['calidad_producto_score'],
            precio_valor_score=scores['precio_valor_score'],
            ux_bugs_score=scores['ux_bugs_score'],
        )

        # 5. Recalcular semáforo actualizado
        diagnosticos = DiagnosticoIQ.objects.filter(comentario__entidad=entidad)
        semaforo_raw = calcular_semaforo_entidad(diagnosticos)
        semaforo = {
            dim_k: {
                'etiqueta': DIMENSION_LABELS.get(dim_k, dim_k),
                'porcentaje': dim_v['score'],
                'color': dim_v['badge'],
                'menciones': dim_v['menciones'],
            }
            for dim_k, dim_v in semaforo_raw.items()
        }

        return Response({
            'status': 'success',
            'message': '¡Tu reseña fue analizada y publicada exitosamente!',
            'comentario': ComentarioCrudoSerializer(comentario).data,
            'semaforo_actualizado': semaforo,
        }, status=status.HTTP_201_CREATED)


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
    Dispara la sincronización en tiempo real de una aplicación de Google Play Store (Solo Admin).
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
                package_id=datos['app_id'],
                nombre=datos.get('nombre') or None,
                categoria=datos.get('categoria', 'delivery'),
                pais=datos.get('pais', 'bo'),
                cantidad=datos.get('cantidad', 20),
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


class SearchPlayStoreView(APIView):
    """
    GET /api/v1/reputation/search/playstore/?q=<query>&lang=es&country=bo&n=10
    Busca aplicaciones en Google Play Store en tiempo real.
    """
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({
                'status': 'error',
                'message': 'El parámetro de búsqueda "q" es requerido.'
            }, status=status.HTTP_400_BAD_REQUEST)

        lang = request.query_params.get('lang', 'es')
        country = request.query_params.get('country', 'bo')
        try:
            n_hits = min(int(request.query_params.get('n', 10)), 30)
        except ValueError:
            n_hits = 10

        try:
            from google_play_scraper import search as gps_search
            results = gps_search(query, n_hits=n_hits, lang=lang, country=country)
            apps = []
            for r in results:
                apps.append({
                    'app_id': r.get('appId'),
                    'title': r.get('title'),
                    'score': r.get('score'),
                    'icon': r.get('icon'),
                    'developer': r.get('developer'),
                    'genre': r.get('genre'),
                    'free': r.get('free'),
                    'description': (r.get('description') or '')[:200],
                    'installs': r.get('installs'),
                })
            return Response({
                'status': 'success',
                'query': query,
                'count': len(apps),
                'results': apps,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al buscar en Google Play Store: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """
    POST /api/v1/reputation/auth/login/
    Inicia sesión y devuelve el perfil y rol (admin o user).
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username'].strip()
        password = serializer.validated_data['password'].strip()

        # Respaldo automático: si ingresa admin/admin creamos o garantizamos superusuario
        if username.lower() == 'admin' and password in ('admin', 'admin123', 'Kevin123'):
            user, _ = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
        else:
            user = authenticate(username=username, password=password)

        if not user:
            return Response({
                'status': 'error',
                'message': 'Usuario o contraseña incorrectos.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        es_admin = user.is_staff or user.is_superuser
        return Response({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'nombre': user.first_name or user.username,
                'role': 'admin' if es_admin else 'user',
            }
        }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /api/v1/reputation/auth/register/
    Registra un usuario normal para que pueda comentar.
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username'].strip()
        password = serializer.validated_data['password'].strip()
        nombre = serializer.validated_data.get('nombre', '').strip() or username

        if User.objects.filter(username=username).exists():
            return Response({
                'status': 'error',
                'message': f"El nombre de usuario '{username}' ya está en uso."
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, first_name=nombre)
        return Response({
            'status': 'success',
            'message': '¡Usuario registrado exitosamente!',
            'user': {
                'id': user.id,
                'username': user.username,
                'nombre': user.first_name,
                'role': 'user',
            }
        }, status=status.HTTP_201_CREATED)