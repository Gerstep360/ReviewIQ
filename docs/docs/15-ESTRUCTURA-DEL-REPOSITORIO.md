# 15 — Estructura objetivo del repositorio de código ReviewIQ

El paquete de especificaciones que recibes NO es el código implementado. Al empezar a programar, construir esta estructura (las carpetas de informes/artefactos nacen al ejecutarse scripts, no necesitan inventarse):

```text
reviewiq/
├── README.md                          # ejecución real desde cero
├── CONTRIBUCIONES.md                 # autores reales y hashes
├── .gitignore                        # omitir datos restringidos y secretos
├── requirements.in
├── requirements.txt                  # lock real de pip-compile
├── config.yaml                       # configuración versionada
├── pyproject.toml                    # herramientas y tests Python
├── data/
│   ├── README.md                     # descarga legítima, licencia, revisión
│   ├── raw/                          # IGNORADO por Git
│   └── processed/                    # IGNORADO por Git
├── notebooks/
│   └── 01_eda.ipynb
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py
│   │   ├── validate.py
│   │   └── eda.py
│   ├── nlp/
│   │   ├── normalize.py
│   │   ├── tokenize.py
│   │   ├── stopwords_es.py
│   │   ├── morphology.py
│   │   ├── pipeline.py
│   │   └── trace.py
│   └── models/
│       ├── train.py                 # -m src.models.train --mode quick|full
│       ├── evaluate.py
│       └── export.py
├── artifacts/
│   ├── manifest.json               # texto exportable
│   └── reviewiq_pipeline.joblib     # solo si licencia y tamaño lo permiten
├── api/
│   ├── main.py
│   ├── schemas.py
│   ├── services/predictor.py
│   └── routes/{health,predict,metrics,nlp}.py
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api/client.ts
│       ├── pages/
│       ├── components/
│       └── tests/
├── tests/
│   ├── test_data.py
│   ├── test_nlp.py
│   ├── test_models.py
│   ├── test_artifacts.py
│   └── test_api.py
├── reports/
│   ├── eda_summary.json
│   ├── nlp_comparison.csv
│   ├── model_comparison.csv
│   ├── test_metrics.json
│   └── confusion_matrix.png
├── docs/
│   ├── DATASET.md
│   ├── NLP_DECISIONS.md
│   ├── INFORME_TECNICO.md          # informe tecnico con resultados reales
│   ├── DECISIONES.md
│   └── diapositivas/                # preparar presentación real
└── .github/pull_request_template.md
```

## Partes que dependen de las evidencias

- `artifacts/reviewiq_pipeline.joblib`: el PDF admite subir el modelo **o el script que lo regenere**; si la licencia, tamaño o seguridad impiden publicar binarios, entregar el script y comprobar que funciona desde cero.
- `reports/` contendrá números generados por ejecución real. No subir métricas generadas manualmente.
- `data/raw` y `data/processed` deben estar en `.gitignore` por derechos y tamaño; incluir instrucciones de descarga y no subir las reseñas completas.
- `src/nlp/` debe ser importable tanto por entrenamiento como por backend (en especial para cargar Joblib sin errores de importación).

## Hitos de integración

1. Crear archivo vacío únicamente si la fase lo necesita; no crear 50 carpetas con código simulado.
2. Tests pasan sin necesidad de iniciar frontend.
3. El artefacto carga en una instalación limpia con el mismo lockfile.
4. La API reproduce el pipeline real.
5. React muestra información real de API y CSV solo si se implementó.

## Commits organizativos de ejemplo

- `chore(repo): organizar codigo en modulos de datos nlp modelos api y frontend`
- `docs(readme): detallar instalacion reproducible en pc sin gpu`
- `test(e2e): verificar entorno limpio y pipeline hasta la interfaz`
