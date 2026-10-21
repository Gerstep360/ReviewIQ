# 04 — Responsabilidad: modelos clásicos ML, selección y métricas

## Tarea EXACTA

**Clasificación multiclase** del valor de reseña: clases internas `0,1,2,3,4` = estrellas públicas `1,2,3,4,5`. No plantear regresión numérica y no usar salidas de LLM. El documento permite escoger otro modelo del temario si se justifica; regresión logística y Naive Bayes están listados como clasificadores.

## Modelos seleccionados (máximo dos)

1. **LogisticRegression** con 5 clases, TF-IDF disperso, `solver='lbfgs'` o `saga` medidos (evitar parámetros deprecados en la versión fijada), `max_iter` suficiente, `C` tunable; usar las probabilidades de `predict_proba`.
2. **MultinomialNB**, texto con TF-IDF no negativo, `alpha` tunable; referencia económica en CPU.

Una **línea base adicional no entrenada** (predecir clase mayoritaria) puede informarse para contexto. No introducir terceros clasificadores aprendidos salvo que el docente apruebe ampliar el alcance.

## División y selección rigurosa

- **Train oficial (200k):** entrenamiento y búsqueda con StratifiedKFold, semilla=42. Muestra pequeña estratificada de 20k–40k para búsqueda inicial.
- **Validation oficial (5k):** decisión final entre combinaciones previamente definidas (modelo + método NLP + ngramas); comparar de manera controlada y dejar registro de todas las elecciones.
- **Test oficial (5k):** una única evaluación final tras congelar TODO (pipeline, hiperparámetros y umbral de producto). No usar test como optimizador ni repetir hasta obtener una métrica mejor.
- Evitar **data leakage**: cada fold reajusta tanto NLP aprendido como TF-IDF dentro de Pipeline; IDF nunca se calcula antes del split.
- Al acabar selección: reentrenar pipeline elegido con train (opcional train+validation **solo si** se documenta y test queda intocado, pero se recomienda mantener train para simplicidad y auditabilidad).

## Búsqueda pequeña y viable en CPU

- NB: `alpha` ∈ {0.1, 1.0, 2.0}.
- LogisticRegression: `C` ∈ {0.5, 1, 2}; `max_iter` ∈ {200, 500} solo si converge; ajustar según registros de warning.
- Comparar NLP `stemming` vs `lemmatization` y `ngram_range=(1,1)` vs `(1,2)` **sin explosión combinatoria**: etapas sucesivas (primero muestreo 20k, luego mejor configuración). Documentar qué datos se usaron en cada etapa.
- CV mínima recomendable: StratifiedKFold de 3 folds, `n_jobs=1` al inicio para evitar copias excesivas de RAM; evaluar aumentar solo con mediciones.
- Fijar presupuesto de entrenamiento e informar tiempo y uso pico de memoria **medidos**.

## Métricas obligatorias y recomendadas

| Métrica | Uso |
|---|---|
| **Macro-F1** (métrica principal) | Dar peso igual a cada estrella |
| Accuracy | Porcentaje de clases exactas |
| Precision/Recall/F1 por clase | Identificar 1–5 estrellas difíciles |
| Matriz de confusión 5x5 | Mostrar confusión de clases próximas |
| **MAE en estrellas** | Capturar severidad del error ordinal (1 vs 2 menos grave que 1 vs 5) |
| Log loss / Brier multicategoría opcional | Calidad/calibración de probabilidades |
| Latencia p50/p95 y tamaño de artefacto | Criterio operativo medido |

**Importante:** la probabilidad de scikit-learn es una **estimación del modelo**; no afirmar calibración perfecta. Si se calibra, hacerlo en datos de entrenamiento/validación separados de test y documentarlo sin añadir un tercer clasificador a la rúbrica.

## Evidencia de análisis de errores

Examinar reseñas mal clasificadas en `validation`/test final sin escoger modelo por test. Categorías plausibles: sarcasmo, texto mixto, reseñas muy cortas, negaciones, estrellas intermedias y dominios ambiguos. Publicar ejemplos mínimos desidentificados, sin intentar localizar autores.

## Productos finales

- `src/models/train.py`: interfaz `--mode quick|full --seed 42`;
- `src/models/evaluate.py` y `src/models/export.py`;
- `reports/model_comparison.csv` (resultados de validation);
- `reports/test_metrics.json` (única evaluación test del campeón);
- `reports/confusion_matrix.png`, `reports/errors.md`;
- `artifacts/reviewiq_pipeline.joblib` (o script que lo produce), `artifacts/manifest.json`.

## Aceptación

- [ ] Dos modelos de los vistos por el docente, ninguno generativo.
- [ ] CV realizada dentro de train en por lo menos un modelo.
- [ ] Criterio de selección definido ANTES de consultar test.
- [ ] Métricas completas, matriz y errores reales con semilla/revisión registradas.
- [ ] Probabilidades suman aproximadamente 1 en cada predicción y se mapean a 1–5 correctamente.

## Commits de ejemplo

- `feat(ml): entrenar baseline naive bayes con tfidf disperso`
- `feat(ml): implementar regresion logistica multiclase`
- `feat(ml): ajustar hiperparametros con validacion cruzada estratificada`
- `test(ml): impedir filtracion de test y validar mapa de estrellas`
- `docs(ml): registrar comparacion de metricas y analisis de errores`
