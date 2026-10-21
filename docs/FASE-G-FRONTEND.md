# Fase G — Frontend funcional

Implementada según la guía 07, conectada al backend Django/DRF de F. Se reemplazó la plantilla de Vite por una aplicación de análisis en español. La predicción, las trazas y las métricas válidas proceden de llamadas reales a la API; no se modifica ni se reentrena el modelo.

## Entregables

- Formulario accesible, contador Unicode y validaciones; ejemplos sintéticos editables, estados inicial/carga/resultado/error/reintento.
- Resultado de estrellas, clase, cinco probabilidades, identidad y latencia real de inferencia.
- Laboratorio con tokens del preprocesador guardado, n-gramas, recortes y metadatos del vocabulario TF-IDF.
- Comparación de los dos clasificadores en validation, selector de origen, matriz 5×5, detalle por clase y configuración activa. Test final se distingue de validation/quick.
- Metodología, corpus/licencia, limitaciones de dominio/dialectos y declaración de asistencia IA.
- Diseño responsive de escritorio/móvil, teclado/foco, estados anunciados, movimiento reducido y contraste adaptado en la matriz.
- Cliente tipado con timeout/cancelación, comprobación de respuestas y proxy local dev/preview. No se conserva texto en almacenamiento del navegador.
- Dependencias fijadas en package-lock.json, seis pruebas de componentes/cliente y un recorrido de navegador sobre la API real.

Archivos centrales en frontend/src/{api,types,hooks,lib,components,pages}, App.tsx, estilos, configuración Vite/Vitest/Playwright, tests y documentación. El contrato y comandos están en FRONTEND.md y frontend/README.md.

## Comandos ejecutados y resultado final

Entorno: Windows, Node 24.15.0, npm 11.12.1, React 19.3.1, TypeScript 6.0.3, Vite 8.3.5. Paquetes de prueba: Vitest 5.0.5, Testing Library React 16.3.3/DOM 10.4.2, jsdom 30.1.3 y Playwright 1.64.1. Se mantuvo la pila del repositorio; las dependencias de prueba no entran en el bundle de producción.

```text
venv/Scripts/python.exe manage.py runapi 127.0.0.1:8000 --noreload --nothreading
  model_ready model_id=reviewiq-8f0ef24251ae5522 mode=full

npm run build
  tsc -b && vite build
  31 modules transformed.
  dist/index.html                       0.68 kB (gzip 0.42)
  dist/assets/index-CkadnIiq.css        24.60 kB (gzip 6.06)
  dist/assets/index-iRB2dmhY.js        255.57 kB (gzip 79.35)
  built in 203ms

npm test
  Test Files 1 passed (1)
  Tests 6 passed (6)
  Duration 1.96s

npm run lint
  oxlint
  Exit code 0, sin advertencias.

npx playwright install chromium
  Chrome for Testing / Headless Shell 156.0.8078.4 instalado desde el CDN oficial de Playwright.

npm run test:browser
  1 passed (3.7s)
```

Se instalaron las dependencias y se generó el lock con npm install; npm ci se documenta para instalaciones posteriores. No se afirma haber repetido una instalación completa del proyecto desde otro clon en esta fase.

## Verificación realizada

Las seis pruebas enfocadas cubren blancos/límite Unicode, ausencia de envío al elegir ejemplo, carga/disabled, cinco probabilidades e inferencia de la respuesta, error de red y reintento con texto conservado, tokens recibidos del backend sin tokenización JS, invalidación de traza al editar, selección de validation frente a test y rechazo de respuestas inválidas/timeout. Sus números son fixtures sintéticos exclusivos de tests.

El navegador integrado no estaba disponible, por lo que se utilizó Chromium aislado mediante Playwright para verificar el frontend. El recorrido comprobó primero dev y después el build servido por preview, ambos con proxy a la API real. Analizó un ejemplo sintético con contraste, obtuvo tres estrellas calculadas por el campeón y comprobó las cinco probabilidades. Verificó que texto normalizado/tokens y matrices coinciden con las respuestas de la API, inspeccionó finalistas y metodología y conservó la reseña al navegar.

Se comprobó en 1366×768 y 390×844, sin desbordamiento horizontal de página. En móvil se verificó un 503 simulado y luego se retiró la interceptación: Reintentar obtuvo otra predicción real. El mensaje de recurso 503 en consola corresponde a esa simulación intencional; no hubo errores JavaScript de página. La matriz ajusta texto blanco/negro según luminancia. Las capturas se inspeccionaron visualmente y se ajustaron contraste, alineación y legibilidad.

Evidencia estructurada: reports/frontend_smoke.json. Capturas públicas con reseñas sintéticas:

- [Predicción de escritorio](../reports/figures/web-prediction-desktop.png) y [estado inicial](../reports/figures/web-empty-desktop.png).
- [Laboratorio NLP](../reports/figures/web-nlp-desktop.png) y [métricas de escritorio](../reports/figures/web-models-desktop.png).
- [Predicción móvil](../reports/figures/web-prediction-mobile.png), [métricas móviles](../reports/figures/web-models-mobile.png) y [estado de error móvil](../reports/figures/web-error-mobile.png).

No se tocó el backend, el pipeline, la configuración congelada ni los resultados históricos de selección/test. Los binarios, el corpus, node_modules, dist y los resultados temporales de los runners quedan fuera de Git.

## Alcance restante

La aplicación funciona localmente con API y frontend activos. Preview es una comprobación del build, no un servidor productivo. No se han validado otros navegadores/dispositivos ni realizado una auditoría completa de accesibilidad. H cubrirá instalación/integración final, operación, informe y defensa; no se creó tag entrega-final.

La asistencia de Codex en código, diseño, pruebas y documentación queda declarada en el informe y contribuciones. Commit del bloque: feat(web): conectar prediccion laboratorio nlp y metricas reales.
