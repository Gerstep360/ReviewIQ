# ReviewIQ — Arquitectura de archivos y responsabilidades

> **Documento técnico de implementación**  
> Proyecto integrador de **Tópicos y Programación Avanzada**  
> Versión de arquitectura: 1.0 — 21 de octubre de 2026  
> Estado: **propuesta para organizar el repositorio existente**; no implica que todos los archivos ya estén implementados.

---

## 1. Objetivo y alcance

**ReviewIQ** es una aplicación web que recibe reseñas comerciales en español y **predice una calificación de 1 a 5 estrellas** mediante un clasificador no generativo. También muestra probabilidades por clase, el procesamiento de NLP y resultados de evaluación. El propósito es ofrecer una demostración académica de análisis de satisfacción comercial, no afirmar que las predicciones son opiniones reales de clientes.

El proyecto debe cumplir las cinco capas exigidas por el documento del docente: **datos, pipeline NLP, modelos ML, API REST y frontend**. Debe permitir reproducir el entrenamiento, comparar dos modelos, documentar decisiones, examinar errores y modificar el sistema en vivo.

**Tecnologías elegidas:**

| Capa | Herramienta | Responsabilidad |
|---|---|---|
| Lenguaje del servidor y ML | Python 3.11 | Django, NLP y entrenamiento |
| Backend único | Django | Configuración, historial, validación y aplicación |
| API REST | Django REST Framework (DRF) | Única API pública, usada por React |
| Frontend | React + TypeScript + Vite | Interfaz y consumo de API |
| Estilos | Tailwind CSS | UI adaptable a escritorio y móvil |
| Visualización | Recharts | Gráficos de métricas y predicciones |
| NLP | NLTK + spaCy | Stop words, stemming, lematización y tokenización |
| ML | scikit-learn | TF-IDF, regresión logística y Multinomial Naive Bayes |
| Datos y análisis | Hugging Face Datasets, pandas, NumPy, matplotlib | Obtención, limpieza y análisis exploratorio |
| Artefactos | Joblib + JSON | Pipelines serializados, métricas y metadatos |
| Base de datos app | Postgresql | Historial local y datos operativos; **no** almacena el corpus completo |
| Pruebas | pytest, pytest-django, DRF test client, Vitest | Tests de ML, API y frontend |
| Versionado | Git + GitHub | Commits, ramas, PR y documentación verificable |

No usar FastAPI ni Laravel para esta versión. **React habla solamente con Django**; Django llama al modelo Python importado dentro del mismo proceso. No existe una segunda API interna. Se puede trabajar con Vite y Django como dos procesos de desarrollo, pero hay **un solo backend de aplicación**.

## 2. Estado inicial y cambios propuestos

Estructura vista en VS Code:

```text
ReviewIQ/
├── Artefactos_entrenados/
├── backend/
├── frontend/
├── NLP/
├── Readme/
├── venv/
├── .gitignore
└── manage.py
```

Esta estructura **no es incorrecta**. Mantendremos `manage.py` en la raíz y `backend/` como paquete principal de Django **si actualmente contiene** `settings.py`, `urls.py`, `asgi.py` y `wsgi.py` (comprobar antes de mover). Los cambios propuestos son:

| Carpeta actual | Destino sugerido | Acción segura |
|---|---|---|
| `backend/` | `backend/` | Mantener configuración Django; agregar apps sin sobrescribir archivos existentes |
| `frontend/` | `frontend/` | Mantener y organizar React/Vite |
| `NLP/` | `ml/nlp/` | **Mover cuando se revisen imports y rutas**; no borrarla |
| `Artefactos_entrenados/` | `ml/artifacts/` | Mover solo después de actualizar las rutas de carga |
| `Readme/` | `docs/` | Mover guías `.md` y crear un `README.md` principal en la raíz |
| `venv/` | `venv/` | Mantener en local; excluir completamente de Git |
| `manage.py` | `manage.py` | Mantener en raíz |

