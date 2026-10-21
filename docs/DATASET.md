# Dataset: Amazon Reviews Multi en español

Fase B ejecutada el 21 de octubre de 2026. Resultados observados en `reports/eda_summary.json`, sin entrenamiento de modelos.

## Origen, licencia y descarga

- Espejo: [SetFit/amazon_reviews_multi_es](https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es).
- Revisión fijada: `16015418b488c9186fce74b058877ea939ca934d`.
- Publicación original: Keung, Lu, Szarvas y Smith (2020), [The Multilingual Amazon Reviews Corpus](https://aclanthology.org/2020.emnlp-main.369/).
- Condiciones examinadas: [documentación oficial de AWS, sección License](https://github.com/awslabs/open-data-docs/blob/main/docs/amazon-reviews-ml/README.md#license). Uso limitado a investigación académica; no redistribuir, revender, usar comercialmente ni intentar identificar autores.
- Fecha UTC de verificación, fechas locales de los archivos, URLs exactas, tamaños y SHA-256: `reports/dataset_manifest.json`. Los hashes de referencia se fijan en `config.json`.

Se leen directamente los JSONL de la revisión fijada mediante la biblioteca estándar, alternativa admitida por la guía `02`, en lugar de añadir `datasets.load_dataset` y Arrow. No se ejecutan scripts del espejo. La descarga inicial también se cotejó con los IDs Git de validation/test y el SHA-256 LFS de train publicados por la API de Hugging Face.

Cada uso verifica tamaño y SHA-256, incluso si el archivo ya existe. Una descarga temporal solo reemplaza el destino después de verificar. Una caché alterada genera error; `python -m ml.data.download --force` permite reobtenerla.

| Partición | Filas originales | Bytes | Filas preparadas |
|---|---:|---:|---:|
| train | 200.000 | 43.777.905 | 197.572 |
| validation | 5.000 | 1.088.600 | 5.000 |
| test | 5.000 | 1.097.228 | 5.000 |

## Esquema y balance

El origen contiene `id`, `text`, `label` y `label_text`. Se valida cada fila: ID y texto deben ser strings no vacíos; label debe ser entero de 0 a 4, rechazando booleanos. Se encontraron cero registros inválidos. Ante una fila inválida el proceso se detiene, mostrando archivo y línea sin su contenido.

La preparación conserva solo `id`, `text` y `label`. `label_text` se excluye por filtración directa de etiqueta; los modelos futuros recibirán solo `text` e `id` servirá para auditoría. Conversión externa: `stars = label + 1`.

Cada clase original tiene 40.000 filas de train y 1.000 de cada holdout: 20 % por clase. Tras la limpieza, train contiene 39.689 / 39.788 / 39.607 / 39.209 / 39.279 filas por etiqueta 0–4. La diferencia máxima es de 579 filas, menos de 0,3 puntos porcentuales del total preparado; no se aplicó remuestreo ni ponderación.

## Duplicados y política de preparación

Se auditan IDs, texto exacto y una identidad de texto adicional: `casefold` y espacios colapsados, con SHA-256. Conserva tildes y puntuación; no transforma la entrada del modelo ni detecta paráfrasis.

| Partición | Filas repetidas por texto exacto | Filas repetidas por texto normalizado | Grupos normalizados con etiquetas contradictorias |
|---|---:|---:|---:|
| train | 1.736 | 1.922 | 427 |
| validation | 5 | 7 | 1 |
| test | 6 | 6 | 1 |

No se encontraron IDs repetidos dentro de las particiones ni compartidos entre ellas. Se observaron 75 textos normalizados distintos compartidos entre train/validation, 61 entre train/test y 9 entre validation/test. Estos conjuntos se superponen: no se deben sumar como si fueran filas distintas.

La preparación aplica esta política fija, sin resultados predictivos:

1. Excluir de train filas cuyo ID o texto normalizado esté en validation o test: 671 filas.
2. Excluir todas las filas restantes de grupos de train con etiquetas contradictorias: 1.313 filas, evitando elegir una etiqueta arbitraria.
3. Conservar la primera aparición de cada ID/texto restante de train: 444 filas adicionales excluidas.

Quedan **197.572 filas de train**. La auditoría posterior confirma cero IDs y textos normalizados compartidos entre train preparado y los holdouts. Los archivos crudos no se modifican.

Validation y test conservan filas, orden, texto y etiquetas; solo se proyectan columnas. Sus duplicados internos y los 9 textos compartidos se documentan como limitación de independencia por contenido, sin alterar las particiones oficiales.

## EDA y reproducción

El notebook `notebooks/01_EDA.ipynb` ejecuta el mismo módulo que la CLI. El informe incluye clases, nulos/validación, longitudes, palabras globales y por clase de train, duplicados y proporciones de números, URLs, tildes/ñ y emojis. Las tres figuras agregadas están en `reports/figures/`.

En train original: media de 151,3029 caracteres, mediana de 120, p95 de 391 y rango 16–3.086; media de 27,6202 tokens alfabéticos Unicode. Los límites de longitud observados en este espejo difieren de la descripción del corpus original: se conservan y reportan los valores medidos.

Los tokens de EDA son secuencias alfabéticas Unicode con casefold, sin quitar stop words. La detección de emojis por rangos Unicode es aproximada. Las palabras frecuentes se calculan solo sobre train. En validation/test se realiza auditoría descriptiva y de identidad; no se selecciona vocabulario, preprocesamiento ni hiperparámetros con test.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ml.data.eda
```

El corpus crudo y preparado permanece en `ml/data/raw/` y `ml/data/processed/`, ignorados por Git. Los informes no publican reseñas ni IDs. La futura CV será estratificada, con shuffle y semilla 42, solo sobre train preparado; aún no se ejecutó. No se entrenaron modelos ni se evaluó test.