# 14 — Órdenes de trabajo por fase para implementar ReviewIQ

**Uso:** cuando se programe con un asistente o agente, **entregar una instrucción a la vez**, adjuntando `README.md`, el módulo específico, `00-MAPA-REQUISITOS.md`, `09-GIT-ROLES-COMMITS.md` y el PDF del ingeniero. **No ejecutar las siguientes fases hasta verificar la anterior**.

## Reglas globales para cualquier asistente

> Construimos ReviewIQ con NLP tradicional y scikit-learn, no un LLM. Debes obedecer literalmente la rúbrica del docente y nuestros `.md`. Antes de implementar, inspecciona el repositorio. No inventes datos, accuracy, hashes, revisiones de datasets, informes de pruebas ni métricas. Conserva el dataset train/validation/test y no entrenes con test. Usa clases 0–4 internamente, estrellas 1–5 externamente. Construye código modular, tipado, testeable y CPU-friendly. Implementa solamente una fase por solicitud. Antes de marcar terminado, ejecuta tests reales y reporta los comandos exactos y sus salidas; si algo no se pudo ejecutar, dilo. Documenta cualquier divergencia técnica. No hagas commits a nombre de otros ni inventes revisiones de PR. Si usas IA en código, recuérdanos actualizar declaración en informe.

## Fase A — Crear repositorio y configuración

> Implementa la estructura del repositorio, entorno Python 3.11, lock de dependencias, configuración de semilla `42`, README instalable, `.gitignore` adecuado para dataset restringido, carpetas `src/data`, `src/nlp`, `src/models`, `api`, `frontend`, `tests`, `docs`, `reports`. Entrega pruebas de estructura/config. No entrenes todavía. Referencias: `01`, `05`, `09`. Propón el commit `chore(repo): iniciar estructura reproducible y configuracion cpu` **solo si hay cambios reales**, y espera mi revisión antes de subirlo.

## Fase B — Dataset y EDA

> Sigue `02-DATOS-Y-EDA.md`. Implementa descarga segura, verificaciones, registros de origen/revisión/licencia, EDA e informe. No subas texto del corpus al Git. Usa splits originales y audita solapamientos. Tests y notebook ejecutables. Muestra conteos observados. Propon commits específicos para dataset, tests y EDA.

## Fase C — Pipeline NLP

> Sigue `03-PIPELINE-NLP.md`. Implementa normalizador configurable español, tokenización, stop words conservando negaciones, stemming y lematización, modo tracing ligado a los mismos transformadores, TF-IDF y n-gramas comparables. Tests de negación/tildes/números/URL/emojis. Evita duplicación NLP en API. Propon commits por mejoras verificadas.

## Fase D — Modelado ML

> Sigue `04-MODELOS-Y-EVALUACION.md`. Entrena SOLO MultinomialNB y LogisticRegression, comparando variantes NLP y unigramas/bigramas. Ajusta al menos un modelo con CV estratificada en train, elige usando validation, y solo cuando todo esté cerrado evalúa test. Reporta Macro-F1, accuracy, MAE ordinal, precisión/recall por clase, matriz y análisis de errores reales. Tests contra leakage. No falsifiques métricas.

## Fase E — Reproducibilidad/artefactos

> Sigue `05`. Implementa `python -m src.models.train --mode quick|full --seed 42`, incluye fuente fijada, configuración, informes JSON, manifest con hashes y `Pipeline` serializado completo. Valida round-trip joblib y CPU RAM. Quick para cambios de clase, full para evaluación académica. No conviertas sparse a denso.

## Fase F — Backend

> Sigue `06-BACKEND-API.md`. FastAPI carga artefacto una vez; implementa `/api/v1/health`, `/api/v1/predict`, `/api/v1/metrics`, `/api/v1/nlp/trace`. Pydantic y tests de respuestas y errores. Predice mediante **pipeline guardado**, no mediante una función nueva de NLP.

## Fase G — Frontend

> Sigue `07-FRONTEND-UX.md`. React + TypeScript + Vite. Crear cuatro vistas: predicción, laboratorio NLP real, métricas comparativas, metodología/limitaciones. Probabilidades 1–5 y matriz 5×5 desde API. Ningún porcentaje simulado en la versión evaluada. Responsive, accesibilidad, estados de fallo. Tests UI.

## Fase H — E2E, informe y presentación

> Sigue `08`, `10`, `11`, `13`. Ejecuta clon limpio, instalación, smoke/test/full según disponibilidad, API + frontend, benchmarking CPU, `INFORME_TECNICO.md`, README, CONTRIBUCIONES verdadero, diapositivas, y ensayos de modificación en vivo. Comprueba la matriz de `00` y reporta casillas pendientes con transparencia. No crees `entrega-final` hasta mi aprobación.

## Formato de reporte requerido al finalizar cada fase

```text
Fase ejecutada:
Archivos reales creados/modificados:
Qué y por qué se decidió:
Comandos ejecutados y resultados:
Tests (aprobados/fallidos/no ejecutados):
Riesgos o bloqueos:
Commits PROPUESTOS (no inventados):
Requisito del PDF que queda cubierto:
Próximo paso recomendado:
```

## Importantísimo para el ingeniero

Los prompts son instrucciones de implementación y no son evidencia de trabajo. Las evidencias son **archivos ejecutables, diffs, métricas verificables, tests, autores verdaderos y commits reales**.