> **Importante:** el árbol siguiente es el **estado objetivo**, no una afirmación de que esos archivos existan ahora. No efectuar reorganizaciones destructivas ni renombrar aplicaciones Django sin revisar `INSTALLED_APPS`, módulos, migraciones, scripts y pruebas.

## 3. Estructura objetivo, carpeta por carpeta

```text
ReviewIQ/
│
├── manage.py                          # Punto de entrada de Django, en raíz
├── README.md                          # Instalación, ejecución, dataset y demo
├── CONTRIBUCIONES.md                  # Aportes reales vinculados a commits
├── requirements.txt                   # Dependencias Python fijadas
├── .env.example                       # Configuración de ejemplo; sin secretos
├── .gitignore                         # Excluir venv, datos pesados y secretos
├── pyproject.toml                     # Configuración opcional de pytest/formatters
│
├── backend/                            # Paquete principal Django
│   ├── __init__.py
│   ├── settings.py                     # DRF, PostgreSQL, CORS en desarrollo, estáticos
│   ├── urls.py                         # /api/v1/ y ruta de React compilado
│   ├── asgi.py
│   ├── wsgi.py
│   └── apps/
│       ├── __init__.py
│       ├── predictions/                # Predicciones e historial
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py                # Modelo ORM para historial (opcional)
│       │   ├── serializers.py          # Validaciones de datos de entrada/salida
│       │   ├── views.py                # Controladores REST (sin NLP duplicado)
│       │   ├── urls.py
│       │   ├── services.py             # Adaptador a ml.inference
│       │   └── migrations/
│       │       └── __init__.py
│       └── analytics/                  # Métricas, trazas NLP y salud del servicio
│           ├── __init__.py
│           ├── apps.py
│           ├── views.py
│           └── urls.py
│
├── frontend/                           # React + Vite; nunca entrenar ML aquí
│   ├── package.json
│   ├── package-lock.json               # Lockfile real según gestor usado
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── components/
│       │   ├── ReviewForm.tsx          # Campo para reseña y envío
│       │   ├── StarPrediction.tsx      # Estrellas predichas y puntuaciones
│       │   ├── ProbabilityChart.tsx    # 5 probabilidades, una por estrella
│       │   ├── NLPTrace.tsx            # Antes/después del preprocesamiento
│       │   ├── ModelMetrics.tsx        # Comparación de clasificadores
│       │   └── ErrorMessage.tsx        # Errores visibles de la API
│       ├── pages/
│       │   ├── DashboardPage.tsx       # Resumen comercial e historial real
│       │   ├── PredictPage.tsx         # Predicción individual
│       │   ├── LaboratoryPage.tsx      # Transformaciones NLP y métricas
│       │   └── AboutPage.tsx           # Fuente, metodología y limitaciones
│       ├── services/
│       │   └── api.ts                  # Cliente tipado: fetch a /api/v1/
│       ├── types/
│       │   └── prediction.ts           # Contratos TypeScript de la API
│       └── tests/
│           └── ReviewForm.test.tsx
│
├── ml/                                 # Código compartido entrenamiento/inferencia
│   ├── __init__.py
│   ├── config.py                       # Seed, flags, rutas, parámetros
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py                  # Descarga documentada del dataset
│   │   ├── validate.py                  # Esquema, etiquetas y faltantes
│   │   ├── prepare.py                   # Filtrado y control de duplicados
│   │   ├── raw/                         # Corpus original NO versionado en Git
│   │   └── processed/                   # Datos derivados NO versionados
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── normalize.py                 # Emojis, URLs, tildes, números, etc.
│   │   ├── tokenize.py                  # Tokenización de reseñas en español
│   │   ├── stopwords.py                 # Lista ajustada, conserva negaciones
│   │   ├── stem_lemma.py                # Ambas variantes comparables
│   │   ├── transformer.py               # Transformer sklearn serializable
│   │   └── trace.py                     # Explicación paso a paso reutilizando NLP
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                      # CLI único: quick/full
│   │   ├── pipelines.py                  # Construye Pipeline NLP + TF-IDF + ML
│   │   ├── tune.py                       # Validación cruzada y parámetros
│   │   └── compare.py                    # Selección justificada del ganador
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluate.py                   # Métricas en validación y test final
│   │   ├── errors.py                     # Falsos aciertos/errores por clase
│   │   └── plots.py                      # Matriz confusión y gráficos exportados
│   ├── inference/
│   │   ├── __init__.py
│   │   └── predictor.py                  # Carga una vez, predict/predict_proba
│   └── artifacts/                       # Salidas del entrenamiento
│       ├── .gitkeep
│       └── (pipeline.joblib, metrics.json, manifest.json)
│
├── notebooks/
│   ├── 01_EDA.ipynb                      # Distribución, longitud, vacíos, etc.
│   └── 02_Experimentos_NLP.ipynb        # Stemming/lemas; uni/bi-gramas
│
├── tests/
│   ├── test_nlp.py                       # Ejemplos antes/después y negaciones
│   ├── test_training.py                  # Entrenamiento smoke con datos pequeños
│   ├── test_inference.py                 # Misma transformación en producción
│   ├── test_api.py                       # REST, errores, métricas y salud
│   └── test_reproducibility.py           # Seed y consistencia de ejecución
│
├── docs/
│   ├── ARQUITECTURA.md                   # Este documento
│   ├── DATASET.md                        # Origen, licencia, versión, etiquetas
│   ├── NLP.md                            # Decisiones y ejemplos antes/después
│   ├── MODELOS.md                        # Hiperparámetros y análisis comparativo
│   ├── API.md                            # Contratos de rutas y respuestas
│   ├── EXPERIMENTOS.md                   # Registro de pruebas sin inventar cifras
│   ├── GUIA-COMMITS.md                   # Ramas, PR y mensajes por módulo
│   ├── INFORME-TECNICO.md                # Informe exigido por el docente
│   └── DEFENSA.md                        # Preguntas y cambios en vivo
│
└── venv/                                # Entorno virtual SOLO local; ignorado
```

