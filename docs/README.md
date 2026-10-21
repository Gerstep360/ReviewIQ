# ReviewIQ — Paquete de especificaciones de desarrollo

> Referencia vigente: [ARQUITECTURA.md](ARQUITECTURA.md), con Django/DRF, PostgreSQL y ml/. Las guías de este paquete conservan propuestas anteriores de FastAPI y src/; deben adaptarse al implementar cada fase. El [README principal](../README.md) informa el estado real del repositorio.

**Proyecto integrador: Tópicos y Programación Avanzada (primer parcial)**  
**Estado:** planificación y criterios de aceptación; *el código, los entrenamientos y las métricas aún deben implementarse y medirse*.  
**Objeto:** producto académico que predice la **valoración en estrellas (1–5)** a partir de texto de reseñas comerciales en español, utilizando **TF-IDF + regresión logística multinomial / Multinomial Naive Bayes**.  
**Fuente principal de requisitos:** `Proyecto_Integrador(1).pdf`, 7 páginas, proporcionado por el docente.  
**Fecha de exposición:** 3 de noviembre de 2026; **último commit evaluado:** 2 de noviembre de 2026, 23:59; crear tag `entrega-final`.

> **Advertencia de autoría:** el enunciado especifica **3–4 estudiantes**. Una implementación exclusivamente individual necesita autorización del docente. Si una sola persona escribe todo, no se deben fabricar contribuciones, cuentas ni revisiones de compañeros. El historial deberá reflejar la realidad.

## Guías por responsabilidad (orden de trabajo)

| Archivo | Responsabilidad | Entregable verificable |
|---|---|---|
| [`docs/00-MAPA-REQUISITOS.md`](docs/00-MAPA-REQUISITOS.md) | Control de rúbrica | Matriz requisito → prueba/evidencia |
| [`docs/01-PRODUCTO-Y-ARQUITECTURA.md`](docs/01-PRODUCTO-Y-ARQUITECTURA.md) | Producto | Caso de uso, alcance, arquitectura |
| [`docs/02-DATOS-Y-EDA.md`](docs/02-DATOS-Y-EDA.md) | Datos | Descargar, auditar, EDA, división |
| [`docs/03-PIPELINE-NLP.md`](docs/03-PIPELINE-NLP.md) | NLP | Normalizar, tokenizar, comparar técnicas, TF-IDF |
| [`docs/04-MODELOS-Y-EVALUACION.md`](docs/04-MODELOS-Y-EVALUACION.md) | Modelado ML | Entrenar y comparar dos modelos |
| [`docs/05-REPRODUCIBILIDAD-Y-RENDIMIENTO.md`](docs/05-REPRODUCIBILIDAD-Y-RENDIMIENTO.md) | Empaquetado | Entrenamiento de un comando, artefactos, modo rápido |
| [`docs/06-BACKEND-API.md`](docs/06-BACKEND-API.md) | Backend | API FastAPI y pruebas |
| [`docs/07-FRONTEND-UX.md`](docs/07-FRONTEND-UX.md) | Frontend | Aplicación web conectada, análisis NLP y métricas |
| [`docs/08-PRUEBAS-Y-ACEPTACION.md`](docs/08-PRUEBAS-Y-ACEPTACION.md) | Calidad | Verificación reproducible extremo a extremo |
| [`docs/09-GIT-ROLES-COMMITS.md`](docs/09-GIT-ROLES-COMMITS.md) | Trazabilidad | Ramas, commits reales, PR, autoría |
| [`docs/10-INFORME-Y-DEFENSA.md`](docs/10-INFORME-Y-DEFENSA.md) | Informe/defensa | Estructura técnica, presentación, simulacros |
| [`docs/11-CRONOGRAMA-Y-CHECKLIST.md`](docs/11-CRONOGRAMA-Y-CHECKLIST.md) | Coordinación | Prioridades, dependencias y entregables |
| [`docs/12-DECISIONES-Y-RIESGOS.md`](docs/12-DECISIONES-Y-RIESGOS.md) | Arquitectura | ADRs, limitaciones, riesgos y mitigaciones |
| [`docs/13-FUENTES-Y-LICENCIAS.md`](docs/13-FUENTES-Y-LICENCIAS.md) | Cumplimiento | Datos, licencias, referencias, uso de IA |
| [`docs/14-ORDEN-DE-IMPLEMENTACION-PARA-AGENTE.md`](docs/14-ORDEN-DE-IMPLEMENTACION-PARA-AGENTE.md) | Trabajo guiado | Instrucciones precisas por fase para implementador/IA |
| [`docs/15-ESTRUCTURA-DEL-REPOSITORIO.md`](docs/15-ESTRUCTURA-DEL-REPOSITORIO.md) | Ingeniería | Mapa completo de archivos del software a crear |
| [`CONTRIBUCIONES.md`](CONTRIBUCIONES.md) | Evidencias | Plantilla de trabajo realmente realizado |
| [`plantillas/PULL_REQUEST.md`](plantillas/PULL_REQUEST.md) | Revisión | Plantilla para cada PR |
| [`plantillas/REGISTRO-EXPERIMENTO.md`](plantillas/REGISTRO-EXPERIMENTO.md) | Experimentos | Registro auditable de modelos/EDA |

## Principios no negociables

1. El predictor de estrellas **no es un LLM**. Dos candidatos clásicos permitidos: regresión logística y MultinomialNB.
2. `label=0..4` en el dataset `SetFit/amazon_reviews_multi_es` ⇒ **estrellas mostradas = `label+1`**. `label_text` nunca entra como variable predictora.
3. Corpus: `train` 200.000; `validation` 5.000; `test` 5.000. **No mezclar splits** ni ajustar con test.
4. Un pipeline serializado contiene el **mismo** preprocesador y vectorizador que se usan en la API. No copiar la lógica NLP al backend.
5. Mostrar stemming y lematización; medir ambos antes de elegir. Mostrar unigramas vs unigramas+bigramas.
6. Decidir con validación; evaluar **una sola vez** en test final; informar resultados reales, nunca inventar F1, latencia, consumo de RAM o accuracy.
7. Un comando desde datos crudos hasta artefactos; entorno fijado; prueba de instalación limpia.
8. Los datos de Amazon tienen **restricción de uso académico**; este es un prototipo **académico**, no un modelo reutilizable comercialmente sin derechos adecuados.
9. Los ejemplos de commits son **plantillas de mensajes futuros**, no prueba de trabajo realizado.

## Desarrollo sugerido

- Backend: Python 3.11 + scikit-learn + FastAPI + Pydantic + Joblib.
- Frontend: React + TypeScript + Vite, interfaz responsiva.
- Procesamiento español: expresiones regulares/normalizador propio, stop words curadas, NLTK Snowball (stemming), spaCy español (lematización, en comparativa y solo en producción si gana).
- CPU: TF-IDF disperso `float32`, inicialmente máximo 50.000 rasgos; no convertir matrices dispersas a densas.
- Sin base de datos obligatoria; métricas obtenidas de artefactos versionados y ejemplos locales no persistentes.

## Orden mínimo de ejecución para el equipo de desarrollo

1. `02` datos → `03` NLP → `04` modelos → `05` artefactos.
2. `06` API → `07` frontend → `08` pruebas extremo a extremo.
3. `09` trazabilidad **durante** cada fase → `10` informe → `11` entrega.

## Lo que NO contiene este paquete

No es un software ya terminado. Son documentos de implementación y control para construirlo. Los comandos y rutas propuestos deben implementarse y validarse en el repositorio del proyecto. Tampoco incluye métricas de modelos entrenados ni archivos de datos de Amazon.
