# Fase B — Datos y análisis exploratorio

Estado: implementada y ejecutada el 21 de octubre de 2026. La instrucción del responsable autoriza commit y push después de verificar cada bloque.

## Alcance y decisiones

Se implementó en `ml/data/`, según `ARQUITECTURA.md`, adaptando el antiguo `src/data/` de las guías. Se completa la configuración compartida con semilla 42 y un proceso de CPU; las dependencias se fijan con pip-tools en Windows/Python 3.11. No se implementaron entrenamiento, NLP de producción, endpoints ni interfaz de predicción.

La descarga JSONL usa revisión y hashes reales fijados. El EDA valida esquema, clases, faltantes, longitudes, palabras, duplicados y solapamientos; produce informes y tres figuras. La preparación limpia solo train. Origen, licencia y límites: `DATASET.md`.

Archivos: `config.json`, `ml/config.py`, `ml/data/{download,validate,prepare,eda}.py`, archivos `requirements*.in/txt`, `notebooks/01_EDA.ipynb`, `scripts/run_eda_notebook.py`, `tests/test_data.py`, `reports/` y documentación.

## Comandos y resultados reales

```text
venv/Scripts/python.exe -m ml.data.download --force
  revision: 16015418b488c9186fce74b058877ea939ca934d
  verified_files: train, validation, test

venv/Scripts/python.exe -m ml.data.eda
  raw_rows: train=200000, validation=5000, test=5000
  prepared_train: 197572
  report: reports/eda_summary.json

venv/Scripts/python.exe -m unittest discover -s tests -p test_data.py -v
  Ran 5 tests
  OK

venv/Scripts/python.exe scripts/run_eda_notebook.py
  Notebook ejecutado: notebooks/01_EDA.ipynb

venv/Scripts/python.exe -m pip check
  No broken requirements found.
```

Las cinco pruebas, sin red ni corpus externo, cubren esquema y exclusión de label_text, auditoría de duplicados, limpieza sin modificar holdouts ni crudos, detección de alteraciones del mismo tamaño por SHA-256 y configuración fijada.

El notebook se ejecutó con el intérprete del entorno mediante un kernel temporal. La auditoría posterior comprueba cero IDs/textos normalizados compartidos entre train preparado y los holdouts. La evidencia se conserva en los informes generados; las figuras se revisaron visualmente.

## Requisitos cubiertos y pendientes

- Fuente, revisión, fecha, tamaños, hashes y restricciones documentados.
- EDA de clases, longitudes, palabras, nulos y duplicados ejecutado.
- Splits originales y balance verificados; futura CV estratificada en train con semilla 42 documentada.
- Corpus fuera de Git; notebook e informes solo contienen agregados.

La validación se detiene en la primera fila inválida. La identidad de texto y la detección de emojis tienen límites documentados. Persisten duplicados internos y 9 textos compartidos entre validation/test porque se conservaron los holdouts.

No se probaron PostgreSQL, API, frontend ni entrenamiento en esta fase. El mapa del PDF se sigue a través de los documentos disponibles; el PDF original no se recibió en esta sesión. La siguiente fase es C: pipeline NLP reutilizable en `ml/nlp/`.

Commit del bloque: `feat(data): descargar validar y auditar resenas en espanol`.