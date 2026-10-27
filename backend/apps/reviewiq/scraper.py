"""Extractor de reseñas públicas de Google Play Store e integración con ReviewIQ."""

import logging
from datetime import datetime, timezone
from google_play_scraper import Sort, reviews

from backend.api.service import model_service
from backend.apps.reviewiq.dimensions import calcular_semaforo_entidad, puntuar_dimensiones
from backend.apps.reviewiq.models import ComentarioCrudo, DiagnosticoIQ, Entidad

logger = logging.getLogger('reviewiq.scraper')


def sincronizar_app_playstore(
    package_id: str,
    nombre: str,
    categoria: str,
    cantidad: int = 20,
    icono_url: str = None
) -> dict:
    """Extrae reseñas de Google Play Store, las clasifica con ReviewIQ y las guarda en PostgreSQL.
    
    Args:
        package_id: ID de la app en Play Store (ej: 'com.pedidosya')
        nombre: Nombre visible de la app (ej: 'PedidosYa')
        categoria: Rubro (ej: 'delivery', 'banca_finanzas')
        cantidad: Número de reseñas a descargar (por defecto 20)
    """
    # 1. Obtener o crear la Entidad en la base de datos (evita duplicados)
    entidad, _ = Entidad.objects.get_or_create(
        tipo_fuente='play_store',
        identificador_externo=package_id,
        defaults={
            'nombre': nombre,
            'categoria': categoria,
            'tipo_entidad': 'app',
            'icono_url': icono_url
        }
    )

    # 2. Descargar reseñas públicas de Google Play Store para Bolivia en español
    try:
        raw_reviews, _ = reviews(
            package_id,
            lang='es',
            country='bo',
            sort=Sort.NEWEST,
            count=cantidad
        )
    except Exception as exc:
        raise RuntimeError(f'Error al conectar con Google Play Store para {package_id}: {exc}')

    nuevos_comentarios = 0
    model_service.start()
    predictor = model_service.require_predictor()

    # 3. Procesar cada comentario y persistir en PostgreSQL
    for item in raw_reviews:
        texto = (item.get('content') or '').strip()
        if not texto:
            continue

        fecha_pub = item.get('at')
        if fecha_pub and fecha_pub.tzinfo is None:
            fecha_pub = fecha_pub.replace(tzinfo=timezone.utc)

        # Evitar guardar el mismo comentario si ya se había descargado antes
        comentario, creado = ComentarioCrudo.objects.get_or_create(
            entidad=entidad,
            texto=texto,
            defaults={
                'estrellas_origen': int(item.get('score', 3)),
                'fecha_publicacion': fecha_pub,
            }
        )

        if not creado and hasattr(comentario, 'diagnostico'):
            # Si ya existía y ya tiene diagnóstico, no repetimos el cálculo
            continue

        # 4. Inferencia con ReviewIQ (Predice estrellas y probabilidades)
        prediccion = predictor.predict([texto])[0]
        estrellas = prediccion['stars']
        probabilidades = prediccion['probabilities']
        confianza = float(probabilidades.get(str(estrellas), 0.5))

        # 5. Motor de dimensiones (Calcula el impacto en las 5 dimensiones)
        scores_dimensiones = puntuar_dimensiones(texto, estrellas, probabilidades)

        # 6. Guardar el Diagnóstico en PostgreSQL
        DiagnosticoIQ.objects.update_or_create(
            comentario=comentario,
            defaults={
                'estrellas_predichas': estrellas,
                'probabilidad_mayor': confianza,
                'sentimiento_global': scores_dimensiones['sentimiento_global'],
                'atencion_cliente_score': scores_dimensiones['atencion_cliente_score'],
                'envio_logistica_score': scores_dimensiones['envio_logistica_score'],
                'calidad_producto_score': scores_dimensiones['calidad_producto_score'],
                'precio_valor_score': scores_dimensiones['precio_valor_score'],
                'ux_bugs_score': scores_dimensiones['ux_bugs_score'],
            }
        )
        nuevos_comentarios += 1

    # 7. Calcular el Semáforo actualizado de la entidad con todos sus diagnósticos
    todos_diagnosticos = DiagnosticoIQ.objects.filter(comentario__entidad=entidad)
    semaforo = calcular_semaforo_entidad(todos_diagnosticos)
    
    total = todos_diagnosticos.count()
    promedio_estrellas = (
        round(sum(d.estrellas_predichas for d in todos_diagnosticos) / total, 1)
        if total > 0 else 0.0
    )

    return {
        'entidad_id': str(entidad.id),
        'nombre': entidad.nombre,
        'nuevos_procesados': nuevos_comentarios,
        'total_comentarios': total,
        'estrellas_promedio': promedio_estrellas,
        'semaforo': semaforo
    }