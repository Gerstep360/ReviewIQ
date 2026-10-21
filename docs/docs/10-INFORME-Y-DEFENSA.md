# 10 — Informe técnico, presentación y preparación para cambios en vivo

## Entregables exigidos por el PDF

- **Informe breve en `docs/`**: problema, dataset, NLP y comparación, tabla de métricas, arquitectura y fuentes.
- **README** instalable desde cero; ejecutables, artefactos o regeneración con un comando.
- **Notebook** de EDA y experimentos; gráficos reales.
- **Slides** de exposición.
- **CONTRIBUCIONES.md** fiel a Git.
- **Tag** `entrega-final` en commit anterior a la fecha límite.
- **Declaración de IA**: permitido usar asistentes si se declara, pero cada autor debe explicar y modificar su código.

## Esqueleto recomendado de `docs/INFORME_TECNICO.md`

1. **Resumen y problema real.** Predecir 1–5 estrellas a partir de reseñas en español.
2. **Dominio, actores y casos de uso.** Explicar alcance y no confundir clasificación con verificación de satisfacción real.
3. **Dataset.** Origen académico, licencia, revisión fija, 3 splits, clases 0..4, EDA (datos realmente observados).
4. **Diseño NLP.** Normalización, tildes, URLs, números, emojis, tokens, stop words, stemming **y** lematización, n-gramas y TF-IDF; ejemplos reales antes/después.
5. **Modelos.** Fórmulas/intuición de regresión logística multiclase y MultinomialNB, selección en validación, búsqueda CV en train.
6. **Tabla de experimentos.** Filas reales con método morfológico, n-gramas, modelo, hiperparámetros, Macro-F1 y tiempo CPU.
7. **Métricas finales.** Accuracy, Macro-F1, recall por clase, confusión 5×5, MAE ordinal y errores cualitativos; fecha y split final.
8. **Arquitectura reproducible.** Diagrama del pipeline serializado, API y frontend; versiones.
9. **Rendimiento y límites.** RAM, tamaño, latencias medidas, error en estrellas intermedias, dominio Amazon; generalización a Bolivia **no validada** salvo pruebas propias.
10. **Evidencia Git y trabajo.** Commits representativos, PR revisados y autoría real.
11. **Conclusiones y trabajo futuro.** Datos comerciales con licencia apropiada, pruebas por dominio, recalibración.
12. **Bibliografía, licencias y declaración de IA.** Enlaces originales, citas, uso académico y herramientas usadas.

## Diapositivas (~10 min; adaptar tiempo real si el docente cambia)

| Minutos (orientativos) | Diapositiva | Mensaje |
|---|---|---|
| 0–1 | Problema | Mucho texto sin nota explícita; ¿qué resuelve ReviewIQ? |
| 1–2 | Dataset | Español 210k; splits, etiquetas, licencia académica |
| 2–4 | Pipeline NLP | Antes/después; negaciones; stem vs lemma; TF-IDF |
| 4–5 | Modelos | NB frente a regresión logística, por qué dos |
| 5–6 | Evaluación | Métricas **reales** y confusión, sin inflar |
| 6–8 | Demo | Respuesta API; estrellas, probabilidades, traza |
| 8–9 | Reproducibilidad | Comando de entrenamiento y estructura Git |
| 9–10 | Valor y límites | Producto académico, restricción de licencia y futuro |

## Preguntas previsibles del ingeniero (preparar respuesta propia)

- **¿Por qué clasificación y no regresión?** Porque las estrellas son cinco etiquetas discretas; el curso permite elegir clasificadores adecuados. Reportamos MAE como métrica ordinal complementaria.
- **¿Por qué TF-IDF en lugar de embeddings?** Exigencia del curso, menor coste CPU, interpretabilidad y matrices dispersas.
- **¿Qué hace el IDF?** Reduce peso relativo de términos frecuentes en muchos documentos; sólo debe ajustarse con entrenamiento.
- **¿Por qué conservar 'no'?** Puede invertir significado de opinión; se verifica empíricamente.
- **¿Qué cambia stemming vs lematización?** Stemming reduce a raíces mecánicas; lematización intenta forma canónica con análisis lingüístico; comparar impacto y CPU.
- **¿Por qué Macro-F1?** Cada clase tiene peso igual; no oculta errores en estrellas minoritarias.
- **¿Cómo evitar leakage?** TF-IDF en Pipeline dentro de CV train; validation para elegir; test final se abre una vez.
- **¿Cómo se entrena?** `python -m src.models.train --mode ...` desde datos originales y semilla fija.
- **¿Qué pasa con una reseña fuera del dominio?** La predicción puede fallar; es una limitación, no una garantía.
- **¿Es IA generativa?** No. Clasificador ML clásico.
- **¿Pueden venderlo con estos datos?** No sin verificar/obtener derechos comerciales; el corpus Amazon tiene licencia de investigación académica.

## Ejercicios para modificación en vivo (PDF páginas 6–7)

1. Añadir a stop words o excluir una, ejecutar tests, reentrenar **quick**, mostrar diferencias no inventadas y hacer commit.
2. Cambiar `ngram_range=(1,1)` a `(1,2)` vía config, reentrenar quick y comparar.
3. Cambiar `alpha` de NB o `C` de regresión logística, reentrenar quick y comparar Macro-F1.
4. Agregar una nueva métrica en el reporte (MAE o confusión) y test.
5. API: rechazar reseñas de menos de 3 palabras (según encargo del docente) y agregar test; no dejar el cambio «hardcodeado» sin documentación.
6. UI: agregar tiempo de inferencia recibido desde el backend, test y commit.

**En vivo** usar quick para que sea ejecutable en tiempo razonable; no reemplazar por esos resultados las métricas finales del full.

## Compromiso con la honestidad académica

Usar herramientas de IA solo como apoyo permitido y documentarlo. Cada persona debe entender, explicar y modificar lo que realmente subió. No atribuir autores falsos ni presentar números sintéticos como resultados.

## Commits de ejemplo

- `docs(report): incorporar tabla comparativa y analisis de errores reales`
- `docs(defense): explicar decisiones del pipeline y plan de demostracion`
- `test(defense): practicar cambio de ngramas y reconstruccion rapida`
