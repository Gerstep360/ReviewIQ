# Registro de experimentos

## Fase C — Variantes NLP

Ejecutado el 21 de octubre de 2026 con semilla 42. Evidencia completa: reports/nlp_comparison.json y reports/nlp_comparison.csv. Se conservan versiones, hashes de origen/configuración/código, identidad de la muestra y políticas.

Datos: 20.000 filas estratificadas de train preparado; 5.000 de validation. Ningún acceso a test. Baseline fijo: MultinomialNB(alpha=1). Comparación: stemming/lematización por (1,1)/(1,2), con el mismo TF-IDF float32.

Mejor variante experimental: stemming+(1,2), Macro-F1 validation 0,4782833223643447 y accuracy validation 0,4812. No son métricas finales. Vocabulario: 36.851 rasgos; nnz de train: 442.474.

Se recomienda comenzar la fase D con esta variante, comparándola con los dos clasificadores y CV estratificada en train. No se ha seleccionado un modelo final ni generado un artefacto de entrega. Ver docs/NLP.md para costes y límites de medición.
## Fase D — Clasificadores y CV

Misma muestra de 20.000 filas de train y 5.000 de validation para el cribado de ocho combinaciones. CV estratificada de tres folds en train: NB eligió alpha=2 (Macro-F1 medio 0,478621); LR eligió C=1 (0,479923). El preprocesamiento aprendido y TF-IDF se ajustan en cada fold.

Tras ajustar ambos con 197.572 filas de train, LR con lematización y bigramas obtuvo Macro-F1 validation 0,515025 y superó a NB con stemming y bigramas (0,508795). Se congeló el campeón antes de test: reviewiq-8f0ef24251ae5522.

Única evaluación test: Macro-F1 0,5131349211771471; accuracy 0,5154; MAE en estrellas 0,6128. Registro persistente: reports/final_test_ledger.json. No se retocaron parámetros tras esta evaluación. Evidencia: model_screening, cv_results, model_comparison, model_selection, test_metrics y errors.md en reports/.