**Archivos opcionales solo si aportan valor:** `docker-compose.yml`, `.github/workflows/tests.yml`, `backend/apps/predictions/admin.py`, `/api/v1/predict/batch` y exportación CSV. No retrasar los requisitos obligatorios por funcionalidades extras.

## 4. Reglas de arquitectura (obligatorias)

1. **Una única API REST:** `/api/v1/...` en Django/DRF. React no consulta directamente modelos ni ficheros `.joblib`.
2. **Una sola fuente de verdad para NLP:** `ml/nlp/` se usa desde `ml/training/` y `ml/inference/`. Django **no reimplementa** normalización ni TF-IDF.
3. **Pipeline serializado completo:** guardar un `sklearn.pipeline.Pipeline` que incluya el transformador de NLP, el vectorizador TF-IDF y el clasificador. La inferencia invoca ese objeto directamente.
4. **Artefactos importables:** las clases personalizadas de los transformers viven en módulos Python estables (`ml.nlp.transformer`), nunca solo en notebooks, para que `joblib.load` pueda reconstruirlas.
5. **Entrenamiento independiente de HTTP:** `python -m ml.training.train ...` prepara y entrena offline. Una petición web **nunca** descarga dataset, entrena ni ajusta hiperparámetros.
6. **Cargar el modelo una vez por proceso:** `ml/inference/predictor.py` lo mantiene en memoria, sin deserializar en cada petición; no exponer escritura arbitraria de rutas de artefactos.
7. **La BD no es el dataset:** PostgreSQL puede guardar historial opcional de predicciones. Las reseñas del corpus se obtienen y procesan mediante scripts controlados.
8. **Separación limpia:** React solo presentación; Django valida, registra y responde; `ml/` realiza transformaciones y predicciones.
9. **Nada de resultados inventados:** las métricas del frontend deben provenir del último entrenamiento documentado, no de cifras simuladas.
10. **Uso académico:** comprobar la licencia y condiciones del corpus de Amazon; no promocionar un uso comercial real sin autorización de derechos.

