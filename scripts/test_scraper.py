"""Script de prueba para verificar el scraper de Google Play y la persistencia en PostgreSQL."""

import os
import sys
from pathlib import Path

# Agregar la raíz del proyecto para que encuentre la carpeta 'backend'
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.apps.reviewiq.scraper import sincronizar_app_playstore
from backend.apps.reviewiq.models import ComentarioCrudo

def main():
    print("=" * 60)
    print("🚀 Iniciando prueba del Extractor de Google Play Store...")
    print("📲 Descargando 5 reseñas reales de PedidosYa (Bolivia)...")
    print("=" * 60)

    # Llamamos a nuestra función para sincronizar 5 reseñas
    resultado = sincronizar_app_playstore(
        package_id='com.pedidosya',
        nombre='PedidosYa',
        categoria='delivery',
        cantidad=5
    )

    print("\n✅ ¡Sincronización completada con éxito!")
    print(f"🏢 Entidad: {resultado['nombre']} (ID: {resultado['entidad_id']})")
    print(f"📊 Total reseñas procesadas: {resultado['nuevos_procesados']}")
    print(f"⭐ Calificación promedio calculada: {resultado['estrellas_promedio']} estrellas\n")

    print("🚦 SEMÁFORO DE EXPERIENCIA (Calculado en tiempo real):")
    for dim, info in resultado['semaforo'].items():
        color_emoji = "🟢" if info['badge'] == "verde" else ("🟡" if info['badge'] == "amarillo" else "🔴")
        print(f"  {color_emoji} {dim.replace('_', ' ').title():<22}: {info['score']}% [{info['badge'].upper()}] ({info['menciones']} menciones)")

    print("\n📝 RESEÑAS GUARDADAS EN POSTGRESQL:")
    ultimos = ComentarioCrudo.objects.filter(entidad__identificador_externo='com.pedidosya').order_by('-fecha_captura')[:5]
    for idx, c in enumerate(ultimos, 1):
        diag = c.diagnostico
        print(f"\n[{idx}] Reseña original ({c.estrellas_origen}★ en Play Store):")
        print(f"    \"{c.texto[:100]}...\"")
        print(f"    🤖 ReviewIQ predijo: {diag.estrellas_predichas}★ (Sentimiento: {diag.sentimiento_global}, Confianza: {round(diag.probabilidad_mayor * 100, 1)}%)")

    print("\n" + "=" * 60)
    print("🎉 ¡Parte 3 probada y verificada de punta a punta!")
    print("=" * 60)

if __name__ == '__main__':
    main()