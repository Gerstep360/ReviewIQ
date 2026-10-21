# 06 — Responsabilidad: backend REST con FastAPI

> Guía original conservada. La Fase F se implementó con Django/DRF según la arquitectura vigente. Contrato, comandos y límites reales: [API.md](../API.md). Evidencia: [FASE-F-BACKEND.md](../FASE-F-BACKEND.md). FastAPI/Pydantic/TestClient se adaptaron a APIView/serializers/APIClient; las rutas también aceptan barra final.

## Arquitectura interna

`api/main.py` registra FastAPI, `api/schemas.py` valida entradas/salidas, `api/services/predictor.py` carga el **pipeline completo** y `api/routes/` define endpoints. En lifespan startup cargar artefactos confiables y validar `manifest`/versiones, sin volver a entrenar ni reimplementar la limpieza de texto.

## Contratos mínimos

### `GET /api/v1/health`

Estado `200` cuando modelo está cargado y listo. JSON: `{"status":"ok", "model_loaded":true, "model_id":"..."}`. Si no hay artefactos, iniciar con mensaje claro o health 503 en entorno de desarrollo (decidir y documentar).

### `POST /api/v1/predict`

Entrada:

```json
{"text": "El sonido es bueno pero la batería apenas dura dos horas"}
```

Salida **esquema**, no resultado calculado:

```json
{
  "stars": 3,
  "label": 2,
  "probabilities": {"1": 0.08, "2": 0.18, "3": 0.42, "4": 0.25, "5": 0.07},
  "model_id": "reviewiq-...",
  "inference_ms": 12.4
}
```

**Todos esos números son simulados para definir el contrato y deben calcularse realmente.** `stars=argmax` de `predict_proba` según `classes_`, no usar posición del array a ciegas si cambian clases. Validar que las cinco probabilidades sean finitas, entre 0 y 1 y sumen ≈1. `inference_ms` medido; `probabilities` no equivale a certeza estadística calibrada.

### `GET /api/v1/metrics`

JSON precalculado y versionado (no recalcular test por cada petición): modelos comparados, métricas globales y por clase, configuración, matriz 5x5, split evaluado, `model_id` y fecha. Distinguir claramente **validation** de **test final**.

### `POST /api/v1/nlp/trace`

Entrada `{ "text": "..." }`. Devuelve **pasos reales** generados por los mismos objetos NLP serializados; tokens, stop words eliminadas, modo stem/lemma y n-gramas representativos. NO construir otro normalizador en la API. Limitar tamaño de la traza para no devolver millones de tokens.

### `POST /api/v1/predict/batch` (opcional)

CSV/JSON por lotes, máximo inicial 100 registros y tamaño máximo controlado; validar extensión, MIME, UTF-8, columnas y tamaño real en bytes; no guardar archivos por defecto.

## Seguridad, robustez, límites

- Rechazar blancos, solo espacios, tipos incorrectos, longitud superior al máximo, texto extremadamente largo, errores de encoding.
- Pydantic para request y response; respuestas 422 o 400 documentadas con mensajes en español.
- CORS restringido al host de la UI en desarrollo/producción; no `*` indiscriminado si hay credenciales.
- Sin persistencia de reseñas por defecto y sin registrar texto sensible en logs; limitar logging a duración, código de estado y versión del modelo.
- `joblib.load` solo de artefactos creados por nosotros; validar checksum manifest.
- Cargar pipeline una vez al iniciar, evitar recargarlo para cada petición.
- Timeout razonable, manejo de errores 500 sin filtrar stacktrace al cliente.
- OpenAPI disponible en `/docs`; docstrings y ejemplos válidos.

## Pruebas con TestClient/pytest

1. Health con artefacto válido/inválido.
2. Texto vacío/espacios/longitud excesiva/tipo incorrecto.
3. Salida 1–5 estrellas, cinco probabilidades y suma ≈1.
4. Caso de clase 0 mapeada a 1 estrella; clase 4 a 5.
5. API vs pipeline directo idéntico en muestra de validación.
6. Trace NLP vs mismo preprocesador; cambios de stop words **requieren** artefacto nuevo.
7. Métricas corresponden a `model_id` de artefacto activo; no mostrar métricas de otro entrenamiento.

## Aceptación, commits y prueba manual

- [ ] `GET /health`, `POST /predict` y `GET /metrics` cumplen enunciado.
- [ ] Validaciones y mensajes de error claros.
- [ ] Tests y documentación OpenAPI.
- [ ] Frontend usa REST real y no predicciones simuladas.

```bash
python -m uvicorn api.main:app --reload
python -m pytest tests/test_api.py -q
```

Commits:

- `feat(api): cargar pipeline y manifiesto al iniciar servidor`
- `feat(api): exponer prediccion multiclase y probabilidades por estrella`
- `feat(api): publicar metricas y estado del servicio`
- `feat(api): exponer traza nlp mediante preprocesador serializado`
- `test(api): validar inputs y consistencia de salida con modelo`