## 5. Dataset, etiquetas y separación de datos

Fuente candidata: [`SetFit/amazon_reviews_multi_es`](https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es).

- Aproximadamente **200.000** ejemplos de `train`, **5.000** de `validation` y **5.000** de `test` (verificar ficha y versión exacta al descargar).
- En esta versión, las etiquetas habitualmente se almacenan como `label` de **0 a 4**. Convertir `stars = label + 1` **en un único punto documentado**; verificar primero el esquema real descargado.
- Mantener la separación oficial para la evaluación final. Dentro de `train`, usar particiones estratificadas y semilla fija si se necesita una subdivisión para experimentación, sin tocar el test.
- El conjunto `validation` sirve para comparar configuraciones y decidir el modelo. **No optimizar usando `test`**; se evalúa solo al finalizar.
- Investigar duplicados entre splits, vacíos, distribución de clases, longitud de textos, palabras frecuentes y posibles problemas del etiquetado.
- Guardar el origen, revisión de la fuente, fecha de descarga y términos de uso en `docs/DATASET.md`.

## 6. Diseño del pipeline y rendimiento en CPU

```text
reseña en español
  -> normalización justificada (sin destruir negaciones)
  -> tokenización
  -> stop words (probar conservando «no», «nunca», «sin»)
  -> stemming O lematización (ambas implementadas y evaluadas)
  -> TF-IDF (1,1) vs. TF-IDF (1,2)
  -> LogisticRegression O MultinomialNB
  -> distribución de probabilidad de 5 clases
  -> estrellas predichas = clase + 1
```

**Parámetros iniciales para investigar, no resultados garantizados:**

| Ajuste | Valor inicial | Motivo |
|---|---|---|
| `random_state` | `42` donde sea aplicable | Experimentos repetibles |
| `max_features` | `50_000` | Limitar memoria del vocabulario |
| `dtype` TF-IDF | `np.float32` | Reducir memoria de la matriz dispersa |
| `ngram_range` | `(1,1)` y `(1,2)` | Comparación obligatoria |
| `min_df` / `max_df` | Ajustar con validación | Evitar términos raros o ubicuos |
| Modo rápido | Muestra estratificada de ~20.000 | Desarrollo y cambios en vivo |
| Modo completo | Hasta 200.000 `train` | Comparación final |
| Matriz TF-IDF | CSR dispersa | No convertir a `.toarray()` |
| `n_jobs` / procesos | Moderado y configurable | Evitar saturar un PC de 16 GB |

**Dos modelos permitidos por el docente:** `LogisticRegression` multiclase y `MultinomialNB`. Compararlos por **macro-F1** como métrica principal y reportar accuracy, precision, recall, F1 por clase, matriz de confusión y errores por distancia de estrellas. Ajustar hiperparámetros con validación cruzada en al menos un modelo. Si se muestran probabilidades, describirlas como estimaciones del modelo; revisar su calibración antes de tratarlas como confianza fiable.

Para no disparar los tiempos de entrenamiento, hacer primero los experimentos con una muestra estratificada pequeña; únicamente las configuraciones prometedoras pasan al entrenamiento completo. La lematización con spaCy puede consumir más CPU que stemming; **medir el rendimiento**, no suponer cuál será mejor.

Ejemplos de comandos **a implementar**, no ejecutables hasta crear los módulos:

```bash
python -m ml.data.download
python -m ml.training.train --mode quick
python -m ml.training.train --mode full
python -m ml.evaluation.evaluate
python manage.py runserver
```

Para desarrollo frontend:

```bash
cd frontend
npm install
npm run dev
```

En desarrollo, Vite y Django pueden tener puertos distintos; Vite usa un proxy o CORS restringido. En distribución, `npm run build` genera los estáticos que Django puede servir con configuración adecuada, manteniendo **un único backend/API pública**.

## 7. Contratos REST de Django

Prefijo general: `/api/v1/`.

