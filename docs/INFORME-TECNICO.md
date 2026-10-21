# Informe técnico — avance

Documento parcial. La arquitectura y las fases B (datos/EDA), C (pipeline NLP) y D (modelado ML) están implementadas. Se completará después del empaquetado reproducible y la integración del sistema.

Fuente, licencia y preparación: `DATASET.md`. Comandos y resultados: `FASE-B-DATOS-EDA.md`, `FASE-C-PIPELINE-NLP.md` y `FASE-D-MODELADO.md`. Las estadísticas proceden de ejecuciones reales. `reports/nlp_comparison.json` conserva el experimento exploratorio de NLP; `reports/model_comparison.json` documenta selección y `reports/test_metrics.json` la única evaluación del campeón congelado.

## Uso de asistentes de IA

Se utilizó Codex para revisar especificaciones y proponer e implementar configuración, código, pruebas, documentación y notebook. El código se ejecutó sobre la fuente fijada y se comprobó mediante las verificaciones documentadas. No se afirma una revisión humana que aún no esté documentada. La revisión final y defensa deberán reflejar la comprensión y validación reales del responsable del proyecto.

## Resultado del modelado

Se compararon ocho combinaciones de dos clasificadores y variantes NLP, se ajustaron alpha/C con CV estratificada de tres folds en una muestra de train y se reajustaron los dos finalistas con train completo. El campeón de validation fue LogisticRegression(C=1), lematización y uni/bigramas.

La selección quedó congelada antes de la única evaluación de test: Macro-F1 0,513135, accuracy 51,54 % y MAE 0,6128 estrellas sobre 5.000 reseñas. El análisis de errores muestra dificultades en estrellas intermedias y casos con contraste, formulaciones breves e interpretación contextual. Las lecturas cualitativas fueron asistidas por IA y se publican como paráfrasis; no son una revisión humana ni diagnósticos causales demostrados.

El proceso y sus limitaciones están en MODELOS.md y FASE-D-MODELADO.md. La evaluación final no se repetirá para optimizar el diseño. El corpus y el checkpoint binario permanecen fuera de Git; falta la fase E de reproducción y empaquetado de despliegue.