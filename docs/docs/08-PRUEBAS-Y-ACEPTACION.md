# 08 — Responsabilidad: calidad, pruebas e integración

## Estrategia de pruebas

| Tipo | Comprobar | Archivo estimado |
|---|---|---|
| Datos | Etiquetas 0–4; splits; nulls; reproducibilidad | `tests/test_data.py` |
| NLP | No negación; Unicode; URL; emoji; stems/lemas; ejemplos | `tests/test_nlp.py` |
| ML | CV solo train; clases cinco; resultados de validación; no leakage | `tests/test_models.py` |
| Serialización | Predicciones idénticas antes/después de Joblib | `tests/test_artifacts.py` |
| Backend | `/health`, `/predict`, `/metrics`, `/nlp/trace`, validaciones | `tests/test_api.py` |
| Frontend | Estados de red, resultado, traza, matriz | `frontend/src/tests/` |
| E2E | Frontend → API → pipeline → resultado real | `tests/e2e/` o instrucciones documentadas |

## Pruebas particularmente útiles ante el docente

1. Texto `'NO funciona'` vs `'funciona'`: la etapa de NLP debe conservar negación según política; **no exigir** que la predicción cambie de una manera específica, solo que el pipeline la representa.
2. `label=0` corresponde a 1 estrella y `label=4` corresponde a 5.
3. `Pipeline` recargado produce la misma distribución de probabilidad dentro de tolerancia definida.
4. `TF-IDF` se **ajusta** solo en entrenamiento (en cada fold); validation y test únicamente `.transform`.
5. Si se cambia `ngram_range`, **reentrenar** e invalidar métricas anteriores.
6. API rechaza texto vacío, 3.001 caracteres si límite=3.000, JSON inválido.
7. Métricas y manifiesto tienen mismo `model_id` y split correcto.
8. Sin red: API ya iniciada sirve inferencias locales con artefactos.

## Benchmark sin promesas inventadas

- Equipo/CPU, RAM disponible, sistema y versión de Python.
- Número de reseñas usadas (quick/full), tiempo de entrenamiento total, tamaño de artefacto.
- Memoria pico (RSS) del entrenamiento y de API inactiva.
- Latencia de predicción 1 texto y lote de 100, p50/p95; fase warm-up explícita.
- Mantener cargas pequeñas en un portátil, medir con `time.perf_counter` y `psutil` si se usa.
- No fijar «menos de X ms» sin medir; objetivo operativo inicial: la interfaz responde fluidamente, sin agotar RAM, y documenta las limitaciones.

## Aceptación final en clon limpio

- [ ] `git clone` del tag `entrega-final`.
- [ ] Instalar Python/Node y dependencias fijadas siguiendo README.
- [ ] Descarga académica de datos funciona o están las instrucciones legítimas necesarias.
- [ ] Modo quick sirve para una modificación en clase; modo full produce modelo final.
- [ ] Levantar FastAPI, acceder a `/docs`, comprobar `/health`.
- [ ] Levantar frontend, escribir reseña, recibir respuesta real.
- [ ] Ver NLP paso a paso y comparación de dos modelos.
- [ ] Pruebas pasan; informe corresponde al código entregado.
- [ ] Sin secretos, credenciales, datos privados o archivos de prueba sueltos en commits.

## CI opcional

GitHub Actions: Python lint+pytest y frontend `npm ci && npm test && npm run build`; no ejecutar entrenamiento 200k por cada push. Usar pequeños **fixtures sintéticos** para CI y pruebas de inferencia; marcar fixtures como sintéticos.

## Commits

- `test(nlp): cubrir normalizacion y negaciones españolas`
- `test(ml): verificar consistencia de inferencia serializada`
- `test(e2e): validar prediccion desde frontend hasta modelo`
- `perf(api): medir latencia y memoria en cpu`
- `ci: ejecutar pruebas y build en cada pull request`
