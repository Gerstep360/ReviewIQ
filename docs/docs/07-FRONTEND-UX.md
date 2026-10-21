# 07 — Responsabilidad: frontend profesional y verificable

> Fase G implementada con React/TypeScript/Vite y la API Django/DRF de la arquitectura vigente. Las menciones originales de FastAPI se adaptan a ese backend. Uso y decisiones: [FRONTEND.md](../FRONTEND.md). Evidencia ejecutada y capturas: [FASE-G-FRONTEND.md](../FASE-G-FRONTEND.md).

## Objetivo visual

Construir una aplicación de análisis comercial utilizable y sobria, no una página tipo chatbot. Mostrar **predicción y evidencia**. React + TypeScript + Vite; UI responsiva de escritorio/móvil; colores neutros y un acento para estrellas/estado.

## Vista 1 — Predicción (obligatoria)

- Campo para reseña (español) con contador y validación visible.
- Botón **Analizar reseña** con carga/disabled durante envío.
- Resultado de 1 a 5 estrellas, clase y probabilidad estimada del modelo; aclarar que no es opinión verdadera garantizada.
- Gráfico de cinco barras de probabilidades; suma total ~100%.
- Model ID, tiempo real medido, indicador de API conectada.
- Estados: reposo / enviando / resultado / error / reintentar.
- Ejemplo ilustrativo claramente marcado al principio; la entrega final debe tener resultados reales del backend.

## Vista 2 — Laboratorio NLP (obligatoria)

Panel que muestra: **original → normalizado → tokens → stop words eliminadas → stemming o lematización → n-gramas → datos de TF-IDF** (vocabulario, `ngram_range` y nº características). Todo procede de API `nlp/trace` y los **mismos transformadores serializados**. Si se muestran tokens en frontend, no calcularlos en JS independientemente.

## Vista 3 — Comparador ML (obligatoria)

- Regresión logística vs Naive Bayes: Macro-F1, accuracy, precision/recall por estrellas y MAE.
- Identificación visual del modelo activo con regla de selección.
- Matriz de confusión 5×5 con filas de estrellas reales, columnas de predicción; accesibilidad y contraste.
- Configuración ganadora, split de origen y fecha/versión de métricas.
- Mostrar métricas que devuelva API; **jamás números de demo en producción**.

## Vista 4 — Metodología y limitaciones

Origen del corpus, método, licencia académica, riesgo de errores en estrellas intermedias, advertencia sobre reseñas fuera de dominio (por ejemplo dialectos de Bolivia, español coloquial, restaurantes vs Amazon), declaración de uso de IA de asistencia en desarrollo.

## Componentes sugeridos

```text
frontend/src/
  app/
  api/client.ts                 # fetch tipado, timeout y errores
  components/StarRating.tsx
  components/ProbabilityBars.tsx
  components/ConfusionMatrix.tsx
  components/NlpTrace.tsx
  pages/PredictPage.tsx
  pages/NlpLabPage.tsx
  pages/ModelsPage.tsx
  pages/AboutPage.tsx
  types/reviewiq.ts
  tests/
```

## Accesibilidad y UX

- `<label>` correcto, navegación por teclado y foco visible.
- Textos accesibles para barras además del color; escala 1–5 comprendida.
- Estado de red confiable, mensajes claros en castellano; skeleton o indicador de carga.
- No enviar automáticamente texto a terceros: API local.
- Si UI ofrece «prioridad de atención», definirlo como **regla de interfaz opcional** derivada de estrellas, no modelo ML adicional. No asegurar que equivale a daño real.

## Lista de aceptación

- [ ] Predice desde FastAPI sin datos simulados.
- [ ] Muestra 5 probabilidades, una estrella ganadora, errores de red y limitaciones.
- [ ] Panel de NLP tiene trazas reales (no tokenización nueva en JS).
- [ ] Métricas de ambos modelos con versión/split de evaluación.
- [ ] Interfaz usable en 1366×768 y en móvil.
- [ ] Tests de componentes para resultado/error/trace.

## Ejemplos de commits

- `feat(web): crear formulario accesible para evaluar reseñas`
- `feat(web): visualizar probabilidades de las cinco estrellas`
- `feat(web): incorporar laboratorio de preprocesamiento del backend`
- `feat(web): comparar metricas y matriz de confusion por modelo`
- `test(web): cubrir errores de api y estados de carga`
