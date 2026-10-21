# Modelado ML — Fase D

El problema es clasificación multiclase ordinal: labels internos 0–4, estrellas públicas 1–5. Se usan exclusivamente MultinomialNB y LogisticRegression; la predicción mayoritaria se calcula sin entrenar otro clasificador.

## Protocolo fijado antes de test

1. Cribado de ocho combinaciones: dos clasificadores, stemming/lematización y unigramas/uni+bigramas, con muestra estratificada de 20.000 filas de train preparado y semilla 42. Se reutilizan transformaciones sin objetivos aprendidos; TF-IDF se ajusta solo con esa muestra.
2. Elegir la variante NLP de cada clasificador con Macro-F1 de validation, seguido de menor MAE en empates. Las 5.000 filas de validation sirven para esta selección, no para entrenar.
3. GridSearchCV de tres folds estratificados, con shuffle y semilla 42, exclusivamente sobre la misma muestra de train. NB alpha: 0,1 / 1 / 2; LR C: 0,5 / 1 / 2. NLP y TF-IDF están dentro de Pipeline: cada fold tiene su propio vocabulario e IDF. El caché temporal se identifica por filas/etiquetas/parámetros y solo evita repetir el mismo fit de un fold entre valores del clasificador.
4. Reajustar ambos finalistas con las 197.572 filas de train preparado. LR usa lbfgs y máximo 500 iteraciones; un ConvergenceWarning detiene el flujo antes de test.
5. Comparar ambos finalistas sobre validation y elegir el campeón por mayor Macro-F1, menor MAE y nombre/configuración estable en empate exacto. La regla está en config.json y en reports/selection_protocol.json antes del entrenamiento.
6. Congelar parámetros, pipeline serializado, hashes y regla argmax. Comprobar round-trip con textos de validation. No se mezcla train con validation.
7. Evaluar solo ese campeón una vez sobre las 5.000 filas del test original fijado. La selección ya está cerrada: esos resultados no se usan para retocar el modelo.

No se hace una búsqueda combinatoria de todas las morfologías, n-gramas e hiperparámetros en cada fold: el cribado previo mantiene acotado el coste en CPU. Las métricas de validation son métricas de selección, no una estimación independiente del rendimiento final.

## Reproducción

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42
.\venv\Scripts\python.exe -m ml.evaluation.final_test
```

El primer comando no abre test. Genera los cribados, CV, comparación de finalistas, checkpoint local en ml/artifacts/reviewiq_pipeline.joblib y selección congelada en reports/model_selection.json. El segundo comprueba hashes de artefacto, código y configuración; reserva un registro exclusivo antes de leer test y guarda su única evaluación.

La reserva también bloquea reintentos tras un fallo: no se elimina automáticamente. Si ya existe final_test_ledger.json o test_metrics.json, no se sobrescribe la selección full ni se vuelve a puntuar test. Para regenerar la figura sin recalcular predicciones:

```powershell
.\venv\Scripts\python.exe -m ml.evaluation.final_test --render-only
```

El modo quick ajusta finalistas con la muestra, guarda informes separados en reports/quick y un checkpoint quick distinto. Sus resultados son experimentales; nunca consulta test ni reemplaza el campeón full.

## Métricas y análisis

Se registran Macro-F1, accuracy, MAE en estrellas, precisión/recall/F1/soporte por clase, matriz 5×5 y distribución de distancia ordinal. Se validan las clases en orden 0–4 y que las probabilidades sean finitas, no negativas y sumen aproximadamente uno. Son estimaciones del modelo sin garantía de calibración.

El análisis de errores conserva confusiones, rasgos descriptivos no excluyentes y posiciones locales de casos para revisión. No publica reseñas ni IDs del corpus. Texto corto significa hasta ocho palabras; negación y conectores pero/aunque se detectan por términos explícitos. Estos grupos no prueban causas como sarcasmo: la interpretación cualitativa debe distinguir observación de hipótesis.

El entrenamiento mide pared, CPU y pico RSS muestreado cada 50 ms del proceso completo, incluyendo datos y cachés. Se usa un proceso y un hilo de cálculo. No son mediciones de la API ni garantías para otro equipo.

## Evidencia y alcance

- reports/model_screening.csv/json: ocho combinaciones iniciales.
- reports/cv_results.json: candidatos de hiperparámetros y scores por fold.
- reports/model_comparison.csv/json: dos finalistas full y línea base mayoritaria.
- reports/model_selection.json: campeón y parámetros congelados antes de test.
- reports/test_metrics.json y final_test_ledger.json: única evaluación final y trazabilidad.
- reports/validation_confusion_matrix.png y confusion_matrix.png: matrices de selección y test.
- reports/errors.md: análisis observado, sin textos del corpus.
- docs/FASE-D-MODELADO.md: comandos, resultados y alcance de esta ejecución.

El checkpoint binario queda fuera de Git; se entrega el código que lo regenera. El empaquetado y manifiesto de despliegue corresponden a la fase E. No hay API ni frontend conectados en esta fase.

Fuentes de implementación: [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html) y [Pipeline](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) de scikit-learn. Las versiones están fijadas en requirements.txt.
## Resultados de esta ejecución

Campeón: **LogisticRegression, C=1, lematización y uni+bigramas**, ajustado solo con las 197.572 filas de train preparado. La selección por validation obtuvo Macro-F1 0,515025, frente a 0,508795 de MultinomialNB(alpha=2) con stemming+uni/bigramas.

La única evaluación del campeón sobre 5.000 reseñas test produjo **Macro-F1 0,513135**, **accuracy 0,5154** y **MAE 0,6128 estrellas**. El F1 de 3 estrellas es 0,395918; los extremos son más fáciles que las valoraciones intermedias. Hay 502 predicciones con distancia de al menos dos estrellas. Son resultados observados de este prototipo académico, sin cambios posteriores para mejorarlos.

El modelo congelado se identifica como reviewiq-8f0ef24251ae5522. El entrenamiento completo tardó 19,57 minutos en el equipo registrado, con 1.311,70 MiB de pico RSS muestreado. Las métricas por clase, matrices, análisis y límites están en los informes; los comandos completos se registran en FASE-D-MODELADO.md.