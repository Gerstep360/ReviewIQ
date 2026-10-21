# Análisis de errores del campeón

Modelo: `reviewiq-8f0ef24251ae5522`. Etiquetas convertidas a estrellas 1–5.

Validation se usó para seleccionar; test solo estima el rendimiento del campeón ya congelado. No se retocó el modelo usando este análisis. No se publican textos ni IDs del corpus.

## validation

Errores: 2409 de 5000; 496 predicciones se alejan al menos dos estrellas. La clase con menor F1 es 3 estrellas (F1=0.4016).

### Confusiones más frecuentes

| Estrellas reales | Predichas | Casos |
|---:|---:|---:|
| 4 | 5 | 298 |
| 2 | 1 | 261 |
| 3 | 2 | 254 |
| 2 | 3 | 251 |
| 5 | 4 | 232 |
| 1 | 2 | 229 |
| 4 | 3 | 205 |
| 3 | 4 | 183 |

### Rasgos observados entre los errores

Los grupos se superponen; su presencia no demuestra la causa del error.

| Rasgo | Casos |
|---|---:|
| contains_negation | 1336 |
| contains_contrast_connector | 897 |
| short_text_at_most_8_words | 345 |
| intermediate_rating | 1767 |

### Casos para inspección local

Posiciones contadas desde 1 en el archivo del split evaluado. Validation corresponde al archivo preparado; test al JSONL original fijado. Solo se muestran estadísticas y etiquetas.

| Fila | Reales | Predichas | Distancia | Palabras |
|---:|---:|---:|---:|---:|
| 33 | 1 | 5 | 4 | 24 |
| 198 | 1 | 5 | 4 | 14 |
| 730 | 1 | 5 | 4 | 26 |
| 837 | 1 | 5 | 4 | 6 |
| 974 | 1 | 5 | 4 | 33 |
| 4095 | 5 | 1 | 4 | 20 |
| 4186 | 5 | 1 | 4 | 13 |
| 4269 | 5 | 1 | 4 | 37 |

## test

Errores: 2423 de 5000; 502 predicciones se alejan al menos dos estrellas. La clase con menor F1 es 3 estrellas (F1=0.3959).

### Confusiones más frecuentes

| Estrellas reales | Predichas | Casos |
|---:|---:|---:|
| 4 | 5 | 296 |
| 3 | 2 | 248 |
| 2 | 1 | 247 |
| 1 | 2 | 246 |
| 2 | 3 | 231 |
| 5 | 4 | 225 |
| 3 | 4 | 217 |
| 4 | 3 | 211 |

### Rasgos observados entre los errores

Los grupos se superponen; su presencia no demuestra la causa del error.

| Rasgo | Casos |
|---|---:|
| contains_negation | 1273 |
| contains_contrast_connector | 854 |
| short_text_at_most_8_words | 354 |
| intermediate_rating | 1756 |

### Casos para inspección local

Posiciones contadas desde 1 en el archivo del split evaluado. Validation corresponde al archivo preparado; test al JSONL original fijado. Solo se muestran estadísticas y etiquetas.

| Fila | Reales | Predichas | Distancia | Palabras |
|---:|---:|---:|---:|---:|
| 64 | 1 | 5 | 4 | 10 |
| 113 | 1 | 5 | 4 | 38 |
| 138 | 1 | 5 | 4 | 23 |
| 174 | 1 | 5 | 4 | 22 |
| 283 | 1 | 5 | 4 | 17 |
| 293 | 1 | 5 | 4 | 32 |
| 479 | 1 | 5 | 4 | 42 |
| 537 | 1 | 5 | 4 | 26 |

## Lectura cualitativa asistida de casos reales

Las siguientes descripciones son paráfrasis; las hipótesis no se tratan como causas comprobadas.

- validation, fila 33: Una reseña describe una avería temprana y una reclamación sin resolver; la valoración original es de 1 estrella y el modelo predice 5. La presencia de una negación conservada no garantiza reconocer una secuencia narrativa negativa. No se ha identificado una causa única del error.
- validation, fila 198: La utilidad protectora del artículo se cuestiona mediante una comparación con una alternativa doméstica. El modelo predice 5 frente a 1 estrella real. La formulación puede leerse como ironía; esa interpretación es cualitativa y no una categoría diagnosticada automáticamente.
- validation, fila 730: El texto elogia a la tienda antes de explicar que el producto no resulta adecuado. El modelo predice 5 y la valoración original es 1. Hay señales positivas y negativas en entidades distintas y un conector de contraste; unigramas y bigramas no resuelven de forma explícita a qué entidad se refiere cada valoración.
- validation, fila 837: Una crítica de solo seis palabras comunica deterioro y una alteración del contenido de un recipiente. El modelo predice 5 frente a 1 estrella real. El ejemplo muestra una evaluación negativa breve sin un negador explícito; determinar el papel de términos raros requeriría analizar los pesos del modelo.

## Límites

No se infiere sarcasmo automáticamente. Los marcadores de negación y contraste son indicadores descriptivos; no capturan alcance sintáctico. Los conjuntos reservados conservan sus duplicados originales documentados en DATASET.md. Estas observaciones sirven para explicar límites, no para optimizar usando test.
