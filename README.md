# ReviewIQ

## Estado del repositorio

La referencia vigente es [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): Django/DRF como único backend, PostgreSQL, React + TypeScript + Vite y módulos de ML en `ml/`. Las guías originales en `docs/docs/` conservan propuestas anteriores de FastAPI y `src/`; se adaptarán a esta arquitectura al implementar cada fase.

La arquitectura inicial y las **fases B (datos y EDA), C (pipeline NLP), D (modelado ML), E (reproducción y artefactos) y F (backend REST)** están implementadas. Django/DRF sirve predicciones, métricas, estado y trazas mediante el paquete verificado. El frontend todavía conserva la plantilla de Vite y no está conectado.

`venv/`, `node_modules/`, los datos restringidos y los artefactos generados se excluyen de Git. `.env.example` enumera las variables de configuración: deben exportarse en la terminal; Django aún no carga archivos `.env` automáticamente. La clave de desarrollo es pública y solo sirve en local; con `DJANGO_DEBUG=False` se exige `DJANGO_SECRET_KEY`.

Comprobación mínima del backend desde PowerShell con Python 3.11:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
```

Esta comprobación valida la configuración sin conectarse a PostgreSQL. La API de inferencia puede levantarse con runapi sin base de datos; el admin, runserver habitual y las migraciones requieren PostgreSQL y sus variables de conexión.

## Datos y análisis exploratorio

Desde la raíz del repositorio, con las dependencias de `requirements.txt` instaladas:

```powershell
.\venv\Scripts\python.exe -m ml.data.eda
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_data.py -v
```

El primer comando descarga y verifica la revisión fijada en `config.json`, audita las particiones originales, prepara los datos locales y genera `reports/eda_summary.json`, `reports/dataset_manifest.json`, `reports/data_preparation.json` y tres figuras. No necesita Django ni una base de datos. También se puede ejecutar solo la descarga con `python -m ml.data.download` o la preparación con `python -m ml.data.prepare`.

Se observaron 200.000 / 5.000 / 5.000 filas originales. La limpieza deja **197.572 filas de train** y conserva las filas de validación y prueba; se verificó que train preparado no comparte IDs ni textos normalizados con los conjuntos reservados. El corpus crudo y preparado permanece en carpetas ignoradas por Git. Ver [origen, licencia y decisiones](docs/DATASET.md) y [evidencia de la Fase B](docs/FASE-B-DATOS-EDA.md).

Para regenerar el notebook con el mismo intérprete del entorno:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\python.exe scripts/run_eda_notebook.py
```

Los archivos de dependencias se generaron con pip-tools en Windows y Python 3.11. Para actualizarlos de forma explícita:

```powershell
.\venv\Scripts\python.exe -m piptools compile --no-header --no-emit-index-url --no-strip-extras --output-file requirements.txt requirements.in
.\venv\Scripts\python.exe -m piptools compile --no-header --no-emit-index-url --no-strip-extras --constraint requirements.txt --output-file requirements-dev.txt requirements-dev.in
```

## Pipeline NLP y comparación de variantes

`ml/nlp/` contiene normalización NFKC, tokens, stop words versionadas con negaciones protegidas, Snowball español, lematización spaCy por lotes y TF-IDF disperso `float32`. La traza ejecuta las mismas etapas del transformador que usarán entrenamiento y API. Las dependencias fijadas incluyen `es_core_news_sm==3.8.0`, instalado desde su wheel oficial con SHA-256; no se descarga ningún recurso durante inferencia.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ml.nlp.trace --text "No me gusto, sin garantia tras 2 dias" --morphology stemming
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_nlp.py -v
.\venv\Scripts\python.exe -m ml.nlp.compare
```

La comparación usa una muestra estratificada fija de 20.000 filas de train preparado y las 5.000 de validation, con semilla 42 y MultinomialNB fijo. Compara stemming/lematización y unigramas/uni+bigramas; no abre test. Produce `reports/nlp_comparison.csv` y `.json`, con Macro-F1, vocabulario, dispersión y coste de CPU/RAM medidos. La recomendación experimental es **stemming + (1,2)**, Macro-F1 de validación **0,4783**; no son métricas finales.

Ver [políticas y resultados NLP](docs/NLP.md), [evidencia de la Fase C](docs/FASE-C-PIPELINE-NLP.md) y [trazas de un ejemplo sintético](reports/nlp_trace_examples.json).

## Modelado ML

La Fase D compara MultinomialNB y LogisticRegression con variantes NLP, ajusta alpha/C mediante tres folds estratificados dentro de train y reajusta ambos finalistas con las 197.572 filas de train preparado. Las 5.000 filas de validation eligen el campeón por mayor Macro-F1, menor MAE y desempate estable. NLP y TF-IDF se ajustan dentro de cada fold; test no participa en selección.

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_models.py -v
.\venv\Scripts\python.exe -m ml.training.train --mode quick --seed 42
```

