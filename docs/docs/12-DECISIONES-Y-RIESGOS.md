# 12 — Registro de decisiones arquitectónicas (ADR) y riesgos

Usar este archivo como el registro que el docente puede examinar para preguntar «¿por qué así?».

## ADR-001: clasificación de 5 clases y no regresión

- **Estado:** propuesta inicial; confirmar en implementación.
- **Razón:** estrellas 1..5 son clases con límites discretos; corpus provee clases; dos algoritmos autorizados por temario.
- **Costo:** no modela directamente que 1↔2 es más cercano que 1↔5; mitigar reportando **MAE ordinal** y confusiones.
- **Alternativa:** regresión lineal y redondeo a 1–5; no elegida por interpretación y rangos.

## ADR-002: TF-IDF disperso, no embedding neuronal

- **Razón:** requerido por PDF, eficiente CPU, reproducible e interpretable.
- **Costo:** dependencia de vocabulario; retos ante sarcasmo/paráfrasis.
- **Alternativa:** BERT; excluido de rúbrica temporal y de restricciones de hardware.

## ADR-003: dos modelos, NB vs regresión logística

- **Razón:** algoritmos del curso, compatibilidad con TF-IDF no negativo, comparación sencilla.
- **Criterio:** Macro-F1 validation, luego coste CPU/latencia como desempate documentado.
- **Sin prometer:** que un modelo ganará antes de entrenar.

## ADR-004: pipeline serializado único

- **Razón:** requerimiento explícito. Evita discrepancias entrenamiento/inferencia.
- **Costo:** conservar Python y bibliotecas compatibles, guardar manifest; cargar Joblib **solo de origen propio**.

## ADR-005: modo quick y full

- **Razón:** defensa en vivo y ordenador sin GPU requieren ciclo de feedback rápido.
- **Límite:** quick no sustituye a métrica final y no debe calcular métricas de test para iterar.

## ADR-006: sin base de datos / sin SaaS en MVP

- **Razón:** el PDF no exige persistencia, usuarios ni cobros; usabilidad y reproducibilidad son más importantes.
- **Futuro:** sistema empresarial puede almacenar resultados con consentimiento y políticas de retención.

## Riesgos

| Riesgo | Impacto | Prevención | Evidencia |
|---|---|---|---|
| Corpus no autorizable para negocio | Crítico comercial | Solo investigación académica; entrenar con datos licenciados para vender en futuro | `13-FUENTES-Y-LICENCIAS.md` |
| Texto castellano de Amazon no representa comercio local | Calidad fuera del dominio | No prometer resultados en modismos bolivianos; futura muestra de validación propia | Informe limitaciones |
| Etiquetas 0–4 mapeadas incorrectamente | Crítico | Unit tests 0→1, 4→5 | `test_models.py`, `test_api.py` |
| Leakage de test / IDF | Crítico académico | Split oficial y Pipeline dentro CV | logs y tests |
| spaCy en cada iteración consume CPU | Alto | comparar en muestra, `nlp.pipe()` lotes, stemming si eficaz | Benchmark |
| CV explota memoria | Alto | sparse float32, `n_jobs=1`, muestra estratificada | Benchmark RAM |
| métricas de modelo desfasadas | Alto | match manifest `model_id` y métricas | test de artefacto/API |
| Demo falla sin Wi-Fi | Alto | entrenar y descargar con antelación; API local y artefactos listos | Prueba offline |
| Contribuciones individuales falsas | Crítico académico | una identidad real por autor, PR revisado honestamente, autorización individual | historial Git |
| Cambios en vivo tardan demasiado | Alto | CLI quick, flags/config y tests rápidos | simulacros |

## Registro de decisiones de implementación

Al desarrollar cada tema, añadir: fecha, autor **real**, hipótesis, experimento, resultados **reales**, decisión y commit. Evitar escribir conclusiones que no estén sustentadas por métricas o por pruebas reproducibles.
