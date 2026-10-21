# 01 — Producto, caso de uso y arquitectura

## Nombre y problema

**ReviewIQ — Predictor de satisfacción comercial con NLP y ML.** Los comerciantes reciben opiniones textuales pero no siempre tienen una valoración cuantitativa. El sistema estima una valoración probable de **1, 2, 3, 4 o 5 estrellas** y visualiza cómo se procesa el texto.

**No afirmar** que ReviewIQ mide satisfacción «real» o que conoce intenciones del comprador: predice etiquetas basándose en patrones del corpus.

## Caso de uso CU-01 — Predecir estrellas

- **Actor:** analista/administrador de una tienda (sin autenticación en MVP académico).
- **Precondiciones:** API en ejecución y artefacto de pipeline cargado, con versión compatible.
- **Entrada:** reseña en español; no aceptar entrada vacía; límite configurable (p. ej., 3.000 caracteres).
- **Flujo:** escribir reseña → enviar a API → validar → `pipeline.predict_proba()` → mapear clase 0–4 a 1–5 → devolver probabilidades → renderizar barras, valoración estimada e ID del modelo.
- **Salidas:** 5 probabilidades estimadas, clase más probable, estrellas mostradas, versión de modelo; vista técnica del NLP obtenida del mismo pipeline.
- **Errores:** entrada vacía, demasiado larga, API caída, artefactos incompatibles.
- **Criterio de aceptación:** la misma reseña usada por la API y el pipeline guardado produce la misma salida.

## Otros casos de uso de interfaz (no más modelos)

- **CU-02:** ver transformación del texto por etapas para defensa técnica.
- **CU-03:** comparar las métricas **reales** de los dos clasificadores y sus confusiones.
- **CU-04 opcional:** clasificar lote CSV sin guardar textos en servidor. No compite con el MVP obligatorio.

## Arquitectura

```text
SetFit/amazon_reviews_multi_es (train/validation/test)
        |
        v
src/data/download.py + src/data/eda.py
        |
        v
Pipeline sklearn [normalización -> tokens -> stop words -> stem O lemma
                  -> TF-IDF -> LogisticRegression / MultinomialNB]
        |
        v
Comparación en validation; test FINAL una vez; export manifest+joblib+metrics.json
        |
        v
FastAPI (carga el artefacto una sola vez al iniciar)
        |
        v
React/TypeScript (predicción + trazas NLP + panel de resultados)
```

**Regla principal:** el backend **NO** contiene una función alternativa para limpiar o tokenizar texto; reutiliza las etapas serializadas en `Pipeline`. Si existe un `trace()`, usa los mismos objetos y configuración sin transformaciones divergentes.

## Tecnologías justificadas

| Capacidad | Elección | Motivo |
|---|---|---|
| Clasificación | LogisticRegression multinomial | Eficiente con vectores dispersos; probabilidades por clase |
| Comparación | MultinomialNB | Baseline fuerte, simple y rápido para TF-IDF no negativo |
| Texto → números | TfidfVectorizer | Requisito explícito del docente |
| NLP español | NLTK/es + spaCy/es solo cuando se necesite | Stemming barato y alternativa de lematización |
| API | FastAPI y Pydantic | OpenAPI, validación y tests |
| Interfaz | React/TS/Vite | UI dinámica y tipado simple |
| Modelos | Joblib + manifest | Reproducibilidad controlada, sin carga remota |

## Pantallas imprescindibles

1. **Predicción:** textarea + estrella estimada + histograma de probabilidades 1–5 + estado del servidor.
2. **Laboratorio NLP:** texto original, normalización, tokens, stop words excluidas, stemming/lemas, n-gramas representativos y total de rasgos TF-IDF; mostrar pasos reales.
3. **Modelos:** Macro-F1, accuracy, MAE por estrellas, matriz de confusión y configuración ganadora.
4. **Acerca del modelo:** dataset, método, licencia académica, límites e información de reproducibilidad.

## Producto «vendible» vs. derechos de uso

Prototipo para **demostración académica**. El corpus original Amazon Reviews Multi limita el uso comercial; para vender ReviewIQ de verdad se necesitan datos propios/contratados con permisos adecuados y reentrenamiento. No hacer promesas de negocio basadas en este corpus.

## Definición de terminado

`POST /predict` responde predicciones de un artefacto entrenado; front las muestra; hay informe de modelos y pruebas; se puede levantar en otra PC siguiendo README, sin depender de API generativa.

## Commits de referencia (realizar solo tras implementar)

- `docs(product): definir alcance y caso de uso de clasificacion de estrellas`
- `feat(product): registrar metadatos y limitaciones del predictor`
