# Informe técnico — avance

Documento parcial. La arquitectura y las fases B (datos/EDA), C (pipeline NLP), D (modelado ML), E (reproducción/artefactos), F (backend REST) y G (frontend conectado) están implementadas. Falta el cierre de integración, informe y defensa de H.

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

## Backend REST

La Fase F adapta la guía original de FastAPI/Pydantic a Django/DRF y serializers. WSGI/ASGI cargan el paquete verificado y lo calientan al iniciar; las vistas comparten Predictor para predicción y traza. Health devuelve 503 si la carga falla. Las métricas se leen del mismo paquete y la comparación de validation se publica solo cuando su model_id coincide. No se ajustan transformadores ni se vuelve a puntuar test en solicitudes.

Se validan entrada, codificación, tamaño y salida; se limitan trazas y espera de turno. La API no persiste reseñas ni consulta PostgreSQL. Swagger y el esquema OpenAPI se sirven desde el proyecto con recursos locales. El comando de desarrollo runapi omite exclusivamente el chequeo de migraciones para estas funciones sin persistencia; el backend conserva PostgreSQL para operaciones que lo requieran.

Ocho pruebas enfocadas pasaron, incluida igualdad API/pipeline real sobre tres ejemplos de validation con fit/red bloqueados. Se comprobó además HTTP en loopback y se midieron treinta solicitudes individuales: p50 22,65 ms, p95 31,84 ms y RSS observado tras solicitudes de hasta 264,62 MiB en el servidor de desarrollo. No son resultados de frontend ni de producción. Evidencia, comandos, alcance y asistencia de IA: API.md, FASE-F-BACKEND.md y reports/api_smoke.json.

## Interfaz conectada

La Fase G implementa predicción de estrellas/probabilidades, laboratorio NLP real, comparación de modelos con matriz/detalle por clase y metodología. React no aplica otra tokenización ni contiene métricas de demostración. El cliente maneja validación, estados de red, timeout, cancelación y reintentos; conserva texto solo en memoria y descarta resultados al editar. El comparador identifica validation, test y quick experimental.

Se mantuvo React/TypeScript/Vite, con dependencias fijadas en package-lock.json, proxy local y diseño claro responsive. Build y lint pasaron; seis pruebas de comportamiento y un recorrido Chromium con API real pasaron. El recorrido verificó dev/build, las cuatro vistas, igualdad de trazas/matrices con API, navegación con texto conservado y ausencia de desbordamiento en 1366×768 y 390×844. Solo se simuló un 503 para comprobar el estado de error y su reintento real posterior.

Se inspeccionaron capturas y se ajustó contraste y legibilidad. No se afirma una auditoría completa de accesibilidad, compatibilidad con todos los navegadores ni despliegue de producción. No se modificó el modelo ni se repitió test. La asistencia de Codex incluyó implementación, diseño, pruebas y documentación. Evidencia: FRONTEND.md, FASE-G-FRONTEND.md, reports/frontend_smoke.json y capturas en reports/figures/web-*.png.
