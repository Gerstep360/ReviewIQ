"""Extractor de reseñas públicas de Google Play Store e integración con ReviewIQ."""

import logging
from datetime import datetime, timezone
from google_play_scraper import Sort, app as get_app_info, reviews

from backend.api.service import model_service
from backend.apps.reviewiq.dimensions import calcular_semaforo_entidad, puntuar_dimensiones
from backend.apps.reviewiq.models import ComentarioCrudo, DiagnosticoIQ, Entidad

logger = logging.getLogger('reviewiq.scraper')


def mapear_categoria_playstore(genre_id: str = None, genre: str = None, fallback: str = 'delivery') -> str:
    """Mapea el género oficial de Google Play Store a las categorías del frontend."""
    gid = (genre_id or '').upper()
    gname = (genre or '').lower()

    if gid.startswith('GAME_') or any(k in gname for k in ['juego', 'game', 'arcade', 'estrategia', 'casual', 'acción', 'accion', 'puzzle', 'rol', 'aventura']):
        return 'juegos'
    if gid in ('SHOPPING',) or any(k in gname for k in ['compra', 'shop']):
        return 'compras'
    if gid in ('FOOD_AND_DRINK',) or any(k in gname for k in ['comida', 'food', 'delivery', 'restauran']):
        return 'delivery'
    if gid in ('MAPS_AND_NAVIGATION', 'TRAVEL_AND_LOCAL', 'AUTO_AND_VEHICLES') or any(k in gname for k in ['transport', 'viaje', 'mapa', 'maps']):
        return 'transporte'
    if gid in ('FINANCE',) or any(k in gname for k in ['financ', 'banca', 'bank', 'money', 'pago']):
        return 'banca_finanzas'
    if gid in ('COMMUNICATION', 'SOCIAL') or any(k in gname for k in ['social', 'comunica', 'telecom', 'mensajer']):
        return 'telecom'
    return fallback


def sincronizar_app_playstore(
    package_id: str = None,
    nombre: str = None,
    categoria: str = 'delivery',
    cantidad: int = 20,
    pais: str = 'bo',
    icono_url: str = None,
    **kwargs
) -> dict:
    """Extrae reseñas de Google Play Store, las clasifica con ReviewIQ y las guarda en PostgreSQL."""
    # Soporte para app_id o package_id indistintamente
    package_id = package_id or kwargs.get('app_id')
    cantidad = cantidad or kwargs.get('cantidad_resenas', 20)
    if not package_id:
        raise ValueError("Se requiere 'package_id' o 'app_id'.")

    # Obtener metadatos oficiales de Google Play Store (icono oficial, nombre y categoría real)
    try:
        info = get_app_info(package_id, lang='es', country=pais)
        if not icono_url:
            icono_url = info.get('icon')
        if not nombre:
            nombre = info.get('title', package_id).split(' - ')[0]
        # Auto-inferir categoría desde Google Play si vino genérica o para verificar
        categoria_detectada = mapear_categoria_playstore(info.get('genreId'), info.get('genre'), fallback=categoria)
        if categoria_detectada:
            categoria = categoria_detectada
    except Exception as exc:
        logger.warning(f"No se pudo obtener metadatos de Play Store para {package_id}: {exc}")

    if not nombre:
        nombre = package_id

    # 1. Obtener o crear la Entidad en la base de datos (evita duplicados)
    entidad, created = Entidad.objects.get_or_create(
        tipo_fuente='play_store',
        identificador_externo=package_id,
        defaults={
            'nombre': nombre,
            'categoria': categoria,
            'tipo_entidad': 'app',
            'icono_url': icono_url
        }
    )
    cambios = False
    if icono_url and entidad.icono_url != icono_url:
        entidad.icono_url = icono_url
        cambios = True
    if categoria and entidad.categoria != categoria:
        entidad.categoria = categoria
        cambios = True
    if cambios:
        entidad.save()

    # 2. Descargar reseñas públicas de Google Play Store para Bolivia en español
    try:
        raw_reviews, _ = reviews(
            package_id,
            lang='es',
            country=pais,
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
    if total > 0:
        promedio_estrellas = sum(d.estrellas_predichas for d in todos_diagnosticos) / total
    else:
        promedio_estrellas = 0.0

    return {
        'entidad': entidad,
        'nuevos_comentarios': nuevos_comentarios,
        'total_procesadas': total,
        'calificacion_promedio': round(promedio_estrellas, 1),
        'semaforo': semaforo
    }
