# Contribuciones — ReviewIQ

Modalidad de desarrollo: individual. La autoría real se consulta en Git; no se añaden nombres al mensaje de commit ni se simulan revisiones de compañeros. La autorización académica de esta modalidad no está documentada en el repositorio.

## Trabajo realizado

- Arquitectura inicial: documentación de las capas Django/DRF, React, PostgreSQL y ML; registro del esqueleto existente y de las carpetas reservadas.
- Configuración inicial: exclusión de entornos, secretos, corpus y artefactos generados; variables de entorno para Django y PostgreSQL.
- Fase B: descarga de JSONL con revisión y SHA-256 fijados, validación de esquema, auditoría de duplicados y preparación de train sin solapamiento con los conjuntos reservados. Evidencia: `ml/data/`, `config.json` y `reports/`.
- EDA: estadísticas y figuras agregadas de las particiones originales, notebook ejecutado y cinco pruebas de datos sin red. Evidencia: `notebooks/01_EDA.ipynb`, `tests/test_data.py` y `docs/FASE-B-DATOS-EDA.md`.
- Fase C: pipeline NLP español clonable y serializable, traza compartida, stop words y negaciones, stemming/lematización y TF-IDF. Comparación experimental de cuatro variantes sobre train/validation con tiempos y RAM medidos. Evidencia: `ml/nlp/`, `tests/test_nlp.py`, `reports/nlp_comparison.*` y `docs/FASE-C-PIPELINE-NLP.md`.
- Fase D: comparación de los dos clasificadores, cribado de ocho combinaciones, CV estratificada sin filtraciones, ajuste full con train preparado, selección por validación y evaluación final protegida. Evidencia: `ml/training/`, `ml/evaluation/`, `tests/test_models.py` y los informes de modelos.
- Fase E: paquetes quick/full con manifiesto, hashes, referencia del estado evaluado, loader reutilizable y round-trip; benchmark local y reproducción en copia aislada con instalación y corpus nuevos. Evidencia: `ml/inference/`, `ml/training/reproduce.py`, `scripts/verify_reproduction.py`, seis pruebas de artefactos y `docs/FASE-E-REPRODUCIBILIDAD.md`.
- Fase F: API Django/DRF de predicción, estado, métricas y traza con el paquete de E; validaciones, límites, errores en español, CORS y Swagger local. Ocho pruebas enfocadas y smoke HTTP real con tiempos/RAM observados. Evidencia: `backend/api/`, `backend/apps/`, `tests/test_api.py`, `scripts/check_api.py`, `reports/api_smoke.json` y `docs/FASE-F-BACKEND.md`.
- Fase G: interfaz React/TypeScript con cuatro vistas conectadas a la API real, diseño responsive, validaciones, cancelación/timeout, errores y reintento. Seis pruebas enfocadas y un recorrido de navegador en escritorio/móvil sobre el build, con capturas inspeccionadas. Evidencia: `frontend/`, `reports/frontend_smoke.json`, `reports/figures/web-*.png` y `docs/FASE-G-FRONTEND.md`.
- Las especificaciones restantes son planificación, no evidencia de funcionalidades terminadas.

El commit inicial permite consultar estos cambios con `git log --reverse` y `git show <hash>`.

## Asistencia de IA

Codex ayudó a revisar la documentación y preparar la configuración, el commit inicial y el código, las pruebas, el diseño y los informes de las fases B, C, D, E, F y G. Las estadísticas y métricas provienen de ejecutar el código sobre los datos registrados. El informe técnico registra esta asistencia; no se atribuye una revisión humana que no esté documentada.

## Evidencia

Las verificaciones realmente ejecutadas y sus resultados se registran en el cuerpo de cada commit. El historial conserva los autores y fechas reales.
