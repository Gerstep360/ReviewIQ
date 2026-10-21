# API REST — Fase F

La guía 06 se implementa con Django/DRF según ARQUITECTURA.md. Las vistas de predictions y analytics comparten backend/api/service.py y el Predictor de la Fase E. No se vuelve a ajustar NLP, TF-IDF ni el clasificador. No hay almacenamiento de reseñas ni modelos de base de datos en estas aplicaciones.

## Ejecutar en desarrollo

Desde la raíz, con Python 3.11:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py runapi 127.0.0.1:8000 --noreload --nothreading
```

El comando full verifica o genera el paquete como se explica en ARTEFACTOS.md; no repite test. runapi usa el servidor de desarrollo de Django y conserva sus comprobaciones de sistema y estáticos. Omite únicamente la comprobación de migraciones: estos endpoints no consultan PostgreSQL. El admin y futuras funciones con persistencia necesitan PostgreSQL, migraciones y el comando runserver habitual. runapi no prepara ni comprueba esas funciones.

Documentación interactiva: http://127.0.0.1:8000/docs/. Esquema JSON OpenAPI 3.0.3: http://127.0.0.1:8000/api/schema/. Swagger usa los recursos locales fijados de drf-spectacular-sidecar; no necesita CDN. Con DEBUG=False deberán servirse los estáticos recopilados mediante collectstatic.

Variables: REVIEWIQ_MODEL_DIR (por defecto ml/artifacts/full; rutas relativas desde la raíz), DJANGO_ALLOWED_HOSTS y DJANGO_CORS_ALLOWED_ORIGINS. .env.example es una referencia; hay que exportar sus valores en PowerShell. Para usar un paquete experimental:

```powershell
$env:REVIEWIQ_MODEL_DIR='ml/artifacts/quick'
```

El paquete debe existir antes de iniciar. WSGI/ASGI lo verifican y cargan una vez por proceso, con una predicción sintética de calentamiento. Si falla, el servidor continúa con health 503 y errores claros; no entrena, descarga ni intenta cargar en cada solicitud. Corregir el paquete exige reiniciar el proceso. Se mantiene un respaldo de inicialización única para clientes de prueba o aplicaciones embebidas.

## Rutas y respuestas

Las cuatro rutas admiten también su forma sin barra final, conservando método y cuerpo. El esquema documenta la forma canónica con barra.

| Método y ruta | Resultado |
|---|---|
| GET /api/v1/health/ | Estado del modelo cargado: status, model_loaded, model_id y mode |
| POST /api/v1/predict/ | Estrellas, clase interna, cinco probabilidades y duración real |
| GET /api/v1/metrics/ | Evidencia precalculada del modelo activo y comparación de validación |
| POST /api/v1/nlp/trace/ | Etapas reales del preprocesador y vectorizador guardados |

### Predicción

```powershell
$payload = @{ text = 'El producto funciona, pero la entrega fue lenta.' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/predict/ -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
```

El cuerpo es un objeto con un único campo text. Se conserva el texto de entrada, sin aplicar otra limpieza en el backend. Los campos de salida son:

| Campo | Regla |
|---|---|
| stars | Entero 1–5, clase de mayor probabilidad según classes_ del pipeline |
| label | Entero 0–4, stars - 1 |
| probabilities | Objeto con claves "1", "2", "3", "4", "5"; valores finitos en [0,1] y suma aproximadamente uno |
| model_id | Identidad del paquete activo |
| inference_ms | Tiempo de Predictor.predict en milisegundos; excluye espera de turno, validación, serialización y HTTP |
| experimental | true para quick, false para full |

Se validan tanto la entrada como la salida. Una salida que no respeta clases/probabilidades se trata como un error interno, sin entregar números inválidos. Las probabilidades son estimaciones del modelo, no certeza calibrada. Un ejemplo realmente calculado se conserva en reports/api_smoke.json; no se incluyen números simulados como resultados.

### Estado

Health 200 significa que el paquete se verificó y completó el calentamiento. No comprueba PostgreSQL. Cuando falta el paquete, es incompatible o está corrupto, responde 503 con status="unavailable", model_loaded=false, model_id=null y error público. Una cola ocupada puede rechazar inferencias aunque el modelo siga cargado.

### Métricas

La respuesta contiene model_id, mode, split, experimental, fecha de evaluación (null si no fue registrada en quick), fecha de empaquetado, fuente del dataset, configuración del pipeline activo, métricas globales, per_class y confusion_matrix. Las filas de la matriz representan estrellas reales y las columnas predichas, ambas en orden 1–5.

La sección principal procede exclusivamente del metrics.json verificado del paquete. Full muestra el test histórico del mismo estado aprendido; quick muestra validation experimental. No se ejecutan predicciones sobre el corpus al consultar este endpoint.

comparison incluye los finalistas precalculados de reports/model_comparison.json solo si es un informe full, tiene el mismo model_id del paquete y su split es validation. Así se distinguen métricas de selección de las finales. Es null para quick, cuando falta el informe o pertenece a otro modelo. No se publican las posiciones del análisis de errores en la sección principal.

### Traza NLP

Recibe el mismo cuerpo que predict. Ejecuta Predictor.trace: original, normalizado, tokens, stop words eliminadas, tokens restantes, raíces/lemas, texto procesado, n-gramas conocidos/desconocidos y versiones de las políticas. El método es el del artefacto activo; el request no cambia stop words ni morfología.

Cada lista se limita a 200 elementos y cada cadena a 12.000 caracteres. truncated indica si se recortó alguna salida y original_counts conserva los tamaños originales por campo. Son prefijos reales de las etapas, no un segundo procesamiento NLP. El límite solo afecta a la representación de la traza.

## Validaciones y errores

- text obligatorio y de tipo string; no se convierten números, booleanos ni listas.
- Entre 1 y 3.000 caracteres; rechaza blancos, null, Unicode inválido, caracteres nulos y campos adicionales.
- Solo JSON UTF-8; cuerpo completo limitado a 64 KiB antes de decodificarlo.
- Una inferencia por proceso; espera de turno máxima de dos segundos y 503 si se supera. El cálculo en curso no tiene cancelación forzada.

| HTTP | Código público | Significado |
|---|---|---|
| 400 | invalid_input | Entrada fuera del contrato; fields explica cada campo en español |
| 400 | invalid_json | JSON/codificación inválidos o anidación excesiva |
| 404 | not_found | Ruta API desconocida |
| 405 | method_not_allowed | Método incorrecto |
| 406 | not_acceptable | Se requiere una respuesta JSON |
| 413 | payload_too_large | Cuerpo superior a 64 KiB |
| 415 | unsupported_media_type | Content-Type no soportado |
| 500 | internal_error | Fallo interno o salida inválida; no expone stacktrace ni datos de la excepción |
| 503 | model_unavailable / model_busy | Modelo no disponible o espera de turno agotada; Retry-After: 3 |

Los errores usan {"error":{"code":"...","message":"..."}}; health 503 añade los campos de estado. El servicio es público, sin autenticación ni acceso a sesiones para estos endpoints. CORS permite por defecto http://localhost:5173 y http://127.0.0.1:5173, sin credenciales y limitado a /api/v1/. No usa origen comodín.

Las respuestas API llevan Cache-Control: no-store. El logger del módulo solo registra método, estado, duración y model_id; los errores registran su tipo, sin cuerpo, query string ni mensaje de excepción. No se guarda texto en archivos ni en PostgreSQL.

## Verificación y esquema versionado

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_api.py -v
.\venv\Scripts\python.exe scripts/check_api.py
.\venv\Scripts\python.exe manage.py spectacular --file docs/openapi.json --format openapi-json --validate --fail-on-warn
```

Las siete pruebas con fixture sintético no necesitan corpus ni binarios previos. La octava verifica el paquete real si está instalado y compara tres reseñas de validation (o frases sintéticas si faltan los datos) con el pipeline directo; nunca usa test ni escribe sus métricas. Django SimpleTestCase impide acceso accidental a la base de datos.

check_api crea su propio servidor en un puerto local libre, comprueba endpoints y recursos de Swagger, mide treinta llamadas pequeñas y cierra el proceso. No hay que dejar otro servidor abierto. Registra reports/api_smoke.json; no es una prueba de frontend ni de despliegue productivo. La ejecución real de esta fase se detalla en FASE-F-BACKEND.md y RENDIMIENTO.md.

Fuentes de implementación: [serializadores DRF](https://www.django-rest-framework.org/api-guide/serializers/), [errores DRF](https://www.django-rest-framework.org/api-guide/exceptions/), [OpenAPI con drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/customization.html) y [configuración de django-cors-headers](https://github.com/adamchainz/django-cors-headers#configuration). Pydantic/FastAPI de la guía original se adaptan a serializers/APIView de DRF; la API permanece en Django.
