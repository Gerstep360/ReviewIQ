# ReviewIQ — Frontend

React + TypeScript + Vite. Cuatro vistas conectadas a Django/DRF: predicción, laboratorio NLP, modelos/métricas y metodología. No hay resultados simulados ni tokenización NLP en JavaScript.

## Iniciar

Requiere Node >=22.12 (verificado con 24.15.0), el entorno Python y un paquete del modelo generado según el README de la raíz. En una terminal desde la raíz:

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42
.\venv\Scripts\python.exe manage.py runapi 127.0.0.1:8000 --noreload --nothreading
```

En otra terminal, dentro de frontend:

```powershell
npm ci
npm run dev
```

Abre http://127.0.0.1:5173/. El proxy de Vite dirige /api a 127.0.0.1:8000 y evita configurar CORS para este flujo. No se necesita PostgreSQL para la inferencia. Si la API no está disponible, la interfaz muestra el error y permite reconectar/reintentar.

## Comprobaciones

```powershell
npm test
npm run lint
npm run build
```

Para el recorrido de navegador con la API real (no vuelve a entrenar):

```powershell
npx playwright install chromium
npm run build
npm run test:browser
```

Playwright reutiliza los servidores locales si ya están iniciados; de lo contrario levanta API, dev y preview y cierra los que creó. Necesita un paquete válido antes de iniciar. El recorrido comprueba las cuatro vistas en escritorio/móvil, conserva capturas y escribe reports/frontend_smoke.json. Solo la respuesta de error 503 se simula para comprobar el reintento; las predicciones, trazas y métricas válidas proceden de la API real.

## Versión compilada

```powershell
npm run build
npm run preview
```

Abre http://127.0.0.1:4173/ con la API activa. preview también tiene el proxy local; sirve para revisar el build, no es un despliegue productivo. Al alojar dist en otro servidor se debe servir /api desde el backend o definir VITE_API_BASE_URL al compilar y permitir el origen correspondiente en Django.

.env.example documenta VITE_API_BASE_URL y REVIEWIQ_PROXY_TARGET. Solo las variables VITE_* se exponen al navegador; nunca deben contener secretos. Los puertos son fijos y el inicio falla si están ocupados por otro proceso, en vez de cambiar de puerto silenciosamente.

Contrato, decisiones y alcance: [FRONTEND.md](../docs/FRONTEND.md). Evidencia ejecutada: [FASE-G-FRONTEND.md](../docs/FASE-G-FRONTEND.md).
