# Frontend conectado — Fase G

ReviewIQ presenta una herramienta académica de análisis de reseñas, con cuatro vistas en español. Se conserva React, TypeScript y Vite. El diseño usa un fondo claro, acento verde, estrellas ocre, tipografía del sistema y navegación estable; no añade fuentes remotas, analítica ni librerías de gráficos a producción.

## Vistas y datos

| Vista | Ruta hash | Fuente |
|---|---|---|
| Predicción | #/prediccion | POST /api/v1/predict/ |
| Laboratorio NLP | #/laboratorio | POST /api/v1/nlp/trace/ y metadatos de metrics |
| Modelos y métricas | #/modelos | GET /api/v1/metrics/ |
| Metodología | #/metodologia | Decisiones documentadas del proyecto y enlaces de origen/licencia |

Health se comprueba al iniciar, al volver a la pestaña y cada 30 segundos mientras está visible. El indicador informa el resultado de la última comprobación; el botón permite volver a consultar el servicio y las métricas. La navegación admite recarga y atrás/adelante mediante hashes, sin incorporar un router adicional.

El arranque se describe en frontend/README.md y en el README de la raíz: API en 8000 y Vite en 5173, con proxy /api. El build revisable usa preview en 4173. La API no exige PostgreSQL para estas funciones.

## Predicción y estados

El formulario tiene label, contador de caracteres Unicode compatible con Python, rechazo de blancos/caracteres nulos y límite de 3.000. Los botones de ejemplos solo rellenan textos sintéticos editables; el usuario debe pulsar Analizar reseña para enviarlos. No existe una predicción de demostración precargada.

Durante el envío se deshabilitan los controles y se muestra un estado de carga. El resultado contiene estrellas 1–5, clase interna, las cinco probabilidades, model_id y el tiempo de inferencia medido por el backend. Los valores de las barras son los de la respuesta, con porcentajes redondeados para lectura. No se presentan como certeza calibrada.

Los fallos de red, timeout, errores de formato y errores públicos del backend se muestran en castellano y permiten reintentar sin perder la reseña. Las solicitudes tienen timeout de 15 segundos; no se reenvían POST automáticamente. Se comprueban forma, rangos/suma de probabilidades, identidad/split de métricas y campos de traza antes de mostrar datos.

La reseña y los resultados permanecen solo en memoria al navegar entre vistas. Al editar el texto se invalidan predicción y traza para evitar asociar un resultado anterior a otra reseña. Las respuestas tardías de solicitudes abortadas no reemplazan el estado actual. Recargar la página descarta el texto; no se utiliza localStorage ni se crea un historial.

## Laboratorio NLP

El enlace desde el resultado consulta el procesamiento de la misma reseña. El laboratorio también permite introducir otro texto y pedir su traza. Se muestran normalización, tokens, stop words retiradas, lemas/raíces finales, n-gramas reconocidos y desconocidos, política y modelo activo.

Todos los tokens llegan de la API; el frontend no aplica otra normalización, stemming, lematización ni tokenización. El orden visual describe salidas de etapas; se explica que el lematizador mantiene el contexto antes de retirar stop words.

Los contadores originales y el aviso de recorte respetan los límites del backend. Las listas se pueden plegar y tienen desplazamiento interno. El tamaño del vocabulario y configuración TF-IDF provienen de metrics solo cuando su model_id coincide con el de la traza. Los contadores de n-gramas son ocurrencias, no pesos ni características únicas activas; esta API todavía no expone pesos TF-IDF por documento.

## Métricas y comparación

Se muestran ambos finalistas de validation cuando la API ofrece una comparación compatible. El modelo seleccionado se identifica sin confundir esa selección con los resultados finales. Un selector permite inspeccionar test del paquete activo o validation de cada finalista.

Macro-F1, accuracy, MAE, precisión/recall/F1 por clase y matriz 5×5 se actualizan con la fuente elegida. Filas y columnas de la matriz indican estrellas reales y predichas. Los recuentos tienen texto accesible y títulos descriptivos; el contraste del número se adapta a la luminancia de su celda.

La configuración del paquete activo, fecha, split y model_id se muestran explícitamente. Quick se identifica como experimental y de validation; no recibe la etiqueta test final. Si no hay comparación compatible, se informa y solo se muestran las métricas del paquete. No hay datos de relleno, métricas copiadas en componentes ni reevaluación de test.

## Accesibilidad, privacidad y alcance

Hay navegación semántica, enlace para saltar al contenido, labels, foco visible, estados anunciados con status/alert y controles nativos. Tras analizar se enfoca el resultado; al cambiar de vista se enfoca su encabezado. El diseño reduce movimiento cuando el navegador lo solicita. Las tablas conservan encabezados/captions; el comparador puede desplazarse dentro de su contenedor en móvil, sin desbordar la página.

Las solicitudes con texto van exclusivamente al servicio configurado. No hay envío automático a analítica, fuentes o servicios generativos. La vista de metodología documenta fuente y restricciones académicas, riesgos fuera del dominio Amazon, variantes del español, errores en estrellas intermedias y asistencia de Codex en el desarrollo.

Esta fase valida Chrome/Chromium de pruebas en Windows, en 1366×768 y 390×844. No afirma una auditoría completa de accesibilidad, otros navegadores ni un despliegue de producción. La instalación completa desde un clon limpio, la operación final y la entrega académica corresponden a H.

## Archivos y verificación

- src/api/client.ts y src/types/reviewiq.ts: cliente, timeout, errores y contratos REST.
- src/hooks/useRemote.ts: carga/cancelación de recursos y solicitudes de análisis.
- src/components/: formulario, probabilidades, matriz, traza e indicadores compartidos.
- src/pages/: las cuatro vistas; App.tsx conserva el estado y la navegación.
- vite.config.ts: proxy en desarrollo y preview; package-lock.json fija dependencias.
- src/tests/app.test.tsx: seis pruebas de comportamiento con fixtures sintéticos, aislados del producto.
- tests/browser/phase-g.spec.ts: un recorrido pequeño con API real y capturas; la respuesta 503 del estado de error se intercepta explícitamente.

Comandos y resultados reales: FASE-G-FRONTEND.md. Fuentes de implementación: [proxy de Vite](https://vite.dev/config/server-options#server-proxy), [Vitest](https://vitest.dev/guide/), [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) y [servidores de prueba Playwright](https://playwright.dev/docs/test-webserver).
