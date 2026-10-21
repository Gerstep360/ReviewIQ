# Rendimiento observado — Fase E

Mediciones reales del 21 de octubre de 2026 en Windows 10.0.26200, Python 3.11.0, CPU AMD64 Family 25 Model 120 Stepping 0 (12 procesadores lógicos) y 13,72 GiB de RAM total. Dependencias de requirements.txt; sin GPU. Se limita el cálculo a un hilo mediante threadpoolctl y las variables OMP_NUM_THREADS, OPENBLAS_NUM_THREADS y MKL_NUM_THREADS.

## Construcción

| Ejecución | Filas de train | Tiempo de pared | CPU | Pico RSS del proceso |
|---|---:|---:|---:|---:|
| Quick, datos preparados verificados en caché | 20.000 | 61,36 s | 59,63 s | 419,63 MiB |
| Full, copia aislada sin corpus ni checkpoint | 197.572 | 635,16 s (10,59 min) | 624,42 s | 1.205,18 MiB |

El tiempo registrado comienza después de verificar configuración y termina después de obtener/ajustar/verificar el modelo y calcular las métricas que corresponden. No incluye crear el entorno, instalar dependencias, serializar ni ejecutar el benchmark posterior. El pico RSS sí cubre el bloque de exportación. El ajuste full reproduce parámetros congelados; no repite el cribado ni la CV de D, por eso no es comparable directamente con los 19,57 minutos de aquella selección completa.

## Inferencia local

Cada benchmark se ejecutó en un proceso nuevo. Primero carga y verifica el paquete, mide una primera predicción que incluye la carga diferida de spaCy, realiza tres llamadas de calentamiento y mide treinta predicciones individuales y siete lotes de cien reseñas sintéticas. Los percentiles de lote son por llamada completa de cien textos.

| Medida | Paquete full de despliegue | Quick experimental |
|---|---:|---:|
| Artefacto Joblib | 1.526.934 bytes | 1.095.627 bytes |
| Carga verificada del paquete | 0,278 s | 0,219 s |
| Primera predicción | 0,975 s | 1,359 s |
| Individual p50 / p95 | 9,22 / 11,38 ms | 6,52 / 7,66 ms |
| Lote 100 p50 / p95 | 96,24 / 101,14 ms | 70,26 / 73,13 ms |
| RSS tras inferencia | 233,94 MiB | 232,45 MiB |
| Pico RSS muestreado | 245,68 MiB | 243,62 MiB |

La primera medición de full dentro de la copia aislada obtuvo p50/p95 individuales de 8,73/9,86 ms y pico RSS de 246,63 MiB. Después se reexportó ese mismo estado verificado con los metadatos finales del manifiesto en el workspace y se midió su paquete de despliegue (columna full). Las diferencias entre ejecuciones son observaciones, no mejoras del modelo. El tamaño binario varía ligeramente por serialización; ambas exportaciones tienen exactamente la misma huella del estado aprendido.

## Evidencia y límites

- reports/reproducibility.json: reconstrucción aislada y primer benchmark full.
- reports/deployment_manifest.json y reports/full_build.json: manifiesto final y procedencia del paquete local de despliegue.
- reports/performance.json: benchmark de ese paquete final.
- reports/quick_reproduction.json: paquete, construcción, benchmark y métricas de validation de quick.

Las latencias son de Predictor.predict local y todavía no incluyen Django, HTTP ni concurrencia. Siete observaciones de lote son una muestra pequeña. RSS se muestrea cada 50 ms e incluye intérprete y bibliotecas, pero no otros procesos ni el coste de instalar dependencias. Los bytes de Joblib no incluyen el entorno ni el modelo spaCy instalado. No se presentan estos valores como garantías para otro equipo.

Para repetir la medición sin entrenar:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
.\venv\Scripts\python.exe -m ml.inference.benchmark --package-dir ml/artifacts/full
```

El comando guarda nuevas observaciones en el paquete ignorado; no reemplaza automáticamente los informes versionados ni consulta el corpus.
