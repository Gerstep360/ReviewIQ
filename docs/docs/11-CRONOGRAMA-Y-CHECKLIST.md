# 11 — Cronograma y puerta de calidad por etapas

**Fechas del documento:** exposición 3 de noviembre de 2026; corte de entrega 2 de noviembre de 2026, 23:59, último commit de `main`. El tag `entrega-final` apunta exactamente al commit entregado. El tiempo restante es reducido: priorizar los requisitos obligatorios sobre extras.

## Entrega incremental sugerida

| Periodo | Meta / tareas | Hito verificable |
|---|---|---|
| 21–22 oct | Consulta sobre trabajo individual, repo y docente colaborador, dataset, licencia | README y datos auditados |
| 23–24 oct | EDA + normalización + tokens + stop words + tests | Notebook + pipeline inicial |
| 25–26 oct | Stem vs lemma, n-gramas, TF-IDF, primeros modelos quick | Comparación de técnicas |
| 27–28 oct | CV, validación, entrenamiento full controlado y artefactos | Modelo real y métricas versionadas |
| 29 oct | FastAPI, health, predict, metrics, trace, pruebas | API real navegable |
| 30 oct | React: predicción, NLP, comparación y errores | Demo end-to-end |
| 31 oct | Pruebas, rendimiento CPU y documentación | Clon limpio reproducible |
| 1 nov | Ensayo de exposición, cambios en vivo, revisión de Git | Simulacro y correcciones |
| 2 nov | Congelar, revisión final, generar tag y push antes de las 23:59 | `entrega-final` |
| 3 nov | Exposición y modificación en vivo | Defender commits reales |

No posponer pruebas, documentación y commits hasta el final; están ponderados en la rúbrica.

## Priorización

**P0, sin esto NO entregar como terminado:** dataset trazable; NLP completo; dos clasificadores; CV/validación/test; serialización; un comando; API y pruebas; front real; README, informe, CONTRIBUCIONES y Git auténtico.

**P1 (si queda tiempo):** panel de n-gramas más detallado, barras de probabilidades mejoradas, datos CSV en lote, benchmarks automatizados, diseño visual elaborado.

**P2 / fuera de alcance:** SaaS multiempresa, autenticación, facturación, scraping en vivo de Amazon, LLM generativo, Jev comercial, BERT, red neuronal entrenada desde cero, integración directa con Amazon o bases de datos innecesarias.

## Checklist maestro de salida

### A. Datos
- [ ] Origen, licencia académica, fecha y SHA reales documentados.
- [ ] 200k / 5k / 5k confirmados desde descarga y mapeo 0..4 → 1..5.
- [ ] EDA con frecuencias, nulos, longitudes, clases y duplicados.
- [ ] CV con semilla y split sin leakage.

### B. NLP
- [ ] Normalización tildes, puntuación, URLs, números, emojis.
- [ ] Tokens y stop words españolas con decisión para negaciones.
- [ ] Stemming y lematización implementados y comparados.
- [ ] 1-gramas vs 1+2-gramas y TF-IDF documentados.
- [ ] Misma implementación en training y API, trazas reales.

### C. Modelos
- [ ] NB y regresión logística entrenados y evaluados.
- [ ] Al menos una búsqueda con CV en train.
- [ ] Macro-F1, accuracy, MAE, matriz, por clase y errores reales.
- [ ] Selección en validation, evaluación test final conservada.
- [ ] Modelos y pipeline reproducibles con un comando y entorno fijado.

### D. Aplicación
- [ ] FastAPI: health, predict, metrics, errores/validaciones, tests.
- [ ] React: estrellas, probabilidades, pasos NLP, comparación ML.
- [ ] Sin predicciones falsificadas ni API generativa como motor.
- [ ] Instalación probada desde cero en PC normal CPU.

### E. Evaluación / Git
- [ ] Docente colaborador, roles reales, ramas y PR auténticos.
- [ ] Commits descriptivos, repartidos, trabajo real y `CONTRIBUCIONES.md` veraz.
- [ ] Preguntas de defensa practicadas; cambio rápido probado.
- [ ] Informe, notebook, slides, README, licencia y declaración de IA.
- [ ] `entrega-final` creado y enviado al repositorio a tiempo.

## Regla de parada

Si a 48 horas de la entrega falta una función P0, congelar P1/P2 y resolver P0, pruebas y documentación. No sacrificar un pipeline auditable por el aspecto de la página.
