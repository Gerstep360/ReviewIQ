# Artefactos y reproducción — Fase E

La selección de la Fase D y su evaluación final son evidencia histórica. Full reproduce ese estado aprendido; no vuelve a buscar parámetros, seleccionar con validation ni puntuar test. Quick permite experimentos separados. Las rutas src/models de la guía original se adaptan a ml/training y ml/inference.

## Comandos de uso

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42
.\venv\Scripts\python.exe -m ml.training.train --mode quick --seed 42
```

Full verifica primero la evidencia histórica y la configuración congelada. Si hay un paquete full válido lo reutiliza. Si solo existe el checkpoint original evaluado, verifica su SHA-256 y lo empaqueta. Si no hay artefacto, obtiene el corpus fijado, verifica hashes y esquema, reproduce la preparación de train y reentrena el campeón con los parámetros congelados. El archivo de train preparado debe coincidir con el de la Fase D.

La preparación desde cero compara identidades entre splits para repetir la limpieza previamente definida; no ejecuta predicciones sobre test. Su EDA mínimo se limita al corpus de train. Los informes de esta obtención se guardan en el paquete y no reemplazan los informes históricos de datos.

Para forzar el reajuste congelado sin repetir test:

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode full --seed 42 --rebuild
```

Quick usa 20.000 filas estratificadas de train y evalúa validation; reutiliza la familia de clasificador y parámetros seleccionados como punto de partida, sin repetir CV. Sus métricas se marcan como experimentales y tienen un identificador distinto. Permite probar stemming/lematización y unigramas/bigramas:

```powershell
.\venv\Scripts\python.exe -m ml.training.train --mode quick --seed 42 --morphology stemming --ngram-max 1
```

Los paquetes se guardan por defecto en ml/artifacts/full y ml/artifacts/quick; --output-dir permite elegir otra carpeta. Los datos y los paquetes generados permanecen fuera de Git. El repositorio entrega las instrucciones, referencias, dependencias fijadas y código que los reconstruyen.

## Contenido de un paquete

| Archivo | Responsabilidad |
|---|---|
| pipeline.joblib | Pipeline completo: NLP, TF-IDF y clasificador |
| manifest.json | Versión de esquema, modelo, hashes, clases, semilla, fuente, parámetros, vocabulario y versiones |
| metrics.json | Métricas del mismo model_id: test histórico para full o validation experimental para quick |
| build_report.json | Ruta de construcción, filas, tiempo, CPU y memoria observados |
| performance.json | Carga, primera inferencia, p50/p95 calientes y RAM en proceso separado |
| provenance/ | Obtención, auditoría y preparación cuando fue necesario descargar datos |

El modelo español es una dependencia fijada, no un archivo descargado durante cada predicción. Los módulos del transformador viven en rutas importables estables para Joblib.

## Identidad y evaluación ya cerrada

reports/frozen_reference.json se generó exclusivamente desde el checkpoint cuyo SHA-256 aparece en la evaluación de la Fase D. Registra una huella determinista de vocabulario, IDF, pesos, clases, parámetros y stop words; además incluye versiones, código NLP y probabilidades de diez frases sintéticas.

Los bytes de Joblib pueden variar por compresión o serialización. Full exige igualdad exacta del estado aprendido y comprueba las probabilidades sintéticas tras reentrenar y tras recargar. Solo entonces conserva el model_id evaluado y copia sus métricas históricas. Un estado diferente se rechaza: no recibe las métricas de test del campeón.

Las comprobaciones históricas usan JSON canónico para tolerar diferencias LF/CRLF al copiar el repositorio. No reescriben model_selection.json, test_metrics.json ni final_test_ledger.json. La huella exacta puede fallar si otra plataforma o biblioteca numérica cambia los pesos; en ese caso no se presenta la reconstrucción como el modelo evaluado. La ejecución verificada se documenta con su entorno real.

## Carga e inferencia

```python
from ml.inference.predictor import get_predictor

predictor = get_predictor()
result = predictor.predict(["No funciona, sin garantía"])
trace = predictor.trace("No funciona, sin garantía")
metrics = predictor.metrics
```

get_predictor cachea una instancia por ruta y proceso. Antes de Joblib se verifican los nombres permitidos, hashes, vínculo modelo/métricas, clases, código NLP y versiones; después se comprueba el estado aprendido. Las solicitudes posteriores solo ejecutan el pipeline guardado. No descargan datos, no llaman fit y no duplican normalización ni TF-IDF. Un lock y un hilo de cálculo serializan la inferencia de esta configuración inicial.

El paquete debe provenir del proceso local controlado del proyecto. Sus hashes detectan alteraciones, pero no son una firma de autenticidad de terceros: no se cargarán modelos subidos por usuarios. Las restricciones y requisitos de entorno de Joblib/scikit-learn se describen en la [documentación oficial de persistencia](https://scikit-learn.org/stable/model_persistence.html).

## Verificación aislada

```powershell
.\venv\Scripts\python.exe scripts/verify_reproduction.py
```

El script crea una copia nueva de los archivos listados por Git, incluyendo los cambios actuales de desarrollo. Comprueba que no contiene corpus, checkpoint ni entorno previo; crea un venv e instala requirements.txt. Ejecuta el comando full, descargando/preparando datos y reajustando el modelo. Verifica la identidad aprendida y que los tres archivos históricos conservan sus bytes. Es una copia limpia del estado en prueba, no una afirmación de haber desplegado API/frontend ni de haber probado otros sistemas operativos.

Se conserva en una carpeta ignorada de ml/artifacts para inspección y registra el resultado en reports/reproducibility.json. Las pruebas pequeñas están en tests/test_artifacts.py. Los comandos y resultados observados están en FASE-E-REPRODUCIBILIDAD.md.

## Alcance siguiente

La Fase F integrará Predictor con Django/DRF. La medición actual llama inferencia local; la latencia HTTP, workers y RAM del servidor se medirán cuando exista la API. No se realizaron cambios de modelo para mejorar los resultados de test.