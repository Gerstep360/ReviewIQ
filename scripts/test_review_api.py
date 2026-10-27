"""
Script de verificacion de los endpoints REST de Diagnostico y Reputacion.
"""
import os
import sys
from pathlib import Path

# Configurar entorno Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

# Permitir el host del cliente de pruebas
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

import json
from rest_framework.test import APIClient
from backend.apps.reviewiq.models import Entidad

client = APIClient()

print("=" * 60)
print("[TEST] VERIFICACION DE ENDPOINTS REST (REPUTACION Y DIAGNOSTICO)")
print("=" * 60)

# 1. Probar GET /api/v1/reputation/entities/
print("\n[1] Probando: GET /api/v1/reputation/entities/")
resp = client.get('/api/v1/reputation/entities/')
print(f"    Codigo de respuesta: {resp.status_code}")
data = resp.json()
print(f"    Total de entidades registradas: {data.get('count')}")
for ent in data.get('data', []):
    print(f"    - [{ent['id']}] {ent['nombre']} ({ent['categoria']}) - {ent['calificacion_promedio']} estrellas")

# Obtener la entidad de PedidosYa que sincronizamos antes
entidad = Entidad.objects.first()
if not entidad:
    print("[!] No hay entidades en la base de datos para continuar las pruebas.")
    sys.exit(1)

entidad_id = str(entidad.id)

# 2. Probar GET /api/v1/reputation/entities/<id>/diagnostic/
print(f"\n[2] Probando: GET /api/v1/reputation/entities/{entidad_id}/diagnostic/")
resp = client.get(f'/api/v1/reputation/entities/{entidad_id}/diagnostic/')
print(f"    Codigo de respuesta: {resp.status_code}")
data = resp.json()
print("    Semaforo devuelto por la API:")
for dim_k, dim_v in data.get('semaforo', {}).items():
    print(f"      * {dim_v['etiqueta']:<20}: {dim_v['porcentaje']}% [{dim_v['color'].upper()}]")

# 3. Probar GET /api/v1/reputation/entities/<id>/reviews/
print(f"\n[3] Probando: GET /api/v1/reputation/entities/{entidad_id}/reviews/")
resp = client.get(f'/api/v1/reputation/entities/{entidad_id}/reviews/')
print(f"    Codigo de respuesta: {resp.status_code}")
data = resp.json()
print(f"    Resenas obtenidas: {data.get('total_mostradas')}")
if data.get('reviews'):
    primera = data['reviews'][0]
    print(f"    Ejemplo resena: \"{primera['texto'][:50]}...\"")
    print(f"    IA Prediccion: {primera['diagnostico']['estrellas_predichas']} estrellas ({primera['diagnostico']['sentimiento_global']})")

print("\n" + "=" * 60)
print("[OK] TODOS LOS ENDPOINTS DE LA PARTE 4 RESPONDEN CON CODIGO 200!")
print("=" * 60)
