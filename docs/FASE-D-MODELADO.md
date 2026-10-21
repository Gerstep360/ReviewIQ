# Fase D — Modelado ML

Implementación en ml/training y ml/evaluation, conforme a ARQUITECTURA.md. Se usa clasificación de cinco clases, con labels 0–4 y estrellas 1–5. Los únicos clasificadores aprendidos son MultinomialNB y LogisticRegression.

## Trabajo realizado

- Cribado de ocho combinaciones de modelo, morfología y n-gramas sobre 20.000 filas estratificadas de train preparado.
- CV estratificada de tres folds en la misma muestra, con semilla 42, ajustando alpha y C. Cada fold ajusta su NLP y TF-IDF dentro de Pipeline.
- Ajuste de los dos finalistas con las 197.572 filas de train preparado, manteniendo validation y test fuera del entrenamiento.
- Selección con validation mediante un criterio fijado antes de test: mayor Macro-F1, luego menor MAE y desempate estable.
- Checkpoint local, verificación Joblib y selección congelada con hashes de configuración, código y artefacto.
- Evaluación final única con registro exclusivo persistente; ni un fallo deja habilitado un reintento automático.
- Métricas por clase, matriz de confusión, errores ordinales y análisis descriptivo de casos sin publicar el corpus.

Código y configuración: ml/training/{pipelines,tune,train,export}.py, ml/evaluation/{evaluate,final_test,errors}.py y config.json. Ver MODELOS.md para decisiones, límites y comandos de uso.

## Verificaciones reales

```text
venv/Scripts/python.exe -m unittest discover -s tests -p test_models.py -v
  Ran 6 tests
  OK

venv/Scripts/python.exe -m pip check
  No broken requirements found.
```

Las seis pruebas usan datos sintéticos, sin red ni corpus externo. Cubren el mapeo de etiquetas, métricas ordinales y cinco clases, probabilidades válidas, vocabulario aislado por fold, selección sin scores de test, bloqueo ante reserva incompleta y una única evaluación final sintética.

El entrenamiento y la CV requeridos por la guía son experimentos reales, separados de estas pruebas pequeñas. No se ejecutaron pruebas de frontend, API ni PostgreSQL en esta fase. El modo quick está implementado, pero la ejecución académica de esta fase utiliza full.

## Evidencia de requisitos

Los informes model_screening, cv_results y model_comparison registran candidatos, parámetros, métricas y procedencia; model_selection registra el campeón antes de test; test_metrics y final_test_ledger conservan su evaluación final. Las matrices y errors.md permiten examinar errores reales sin distribuir reseñas.

La selección por validación usa las mismas 5.000 reseñas en varias etapas, por lo que sus métricas no son una estimación independiente. La CV de búsqueda usa 20.000 filas, no todo train; ambos finalistas se reajustan luego con train completo. Las probabilidades no están calibradas. Los duplicados entre validation/test documentados en DATASET.md se conservan como limitación.

La fase E queda pendiente para regenerar el artefacto congelado sin volver a seleccionar ni puntuar test, completar su manifiesto de despliegue y verificar reproducción desde una instalación limpia. El checkpoint y los cachés temporales permanecen fuera de Git.

Commit del bloque: feat(ml): comparar modelos con cv y congelar evaluacion final.
## Resultados de búsqueda en train

CV de tres folds sobre la muestra estratificada de 20.000 filas, sin usar validation ni test como folds:

| Modelo | Variante preseleccionada | Mejor parámetro | Macro-F1 medio CV |
|---|---|---|---:|
| MultinomialNB | stemming + (1,2) | alpha=2 | 0,478621 |
| LogisticRegression | lematización + (1,2) | C=1 | 0,479923 |

Se evaluaron tres valores por clasificador y tres folds: 18 ajustes de hiperparámetros en total. Los registros de las particiones de cada fold muestran cero posiciones compartidas entre su parte de ajuste y su parte de evaluación. Los scores individuales y su desviación están en reports/cv_results.json.
## Ejecución full y evaluación final

Comandos reales adicionales:

```text
venv/Scripts/python.exe -m ml.training.train --mode full --seed 42
  model_id: reviewiq-8f0ef24251ae5522
  champion: LogisticRegression
  mode: full
  test_accessed: false

venv/Scripts/python.exe -m ml.evaluation.final_test
  model_id: reviewiq-8f0ef24251ae5522
  macro_f1: 0.5131349211771471
  accuracy: 0.5154
  mae_stars: 0.6128

venv/Scripts/python.exe -m ml.evaluation.errors
  errors.md
```

| Finalista full | Variante | Parámetro | Macro-F1 validation | Accuracy validation | MAE validation |
|---|---|---|---:|---:|---:|
| MultinomialNB | stemming + (1,2) | alpha=2 | 0,508795 | 0,5138 | 0,6350 |
| LogisticRegression | lematización + (1,2) | C=1 | 0,515025 | 0,5182 | 0,6040 |

Ambos modelos usan 197.572 filas de train y vocabularios de 50.000 rasgos. LR convergió en 325 iteraciones, sin ConvergenceWarning. El checkpoint del campeón se serializó y sus probabilidades se conservaron al recargarlo. Identificador: reviewiq-8f0ef24251ae5522; tamaño local: 1.526.931 bytes.

El experimento completo tardó 1.174,50 s de pared (19,57 minutos) y 1.166,19 s de CPU, con pico RSS muestreado de 1.311,70 MiB. Incluye cribado, CV, ambos ajustes full y validación; no es el tiempo aislado del clasificador ni incluye la evaluación final separada.

La selección se congeló antes de abrir test. El registro final_test_ledger.json conserva inicio, finalización y hashes del checkpoint, selección y métricas. Su estado es complete. Se comprobaron las probabilidades y el orden de clases en las 5.000 filas de test. No se reajustó ningún parámetro después de observar estos resultados.

Test: 2.577 aciertos de 5.000, Macro-F1 0,513135, accuracy 51,54 % y MAE 0,6128 estrellas. Hay 1.921 errores de una estrella y 502 de al menos dos. La clase más difícil es 3 estrellas, con F1 0,395918; la distinción entre valoraciones intermedias sigue siendo una limitación.

Los informes incluyen precisión/recall/F1/soporte por clase y matrices 5×5. Se revisaron visualmente ambas figuras. El análisis de errores incorpora cuatro casos reales de validation examinados mediante paráfrasis, sin publicar sus textos ni IDs; se distinguen observaciones de hipótesis. No se afirma una revisión humana que no esté documentada.