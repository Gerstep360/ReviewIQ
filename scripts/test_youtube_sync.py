"""Script de prueba para verificar la extracción y análisis de comentarios de YouTube con ReviewIQ."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
os.environ.setdefault('USE_SQLITE', '1')

import django
django.setup()

from backend.apps.reviewiq.models import Entidad, ComentarioCrudo
from backend.apps.reviewiq.youtube_scraper import sincronizar_app_youtube


def main():
    print("=" * 65)
    print("🚀 PROBANDO EXTRACTOR Y ANÁLISIS DE RESEÑAS DE YOUTUBE")
    print("=" * 65)

    # 1. Asegurar o crear una entidad para pruebas
    entidad, _ = Entidad.objects.get_or_create(
        identificador_externo='com.pedidosya.bo',
        defaults={
            'nombre': 'PedidosYa Bolivia',
            'categoria': 'delivery',
            'tipo_entidad': 'app',
            'tipo_fuente': 'play_store',
        }
    )
    print(f"🏢 Entidad objetivo: {entidad.nombre} (ID: {entidad.id})")

    # 2. Sincronizar un video de YouTube
    video_test = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"📲 Analizando video de YouTube: {video_test}")
    print("⏳ Descargando comentarios y ejecutando inferencia con ReviewIQ...\n")

    resultado = sincronizar_app_youtube(
        package_id_o_entidad_id=str(entidad.id),
        video_url=video_test,
        cantidad=5
    )

    print("✅ ¡Sincronización completada exitosamente!")
    print(f"📊 Nuevos comentarios analizados: {resultado['nuevos_comentarios']}")
    print(f"📈 Total de opiniones acumuladas: {resultado['total_procesadas']}")
    print(f"⭐ Calificación promedio global (IA): {resultado['calificacion_promedio']} estrellas\n")

    print("🚦 SEMÁFORO DE EXPERIENCIA ACTUALIZADO:")
    for dim, info in resultado['semaforo'].items():
        emoji = "🟢" if info['badge'] == "verde" else ("🟡" if info['badge'] == "amarillo" else "🔴")
        print(f"  {emoji} {dim.replace('_', ' ').title():<24}: {info['score']}% [{info['badge'].upper()}] ({info['menciones']} menciones)")

    print("\n📝 COMENTARIOS DE YOUTUBE GUARDADOS EN BD CON INFERENCIA DE IA:")
    ultimos = ComentarioCrudo.objects.filter(entidad=entidad, fuente='youtube').order_by('-fecha_captura')[:4]
    for idx, c in enumerate(ultimos, 1):
        diag = c.diagnostico
        print(f"\n[{idx}] Autor: {c.autor or 'Anónimo'} (Fuente: {c.fuente})")
        print(f"    Texto: \"{c.texto}\"")
        if diag:
            print(f"    🤖 ReviewIQ predijo: {diag.estrellas_predichas}★ (Sentimiento: {diag.sentimiento_global.upper()}, Confianza: {round(diag.probabilidad_mayor * 100, 1)}%)")

    print("\n" + "=" * 65)


if __name__ == '__main__':
    main()

