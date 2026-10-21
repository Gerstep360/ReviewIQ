# Fase F — Backend Django/DRF

Implementada según la guía 06, adaptada a la arquitectura vigente. Se exponen predicción, métricas, estado y traza NLP con el pipeline serializado de la Fase E. La siguiente fase es G: frontend React conectado a esta API.

## Archivos y decisiones

- backend/apps/predictions/views.py: POST predict y validación de la respuesta.
- backend/apps/analytics/views.py: health, métricas guardadas y traza limitada.
- backend/api/: serializers, errores JSON en español, parser con límite real de lectura, URLs, servicio de carga única y logs de metadatos.
- backend/wsgi.py y asgi.py: carga verificada y calentamiento al iniciar; el proceso queda disponible con 503 si no puede cargar el modelo.
- backend/settings.py y .env.example: DRF, paquete seleccionable, CORS restringido y límites de entrada/concurrencia.
- Comando runapi: servidor de desarrollo Django que omite solo el chequeo de migraciones para la API sin persistencia. PostgreSQL se conserva como base operativa; no se modificó a SQLite.
- requirements.in/txt y requirements-dev.txt: DRF 3.18.3, drf-spectacular 0.30.0, sidecar 2026.10.1 y django-cors-headers 4.9.0, con transitivas fijadas. Se conservaron las versiones anteriores de ML.
- tests/test_api.py: ocho pruebas enfocadas. scripts/check_api.py: smoke por HTTP real y medición pequeña reproducible.
- docs/API.md y docs/openapi.json: contrato vigente y esquema generado/validado. reports/api_smoke.json: evidencia medida.

No se implementó historial, batch opcional ni frontend. No hay modelos ni migraciones nuevos porque las reseñas no se persisten. No se entrenó ningún modelo ni se repitió test.

## Comandos y resultados reales

```text
venv/Scripts/python.exe -m pip install -r requirements.txt
  Successfully installed django-cors-headers-4.9.0 djangorestframework-3.18.3
  drf-spectacular-0.30.0 drf-spectacular-sidecar-2026.10.1
  inflection-0.5.1 pyyaml-6.0.3 uritemplate-4.2.0

venv/Scripts/python.exe manage.py check
  System check identified no issues (0 silenced).

venv/Scripts/python.exe -m pip check
  No broken requirements found.

venv/Scripts/python.exe -m unittest discover -s tests -p test_api.py -v
  Ran 8 tests in 1.657s
  OK

venv/Scripts/python.exe manage.py spectacular --file docs/openapi.json --format openapi-json --validate --fail-on-warn
  Exit code: 0, sin advertencias ni errores de validación.

venv/Scripts/python.exe scripts/check_api.py
  model_id: reviewiq-8f0ef24251ae5522
  endpoints: OK
  http_roundtrip p50_ms: 22.652899962849915
  http_roundtrip p95_ms: 31.84468498511706
```

Los locks se generaron con piptools compile; primero se usó el lock previo como restricción para preservar el entorno del modelo y luego se regeneraron las anotaciones contra requirements.in. El lock de desarrollo se compiló con --constraint requirements.txt. Los comandos habituales de actualización están en README.md.

## Qué se comprobó

Siete pruebas usan un paquete sintético temporal: carga única, ausencia de fit/red durante solicitudes, salud con artefacto ausente/corrupto, entradas y errores de tamaño/codificación, etiquetas extremas 0→1 y 4→5, probabilidades válidas, 500 sin mensajes privados, espera de turno, traza compartida/recortada, métricas ligadas al paquete, exclusión de comparaciones ajenas, CORS, OpenAPI y rutas con/sin barra. La octava cargó el campeón real y comprobó tres reseñas de validation contra predict_proba directo, con fit y red bloqueados. No hubo acceso a base de datos.

Las primeras pruebas detectaron que el límite de cuerpo se convertía en 500 al atravesar DRF; se corrigió a 413 con un parser acotado y el manejador de excepciones. La ejecución final anterior pasó completa. Las rutas API desconocidas devuelven 404 JSON incluso en desarrollo.

El smoke inició WSGI mediante runapi en loopback, sin PostgreSQL y sin autoreload/hilos de solicitudes. Verificó los cuatro endpoints, el esquema, /docs/ y cuatro recursos locales de Swagger, además de una entrada rechazada con 400. Todas las respuestas válidas usaron el mismo model_id y las métricas finales ya guardadas. El script terminó su propio servidor.

## Rendimiento y límites

Treinta llamadas HTTP individuales tras tres de calentamiento: p50 22,65 ms y p95 31,84 ms. La duración de inferencia informada por la API tuvo p50 7,30 ms y p95 10,16 ms. El arranque hasta health listo tomó 4,21 s; RSS listo 264,38 MiB y máximo observado tras solicitudes 264,62 MiB. Equipo, alcance y valores completos: reports/api_smoke.json.

Es el servidor de desarrollo, con textos sintéticos y una sola solicitud a la vez; no representa concurrencia o despliegue productivo. RSS se observó en fronteras de solicitudes, sin medir continuamente el pico. El límite de dos segundos es de espera de turno, no una cancelación del cálculo activo. API.md documenta los límites de entrada y las condiciones de PostgreSQL/estáticos.

Quedan para G la interfaz conectada y sus estados de error; H cubrirá integración completa, despliegue/operación y verificación final. La asistencia de Codex en esta implementación y sus verificaciones está declarada en CONTRIBUCIONES.md e INFORME-TECNICO.md.

Commit del bloque: feat(api): servir predicciones metricas y trazas con pipeline verificado.