| Método y ruta | App/módulo | Función |
|---|---|---|
| `POST /api/v1/predict/` | `predictions` | Valida texto y predice de 1 a 5 estrellas |
| `GET /api/v1/metrics/` | `analytics` | Devuelve métricas reales guardadas |
| `GET /api/v1/health/` | `analytics` | Informa si el servicio y el modelo están listos |
| `POST /api/v1/nlp/trace/` | `analytics` | Devuelve los pasos NLP usando el código compartido |
| `GET /api/v1/history/` | `predictions` | Opcional: historial local de consultas |

**Ejemplo de solicitud:**

```json
{ "text": "El producto funciona, pero la batería dura muy poco." }
```

**Esquema propuesto de respuesta, con valores puramente ilustrativos:**

```json
{
  "stars": 3,
  "probabilities": { "1": 0.08, "2": 0.21, "3": 0.43, "4": 0.20, "5": 0.08 },
  "model_version": "reviewiq-v1"
}
```

La suma de probabilidades debe ser aproximadamente 1. Django validará tipo, longitud máxima y texto vacío. Si el artefacto no existe, devolver un error claro, **no una predicción simulada**. Se deben probar códigos `200`, `400` y `503` según corresponda. La documentación de API se mantiene en `docs/API.md` y, si se desea, en un esquema OpenAPI.

## 8. Frontend: pantallas y flujo

1. **Predicción:** escribir reseña, solicitar predicción, mostrar estrellas, barras de probabilidad y mensajes de error.
2. **Laboratorio NLP:** mostrar original, normalizado, tokens, stop words eliminadas y raíces/lemas. Los datos proceden del módulo compartido de Python mediante la API.
3. **Métricas de modelos:** mostrar resultados reales de LogisticRegression y MultinomialNB, macro-F1, matriz de confusión y configuración ganadora.
4. **Dashboard comercial:** resumen de predicciones almacenadas, tendencias y casos que podrían requerir revisión. Dejar claro que estas cifras son del uso de ReviewIQ, **no** de todas las ventas de Amazon.
5. **Acerca del proyecto:** dataset, autoría, limitaciones, tecnologías y decisiones técnicas.

No añadir autenticación, pagos, chatbot generativo, streaming ni integración con Amazon real si amenazan la fecha de entrega.

## 9. Responsabilidades y commits verificables

Aunque una sola persona implemente técnicamente los módulos, **no falsificar autores ni crear commits a nombre de compañeros**. El documento original prevé grupos de 3–4: consultar al docente si la entrega individual está autorizada.

| Área | Archivos centrales | Ejemplos de commits cuando el código realmente exista |
|---|---|---|
| Datos y EDA | `ml/data/`, `notebooks/01_EDA.ipynb` | `feat(data): validar etiquetas y particiones del corpus` |
| NLP | `ml/nlp/`, `notebooks/02_Experimentos_NLP.ipynb` | `feat(nlp): implementar stemming y lematizacion comparables` |
| Modelado | `ml/training/`, `ml/evaluation/` | `feat(ml): comparar logistic regression y naive bayes` |
| Inferencia | `ml/inference/`, `ml/artifacts/` | `feat(ml): serializar pipeline completo y reutilizarlo` |
| Django | `backend/apps/`, `backend/urls.py` | `feat(api): validar entradas y devolver probabilidades` |
| React | `frontend/src/` | `feat(web): mostrar prediccion de cinco estrellas` |
| Calidad | `tests/`, `frontend/src/tests/` | `test: cubrir pipeline y endpoints REST` |
| Documentación | `README.md`, `docs/` | `docs: registrar licencia y metodologia del dataset` |

**Normas para Git:**