Quick es experimental: ajusta los parámetros congelados sobre 20.000 filas de train y mide validation; genera su propio paquete en `ml/artifacts/quick/`, excluido de Git. El protocolo histórico de selección y la única evaluación final se describen en [MODELOS.md](docs/MODELOS.md). Los registros persistidos bloquean sobrescribir la selección o repetir test.

Los informes de selección y evaluación están en `reports/model_comparison.*`, `reports/model_selection.json`, `reports/test_metrics.json` y `reports/final_test_ledger.json`; el análisis de errores está en `reports/errors.md`. El checkpoint binario queda local en `ml/artifacts/`, fuera de Git. Ver [evidencia de la Fase D](docs/FASE-D-MODELADO.md).

El campeón es **regresión logística con lematización y bigramas, C=1**. Su única evaluación de test obtuvo **Macro-F1 0,5131**, **accuracy 51,54 %** y **MAE 0,6128 estrellas**. El ajuste full completo tomó 19,57 minutos y registró 1.311,70 MiB de pico RSS en este equipo; las estrellas intermedias siguen siendo difíciles de distinguir.

## Reproducción y artefactos de inferencia

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42
```

Verifica el paquete local, o lo genera desde el checkpoint evaluado; si no existen, descarga el corpus fijado y reconstruye el campeón con sus parámetros congelados. `--rebuild` fuerza este último camino. Full exige reproducir exactamente el estado aprendido antes de asociar las métricas históricas; no vuelve a predecir test ni a seleccionar hiperparámetros. El paquete incluye pipeline completo, manifiesto, métricas, informe de construcción y benchmark local.

```python
from ml.inference.predictor import get_predictor

predictor = get_predictor()
print(predictor.predict(["Excelente producto, llegó a tiempo."]))
```

La carga comprueba hashes, versiones, código NLP e identidad del estado; se reutiliza por proceso. Consulte [comandos y contrato del paquete](docs/ARTEFACTOS.md), [evidencia de la Fase E](docs/FASE-E-REPRODUCIBILIDAD.md) y [medidas de rendimiento](docs/RENDIMIENTO.md). Los binarios permanecen fuera de Git y se regeneran con el comando anterior.

## Backend REST

Con el paquete full generado:

```powershell
.\venv\Scripts\python.exe manage.py runapi 127.0.0.1:8000 --noreload --nothreading
```

El servidor carga y calienta el pipeline al iniciar, sin guardar reseñas ni consultar PostgreSQL. Si no existe un paquete válido, health devuelve 503. Configure REVIEWIQ_MODEL_DIR para usar otro paquete y reinicie al cambiarlo. Documentación interactiva en [localhost:8000/docs/](http://127.0.0.1:8000/docs/), con recursos locales de Swagger.

| Método y ruta | Función |
|---|---|
| GET /api/v1/health/ | Estado e identidad del modelo |
| POST /api/v1/predict/ | JSON con text → estrellas 1–5 y cinco probabilidades |
| GET /api/v1/metrics/ | Métricas precalculadas del modelo activo y comparación de validation |
| POST /api/v1/nlp/trace/ | Etapas reales y limitadas del NLP guardado |

Se aceptan también las rutas sin barra final. La entrada admite hasta 3.000 caracteres; errores JSON en español, cuerpo limitado a 64 KiB y CORS restringido a los orígenes configurados. Ver [contrato y ejemplos](docs/API.md), [esquema OpenAPI](docs/openapi.json) y [evidencia de la Fase F](docs/FASE-F-BACKEND.md).

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_api.py -v
.\venv\Scripts\python.exe scripts/check_api.py
```

El segundo comando levanta y cierra su propio servidor para comprobar HTTP real; no necesita otro servidor abierto. Las ocho pruebas y la comprobación HTTP se ejecutaron con el paquete real disponible; no se reentrenó ni se volvió a evaluar test.

La próxima fase es **G: frontend React conectado**. Las métricas de test corresponden al campeón congelado; no se usarán para volver a elegir parámetros.


**Proyecto integrador: Tópicos y Programación Avanzada (primer parcial)**  
**Estado:** avance implementado hasta la Fase F; las guías siguientes conservan los requisitos originales y las fases pendientes.  
**Objeto:** producto académico que predice la **valoración en estrellas (1–5)** a partir de texto de reseñas comerciales en español, utilizando **TF-IDF + regresión logística multinomial / Multinomial Naive Bayes**.  
**Fuente principal de requisitos:** `Proyecto_Integrador(1).pdf`, 7 páginas, proporcionado por el docente.  
**Fecha de exposición:** 3 de noviembre de 2026; **último commit evaluado:** 2 de noviembre de 2026, 23:59; crear tag `entrega-final`.

> **Advertencia de autoría:** el enunciado especifica **3–4 estudiantes**. Una implementación exclusivamente individual necesita autorización del docente. Si una sola persona escribe todo, no se deben fabricar contribuciones, cuentas ni revisiones de compañeros. El historial deberá reflejar la realidad.

## Guías por responsabilidad (orden de trabajo)

