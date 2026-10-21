# 05 — Responsabilidad: pipeline serializado, reproducción y rendimiento en CPU

## Meta

En una PC normal (referencia inicial: CPU de escritorio, 16 GB RAM, sin GPU dedicada) generar **desde el dataset original hasta artefactos listos para API mediante un solo comando**. Que el despliegue no reimplemente el NLP.

## Entrenamiento de un comando (contrato a implementar)

```bash
python -m src.models.train --mode quick --seed 42
python -m src.models.train --mode full --seed 42
```

- `quick`: muestra estratificada fija de ~20.000 instancias **solo train**; útil para desarrollar/cambiar parámetros en defensa. Sus métricas deben estar marcadas **experimentales, no métricas finales**.
- `full`: entrenar con hasta 200.000 registros train; permitir que dos modelos se ajusten con recursos acotados, evaluar como se prescribe, generar manifest y exports.
- El script descarga/valida (o cache local versionada) → EDA mínimo → experimentos → compara modelos → selecciona con validación → test final controlado → serializa → produce reportes JSON y resumen.
- Reejecuciones de `full` deben **no** reevaluar test para iterar el diseño si ya fue usado; registrar fecha/versión de la evaluación final.
- El entrenamiento de laboratorio no debe depender de archivos ocultos ni de clicks en un notebook.

## Configuración única versionada

```yaml
seed: 42
dataset:
  repository: SetFit/amazon_reviews_multi_es
  revision: TODO_SHA_REAL
  split_train: train
  split_validation: validation
  split_test: test
nlp:
  morphology: stemming            # comparado previamente con lemmatization
  protect_negations: ["no", "ni", "sin", "nunca", "jamas"]
  ngram_range: [1, 2]             # seleccionado después de experimentos
  tfidf:
    max_features: 50000
    min_df: 2
    max_df: 0.98
    sublinear_tf: true
model:
  seed: 42
  scoring: f1_macro
runtime:
  quick_train_rows: 20000
  n_jobs: 1
```

No copiar esta propuesta como «resultado ganador». Modificar `config.yaml` cuando existan experimentos reales; `TODO_SHA_REAL` debe sustituirse por una revisión **verificada** antes de cierre.

## Optimización sin perder corrección

1. **Matrices dispersas** CSR y `TfidfVectorizer(dtype=np.float32)`; evitar `.toarray()`, one-hot denso o embeddings grandes.
2. `max_features` inicial 50.000, sujeto a estudio. Conservar vocabulario y dimensiones en manifest.
3. Regresión logística con solucionador compatible con matrices dispersas; controlar convergencia (`ConvergenceWarning`) y registrar solver, `max_iter`, tiempo.
4. Naive Bayes: procesamiento de TF-IDF sin valores negativos; serializar pipeline completo.
5. Ejecutar CV con `n_jobs=1` de inicio; aumentar paralelismo si RAM y CPU lo justifican con medidas. Múltiples procesos pueden duplicar grandes matrices.
6. Realizar búsquedas sobre muestra estratificada, confirmar en validación oficial y reentrenar final sobre train.
7. Stemming generalmente más ligero que spaCy; **no asumir** que es más preciso: verificar Macro-F1 de ambas variantes. Si se usa spaCy, instalar modelo de idioma fijado y procesar por lotes; no descargarlo en cada predicción.
8. `joblib.dump()` solo de **pipeline controlado y confiable**. `joblib.load()` ejecuta deserialización de Python: nunca cargar artefactos de usuarios ni archivos remotos no confiables.
9. Para servir usar **un único worker** al comenzar; workers múltiples pueden duplicar RAM. Medir RSS y latencia p50/p95 en `/predict`.
10. Fijar dependencias con `requirements.in` → `requirements.txt` generado con `pip-compile` y hashes opcionales; controlar versión de modelo spaCy.

## `artifacts/manifest.json` (contrato esperado)

```json
{
  "schema_version": "1.0",
  "model_id": "reviewiq-<commit-short>-<date>",
  "label_index_to_stars": {"0": 1, "1": 2, "2": 3, "3": 4, "4": 5},
  "dataset_repository": "SetFit/amazon_reviews_multi_es",
  "dataset_revision": "<sha-real>",
  "seed": 42,
  "nlp_config": "config.yaml",
  "feature_count": "<numero-medido>",
  "metric_path": "reports/test_metrics.json",
  "python_version": "<version-real>",
  "sklearn_version": "<version-real>",
  "artifact_sha256": "<hash-real>"
}
```

Los marcadores `<...>` son valores pendientes, **no** falsos datos. Guardar `model_id`, versión de config y la métrica que el backend expone.

## Prueba de reproducibilidad

En clon limpio: instalar dependencias fijadas → descargar dataset con acceso legítimo → ejecutar script → verificar artefactos → ejecutar API y frontend → predecir un texto → comparar salida con ejecución directa del pipeline. Documentar diferencias esperables por arquitectura/BLAS.

## Aceptación y commits

- [ ] Modo `quick` usable durante defensa sin fingir que representa 200k.
- [ ] Modo `full` reproducible, sin GPU, con semilla y dependencias fijas.
- [ ] Pipeline completo guarda NLP+TF-IDF+modelo.
- [ ] API no vuelve a ajustar vectorizador ni tiene ruta NLP duplicada.
- [ ] Medidos artefacto, RSS RAM, latencia p50/p95 y tiempo de entrenamiento real.

Commits sugeridos:

- `feat(train): ejecutar entrenamiento completo con una orden`
- `perf(ml): usar tfidf disperso float32 y limitar caracteristicas`
- `feat(artifacts): serializar pipeline e incluir version y hash`
- `test(repro): verificar inferencia identica tras recargar joblib`
- `docs(perf): registrar memoria latencias y tiempos observados`
