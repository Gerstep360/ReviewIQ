# ReviewIQ

## Estado del repositorio

La referencia vigente es [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): Django/DRF como único backend, PostgreSQL, React + TypeScript + Vite y módulos de ML en `ml/`. Las guías originales en `docs/docs/` conservan propuestas anteriores de FastAPI y `src/`; se adaptarán a esta arquitectura al implementar cada fase.

La arquitectura inicial y la **Fase B (datos y EDA)** están implementadas. Hay descarga reproducible, validación, preparación de datos, informes y un notebook ejecutado. Se mantienen el esqueleto de Django y la plantilla de Vite. Todavía no hay endpoints de predicción ni modelos entrenados; las dependencias de DRF y modelado se agregarán en sus fases.

`venv/`, `node_modules/`, los datos restringidos y los artefactos generados se excluyen de Git. `.env.example` enumera las variables de configuración: deben exportarse en la terminal; Django aún no carga archivos `.env` automáticamente. La clave de desarrollo es pública y solo sirve en local; con `DJANGO_DEBUG=False` se exige `DJANGO_SECRET_KEY`.

Comprobación mínima del backend desde PowerShell con Python 3.11:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
```

Esta comprobación valida la configuración sin conectarse a PostgreSQL. Ejecutar migraciones y levantar la aplicación requerirá una base de datos local y las variables de conexión correspondientes.

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

La próxima fase es **C: pipeline NLP**, usando `ml/nlp/` y los datos preparados. No se ha ejecutado validación cruzada ni evaluación de modelos con test.


**Proyecto integrador: Tópicos y Programación Avanzada (primer parcial)**  
**Estado:** planificación y criterios de aceptación; *el código, los entrenamientos y las métricas aún deben implementarse y medirse*.  
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

## Lo que NO contiene este paquete

No es un software ya terminado. Son documentos de implementación y control para construirlo. Los comandos y rutas propuestos deben implementarse y validarse en el repositorio del proyecto. Tampoco incluye métricas de modelos entrenados ni archivos de datos de Amazon.
