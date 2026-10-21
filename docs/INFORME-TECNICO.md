# Informe técnico — avance

Documento parcial. La arquitectura y las fases B (datos/EDA), C (pipeline NLP), D (modelado ML) y E (reproducción/artefactos) están implementadas. Se completará con la integración del sistema.

Fuente, licencia y preparación: `DATASET.md`. Comandos y resultados: `FASE-B-DATOS-EDA.md`, `FASE-C-PIPELINE-NLP.md` y `FASE-D-MODELADO.md`. Las estadísticas proceden de ejecuciones reales. `reports/nlp_comparison.json` conserva el experimento exploratorio de NLP; `reports/model_comparison.json` documenta selección y `reports/test_metrics.json` la única evaluación del campeón congelado.

## Uso de asistentes de IA

Se utilizó Codex para revisar especificaciones y proponer e implementar configuración, código, pruebas, documentación y notebook. El código se ejecutó sobre la fuente fijada y se comprobó mediante las verificaciones documentadas. No se afirma una revisión humana que aún no esté documentada. La revisión final y defensa deberán reflejar la comprensión y validación reales del responsable del proyecto.

## Resultado del modelado

Se compararon ocho combinaciones de dos clasificadores y variantes NLP, se ajustaron alpha/C con CV estratificada de tres folds en una muestra de train y se reajustaron los dos finalistas con train completo. El campeón de validation fue LogisticRegression(C=1), lematización y uni/bigramas.

La selección quedó congelada antes de la única evaluación de test: Macro-F1 0,513135, accuracy 51,54 % y MAE 0,6128 estrellas sobre 5.000 reseñas. El análisis de errores muestra dificultades en estrellas intermedias y casos con contraste, formulaciones breves e interpretación contextual. Las lecturas cualitativas fueron asistidas por IA y se publican como paráfrasis; no son una revisión humana ni diagnósticos causales demostrados.

El proceso y sus limitaciones están en MODELOS.md y FASE-D-MODELADO.md. La evaluación final no se repetirá para optimizar el diseño. El corpus y los binarios permanecen fuera de Git.

## Reproducción y despliegue del modelo

La Fase E fija una referencia del estado del campeón evaluado: configuración, vocabulario, IDF, clases y pesos. Full solo conserva las métricas históricas cuando reproduce exactamente esa referencia; quick genera identidad y métricas experimentales propias. Los paquetes verifican integridad y compatibilidad antes de Joblib, además del estado aprendido tras la carga. La inferencia comparte el pipeline NLP y no ajusta ni descarga recursos.

El entrenamiento completo se verificó en una copia aislada de los archivos versionables, sin corpus ni checkpoint y con entorno nuevo; no se afirma una prueba de API o frontend. Los informes de reproducción, construcción y rendimiento se describen en FASE-E-REPRODUCIBILIDAD.md, ARTEFACTOS.md y RENDIMIENTO.md. La identidad semántica evita confundir cambios en bytes de serialización con cambios en el modelo; el checksum de archivo también se conserva para controlar integridad. La asistencia de IA incluyó esta implementación y documentación.
