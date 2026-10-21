# Fase E — Reproducción y paquetes de inferencia

Implementada según la guía 05, adaptada a Django/DRF y ml/. La selección/test de la Fase D se conservan: después de evaluar test no se vuelve a optimizar el diseño.

## Cambios concretos

- Entrada quick/full desde el corpus fijado hasta un paquete autocontenido de pipeline, manifiesto, métricas y recursos observados.
- Referencia del estado realmente evaluado y reproducción estricta de vocabulario, IDF, coeficientes y parámetros, sin depender de igualdad binaria de Joblib.
- Asociación de métricas históricas solo al mismo estado aprendido; quick usa validation y otro model_id.
- Verificación de integridad y compatibilidad antes de deserializar, estado después de cargar y comprobación de round-trip.
- Predictor reutilizable por proceso, con trazas de las mismas etapas y sin fit ni descargas durante inferencia.
- Benchmark en otro proceso, con frases sintéticas, warm-up y percentiles de una reseña y lotes de cien.
- Script de reproducción en copia aislada con entorno y datos nuevos.

Archivos centrales: ml/training/reproduce.py, ml/training/reference.py, entrada train.py, ml/inference/{artifacts,predictor,probes,benchmark}.py, scripts/verify_reproduction.py y tests/test_artifacts.py. Referencia y evidencia en reports/; binarios/corpus fuera de Git.

## Comandos y verificaciones ejecutadas

```text
venv/Scripts/python.exe -m ml.training.reference
  reviewiq-8f0ef24251ae5522

venv/Scripts/python.exe -m unittest discover -s tests -p test_artifacts.py -v
  Ran 6 tests
  OK

venv/Scripts/python.exe -m pip check
  No broken requirements found.

venv/Scripts/python.exe -m ml.training.train --mode quick --seed 42
  model_id: reviewiq-quick-3ac8f79ec79a7319
  mode: quick
  feature_count: 36737
  test_evaluation_repeated: false

venv/Scripts/python.exe scripts/verify_reproduction.py
  Copia aislada creada sin corpus, artefactos ni entorno previo.
  No broken requirements found.
  Ajustando full: 197572 filas, lemmatization...
  model_id: reviewiq-8f0ef24251ae5522
  feature_count: 50000
  test_evaluation_repeated: false
  Reproducción limpia verificada; reports/reproducibility.json

venv/Scripts/python.exe -m ml.inference.benchmark --package-dir ml/artifacts/full
  calls: 30, p50_ms: 9.21849999576807, p95_ms: 11.37524500954896
```

Las seis pruebas se enfocan en identidad frente a cambios de serialización/pesos, corrupción antes de Joblib, identidad modelo/métricas, carga única y ausencia de fit/red, rechazo de falsas métricas finales y evidencia histórica inmutable. Usan datos sintéticos; la reproducción real es una verificación distinta.

Quick se ejecutó realmente con 20.000 reseñas: 61,36 s de pared, 419,63 MiB de pico RSS de construcción y Macro-F1 validation 0,478469, accuracy 0,481 y MAE 0,6872. No son métricas finales. Se documenta el experimento en reports/quick_reproduction.json.

## Resultado de la reconstrucción aislada

La copia se creó con archivos listados por Git, incluidos los cambios de esta fase; no tenía corpus, checkpoint ni entorno anterior. Se creó otro venv, se instalaron las dependencias fijadas y se descargó el corpus de la revisión registrada. Full ajustó 197.572 filas sin reutilizar datos preparados, con 635,16 s de pared, 624,42 s de CPU y 1.205,18 MiB de pico RSS. No se repitió CV ni selección.

Se obtuvo exactamente la huella del estado evaluado:

```text
model_id: reviewiq-8f0ef24251ae5522
model_state_sha256: acb4bc2199689a83debd60cf54a127dfcffb07bdc5c20f7fe14e471cdcdac18b
path: retrained_frozen_parameters
data_cache_verified: false
model_state_matches_evaluated: true
test_evaluation_repeated: false
```

Las probabilidades de diez frases sintéticas coincidieron dentro de rtol=1e-7 y atol=1e-8. Los archivos model_selection.json, test_metrics.json y final_test_ledger.json conservaron sus bytes en la copia. Evidencia completa: reports/reproducibility.json. No se ejecutó final_test en esta fase.

El pipeline reconstruido y verificado se reexportó en el workspace con los metadatos finales del manifiesto, sin volver a ajustar. El paquete final tiene 1.526.934 bytes y conserva la misma huella aprendida. Se verificaron su round-trip, diez probabilidades de referencia y reutilización del predictor con fit y red bloqueados mediante mocks. Manifiesto e informe de construcción: reports/deployment_manifest.json y reports/full_build.json. El checkpoint original de D permanece intacto.

El benchmark del paquete final registró p50/p95 individual de 9,22/11,38 ms, lote de cien de 96,24/101,14 ms y pico RSS de inferencia de 245,68 MiB. Las medidas y el alcance están en RENDIMIENTO.md y reports/performance.json. Son medidas locales, todavía no de HTTP.

## Requisitos cubiertos y límites

Se usa CPU, un proceso por entrenamiento y un hilo de cálculo. TF-IDF permanece disperso; no se densifican matrices. Las versiones se mantienen fijadas en requirements.txt y el modelo español en su wheel con checksum.

API/frontend no se implementan ni se ensayan en esta fase. Los percentiles son de Predictor.predict local, no de HTTP. Se usan treinta mediciones individuales y siete de lote; no se presentan como garantías de producción. La reconstrucción exacta se exige en el entorno registrado; diferencias numéricas de otra plataforma no se ignoran para reutilizar métricas.

La siguiente fase es F: endpoints Django/DRF con carga del paquete una vez por proceso y validaciones de entrada/salida. El uso de asistencia IA se refleja en el informe y contribuciones.

Commit del bloque: feat(artifacts): reproducir modelo congelado y verificar paquetes de inferencia.
