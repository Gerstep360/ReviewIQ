# 02 — Responsabilidad: adquisición de datos y EDA

## Fuente y cardinalidad

- Dataset de uso académico: https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es
- Files: https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es/tree/main
- Splits publicados: `train`=200.000, `validation`=5.000, `test`=5.000 (verificar al descargar, registrar revisión o commit exacto de Hugging Face).
- Campos **observados**: `id` (identificador), `text` (reseña), `label` (entero 0–4), `label_text`. **No introducir** `label_text` como entrada: filtración directa de la etiqueta.
- `stars = int(label) + 1` **solo para interfaz/informe**. El algoritmo aprende 0–4 para mantener las etiquetas originales.
- Corpus fuente: *Multilingual Amazon Reviews Corpus*, Keung et al. (EMNLP 2020). Licencia de investigación académica con **restricciones de uso comercial** (ver `13`).

## Implementación por pasos

1. Crear `src/data/download.py`: `load_dataset("SetFit/amazon_reviews_multi_es", revision=REVISION_PIN)`; comprobar los tres splits y esquema; guardar metadatos y hash/revisión de origen. Confirmar si la versión instalada de `datasets` requiere forma alternativa de lectura JSONL; documentar decisión.
2. Guardar solo campos necesarios en preparación (`id`, `text`, `label`), sin datos sensibles ni atributos no usados.
3. Auditar nulos, strings vacíos, tipos, etiquetas fuera de 0..4, textos duplicados, solapamiento de ID y textos entre splits, distribución por clase.
4. Registrar: longitud caracteres/tokens, palabras frecuentes por clase y globales, histograma de longitudes, proporción de textos con números, URL, emojis, tildes.
5. Construir `notebooks/01_eda.ipynb` + `reports/eda_summary.json` y figuras (sin inventar histogramas).
6. Mantener los splits de origen. **No recombinar train+validation+test**, y nunca optimizar decisiones con test. CV **estratificada y semilla 42** solo en train; validar que los splits preservan clases de forma aproximadamente equilibrada.
7. Duplicados: registrar la tasa; si hay contaminación de entrenamiento respecto a validación/test, documentar tratamiento prudente (por ejemplo excluir el duplicado de `train`, manteniendo test intacto). Nunca basar limpieza en los resultados predictivos sobre test.
8. El dataset original es esencialmente balanceado por estrellas; **verificar** el balance de la copia local. Si hay desbalance residual, justificar el tratamiento o por qué no es necesario.

## Ejemplo de lectura para el futuro código

```python
from datasets import load_dataset

ds = load_dataset("SetFit/amazon_reviews_multi_es")  # en producción fijar revision=SHA
assert {"train", "validation", "test"}.issubset(ds)
assert {"id", "text", "label"}.issubset(ds["train"].column_names)
assert set(ds["train"].unique("label")) == set(range(5))
print({split: len(part) for split, part in ds.items()})
```

**Este fragmento es una referencia para implementar, no evidencia de que ya se descargaron datos.** No poner una SHA inventada: obtener la real antes de fijarla.

## Requisitos de calidad

- No descargar a Git miles de reseñas si las condiciones prohíben redistribución; subir script que reobtiene los datos desde la fuente, instrucciones y sumas/verificación.
- Registrar URL, autor, fecha de acceso, commit de HF, tamaños confirmados, licencia, campos y transformaciones.
- Nunca usar estrellas «adivinadas» para etiquetar datos nuevos del conjunto de prueba.
- Preparar pocos ejemplos anonimizados para el informe y no intentar reidentificar autores.

## Archivos esperados

`src/data/download.py`, `src/data/validate.py`, `src/data/eda.py`, `notebooks/01_eda.ipynb`, `reports/eda_summary.json`, `docs/DATASET.md`, tests `tests/test_data.py`.

## Aceptación verificable

- [ ] Script descarga origen fijado y confirma esquema/splits.
- [ ] Distribución 5 clases, nulos, longitudes, palabras frecuentes y duplicados documentados.
- [ ] Balance comprobado y CV estratificada planificada sin usar test.
- [ ] Licencia y procedencia presentes.
- [ ] EDA ejecutable sin alterar los splits de origen.

## Ejemplos de commits (solo tras realizar cambios reales)

- `feat(data): implementar descarga reproducible de reseñas en español`
- `test(data): validar columnas etiquetas y particiones originales`
- `feat(eda): generar distribucion de clases y auditoria de duplicados`
- `docs(dataset): documentar origen licencia y decisiones de limpieza`