| Archivo | Responsabilidad | Entregable verificable |
|---|---|---|
| [`docs/00-MAPA-REQUISITOS.md`](docs/docs/00-MAPA-REQUISITOS.md) | Control de rúbrica | Matriz requisito → prueba/evidencia |
| [`docs/01-PRODUCTO-Y-ARQUITECTURA.md`](docs/docs/01-PRODUCTO-Y-ARQUITECTURA.md) | Producto | Caso de uso, alcance, arquitectura |
| [`docs/02-DATOS-Y-EDA.md`](docs/docs/02-DATOS-Y-EDA.md) | Datos | Descargar, auditar, EDA, división |
| [`docs/03-PIPELINE-NLP.md`](docs/docs/03-PIPELINE-NLP.md) | NLP | Normalizar, tokenizar, comparar técnicas, TF-IDF |
| [`docs/04-MODELOS-Y-EVALUACION.md`](docs/docs/04-MODELOS-Y-EVALUACION.md) | Modelado ML | Entrenar y comparar dos modelos |
| [`docs/05-REPRODUCIBILIDAD-Y-RENDIMIENTO.md`](docs/docs/05-REPRODUCIBILIDAD-Y-RENDIMIENTO.md) | Empaquetado | Entrenamiento de un comando, artefactos, modo rápido |
| [`docs/06-BACKEND-API.md`](docs/docs/06-BACKEND-API.md) | Backend | Contrato de API (adaptar a Django/DRF) |
| [`docs/07-FRONTEND-UX.md`](docs/docs/07-FRONTEND-UX.md) | Frontend | Aplicación web conectada, análisis NLP y métricas |
| [`docs/08-PRUEBAS-Y-ACEPTACION.md`](docs/docs/08-PRUEBAS-Y-ACEPTACION.md) | Calidad | Verificación reproducible extremo a extremo |
| [`docs/09-GIT-ROLES-COMMITS.md`](docs/docs/09-GIT-ROLES-COMMITS.md) | Trazabilidad | Ramas, commits reales, PR, autoría |
| [`docs/10-INFORME-Y-DEFENSA.md`](docs/docs/10-INFORME-Y-DEFENSA.md) | Informe/defensa | Estructura técnica, presentación, simulacros |
| [`docs/11-CRONOGRAMA-Y-CHECKLIST.md`](docs/docs/11-CRONOGRAMA-Y-CHECKLIST.md) | Coordinación | Prioridades, dependencias y entregables |
| [`docs/12-DECISIONES-Y-RIESGOS.md`](docs/docs/12-DECISIONES-Y-RIESGOS.md) | Arquitectura | ADRs, limitaciones, riesgos y mitigaciones |
| [`docs/13-FUENTES-Y-LICENCIAS.md`](docs/docs/13-FUENTES-Y-LICENCIAS.md) | Cumplimiento | Datos, licencias, referencias, uso de IA |
| [`docs/14-ORDEN-DE-IMPLEMENTACION-PARA-AGENTE.md`](docs/docs/14-ORDEN-DE-IMPLEMENTACION-PARA-AGENTE.md) | Trabajo guiado | Instrucciones precisas por fase para implementador/IA |
| [`docs/15-ESTRUCTURA-DEL-REPOSITORIO.md`](docs/docs/15-ESTRUCTURA-DEL-REPOSITORIO.md) | Ingeniería | Mapa completo de archivos del software a crear |
| [`CONTRIBUCIONES.md`](CONTRIBUCIONES.md) | Evidencias | Plantilla de trabajo realmente realizado |
| [`plantillas/PULL_REQUEST.md`](docs/plantillas/PULL_REQUEST.md) | Revisión | Plantilla para cada PR |
| [`plantillas/REGISTRO-EXPERIMENTO.md`](docs/plantillas/REGISTRO-EXPERIMENTO.md) | Experimentos | Registro auditable de modelos/EDA |

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

- Backend: Python 3.11 + Django + Django REST Framework + scikit-learn + Joblib.
- Frontend: React + TypeScript + Vite, interfaz responsiva.
- Procesamiento español: expresiones regulares/normalizador propio, stop words curadas, NLTK Snowball (stemming), spaCy español (lematización, en comparativa y solo en producción si gana).
- CPU: TF-IDF disperso `float32`, inicialmente máximo 50.000 rasgos; no convertir matrices dispersas a densas.
- PostgreSQL para datos operativos; el corpus y los artefactos de ML se gestionan fuera de la base de datos.

## Orden mínimo de ejecución para el equipo de desarrollo

1. `02` datos → `03` NLP → `04` modelos → `05` artefactos.
2. `06` API → `07` frontend → `08` pruebas extremo a extremo.
3. `09` trazabilidad **durante** cada fase → `10` informe → `11` entrega.

## Alcance actual

El sistema todavía requiere frontend conectado y verificación integrada. Las rutas originales `src/` y FastAPI de las guías se adaptan a `ml/` y Django/DRF según ARQUITECTURA.md. Los informes agregados registran resultados reales; los datos de Amazon y los binarios generados se excluyen de Git.
