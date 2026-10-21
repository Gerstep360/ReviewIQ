# Registro de experimentos

## Fase C — Variantes NLP

Ejecutado el 21 de octubre de 2026 con semilla 42. Evidencia completa: reports/nlp_comparison.json y reports/nlp_comparison.csv. Se conservan versiones, hashes de origen/configuración/código, identidad de la muestra y políticas.

Datos: 20.000 filas estratificadas de train preparado; 5.000 de validation. Ningún acceso a test. Baseline fijo: MultinomialNB(alpha=1). Comparación: stemming/lematización por (1,1)/(1,2), con el mismo TF-IDF float32.

Mejor variante experimental: stemming+(1,2), Macro-F1 validation 0,4782833223643447 y accuracy validation 0,4812. No son métricas finales. Vocabulario: 36.851 rasgos; nnz de train: 442.474.

Se recomienda comenzar la fase D con esta variante, comparándola con los dos clasificadores y CV estratificada en train. No se ha seleccionado un modelo final ni generado un artefacto de entrega. Ver docs/NLP.md para costes y límites de medición.