- Crear commits pequeños y sustanciales **después de implementar y comprobar** cada cambio.
- Rama por funcionalidad (`feat/data`, `feat/nlp`, `feat/models`, `feat/django-api`, `feat/react-ui`). Integrar mediante PR revisado por otra persona real **cuando exista equipo**; si trabajas solo, solicitar criterio al docente en vez de simular revisión.
- No reescribir autorías ni fabricar contribuciones. `CONTRIBUCIONES.md` reflejará el historial auténtico.
- Antes de cada merge: `pytest`, pruebas frontend, instalación y smoke test.
- No subir `venv/`, `.env`, datasets completos, cachés, archivos SQLite personales ni artefactos masivos innecesarios.
- Para entregar: tag `entrega-final` en el commit aprobado y registrado antes del plazo.

## 10. Checklist de cumplimiento del documento del ingeniero

- [ ] Dataset público documentado: fuente, licencia y fecha.
- [ ] EDA: distribución de clases, longitudes, palabras frecuentes, nulos.
- [ ] Separación reproducible/estratificada y test intocable.
- [ ] Normalización, tokenización y stop words justificadas.
- [ ] Stemming y lematización **ambos implementados y comparados**.
- [ ] Unigramas frente a unigramas + bigramas.
- [ ] TF-IDF con `max_features`, `min_df`, `max_df` documentados.
- [ ] Regresión logística y MultinomialNB entrenados y comparados.
- [ ] Validación cruzada e hiperparámetros al menos en un modelo.
- [ ] Métricas reales, matriz de confusión y análisis de errores.
- [ ] Entrenamiento reproducible con un comando, versiones fijas y semilla.
- [ ] Pipeline completo serializado y cargado por Django sin reimplementación.
- [ ] API REST: predicción, métricas, health, validaciones, documentación y tests.
- [ ] React: entrada de reseñas, predicciones, pasos de NLP y comparación.
- [ ] README desde cero, informe técnico, diapositivas y contribuciones reales.
- [ ] Preparación para modificar stop words, n-gramas, hiperparámetros o una vista en vivo.
- [ ] Declaración transparente del uso de asistentes de IA en el informe.
- [ ] Tag `entrega-final` antes de las 23:59 del 2 de noviembre, para la presentación del 3 de noviembre (según el PDF).

## 11. Orden recomendado para implementar sin romper el proyecto

1. **Auditoría inicial:** abrir `backend/settings.py`, `backend/urls.py`, `manage.py`, `frontend/package.json` y el contenido de `NLP/`. No asumir carpetas vacías.
2. **Respaldar y reorganizar:** crear `ml/`, `docs/`, `notebooks/`, `tests/`; mover gradualmente las carpetas existentes y comprobar imports tras cada cambio.
3. **Datos y EDA:** probar la descarga, esquema, mapping de etiquetas, muestras y estadísticas.
4. **NLP:** implementar y probar cada transformación; conservar una trazabilidad del antes/después.
5. **Modelos:** entrenar dos candidatos en modo rápido; comparar variantes y medir CPU/RAM; luego ejecutar entrenamiento completo.
6. **Inferencia:** guardar el pipeline completo y confirmar que una predicción recargada coincide con la del entrenamiento.
7. **Django/DRF:** implementar endpoints y pruebas sin incluir lógica NLP en las vistas.
8. **React:** conectar API, mostrar probabilidades, trazas y métricas; después pulir interfaz.
9. **Pruebas globales:** reconstruir desde un clon limpio (sin `venv` ni modelos preexistentes), generar artefactos y comprobar la aplicación completa.
10. **Defensa:** practicar modificar una stop word, `ngram_range`, un hiperparámetro, una validación y una visualización, además de explicar cada commit.

---

### Criterio de finalización

La arquitectura se considera cumplida cuando **una instalación desde cero** puede obtener el dataset, entrenar modelos, guardar el pipeline, levantar Django, abrir React y conseguir una predicción verdadera acompañada de métricas y trazas de NLP. El docente debe poder identificar el código correspondiente a cada capa y comprobar sus cambios en Git.

**Fuente de requisitos:** `Proyecto_Integrador(1).pdf`, páginas 1–7. Las elecciones concretas de Django, React, nombres de archivos y parámetros iniciales son **decisiones propuestas para ReviewIQ**, no requisitos textuales del PDF.
