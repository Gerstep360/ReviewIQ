# 00 — Matriz de trazabilidad exacta con el enunciado

Documento base: `Proyecto_Integrador(1).pdf` (7 páginas). **Verificar cada casilla con evidencia reproducible**, no con afirmaciones.

| Ref. del PDF | Obligación | Implementación ReviewIQ | Evidencia concreta |
|---|---|---|---|
| P1 §1 | Grupo de 3–4, entrega y defensa | Consultar aprobación si desarrolla 1 persona | Autorización o conformación real del grupo |
| P2 §4 | Problema basado en texto y modelos del curso | Clasificación de reseña a 5 clases (estrellas) | `docs/PROBLEMA.md`, demo |
| P2 §4 | Datos: fuente, licencia y fecha | Amazon Reviews Multi ES + revisión de licencia | `docs/DATASET.md` y snapshot de revisión |
| P3 §5.1 | EDA: clases, longitudes, palabras, nulos | Notebook / reporte automático | `notebooks/01_eda.ipynb`, gráficos |
| P3 §5.1 | Split estratificado y semilla fija | Respetar splits oficiales, verificar balance, semilla 42; CV estratificada en train | Conteos, código, reportes |
| P3 §5.1 | Desbalance justificado | Verificar, no asumir; intervención solo si realmente procede | Gráfico y justificación |
| P3 §5.2 | Normalización | Política de mayúsculas, tildes, puntuación, números, URL y emojis | Antes/después + tests |
| P3 §5.2 | Tokenización | Tokens + casos españoles | Vista de NLP + test |
| P3 §5.2 | Stop words españolas | Lista explícita, conservar 'no', 'ni', 'sin' si así se decide | Versión y test |
| P3 §5.2 | Stemming **y** lematización | Implementar ambos, comparar, elegir uno | Experimentos y tabla F1 |
| P3 §5.2 | N-gramas | (1,1) frente a (1,2) | Tabla comparativa |
| P3 §5.2 | TF-IDF | `min_df`, `max_df`, `max_features`, `dtype` documentados | Config + reporte del vocabulario |
| P3 §5.3 | 1 o 2 modelos del curso | LogisticRegression y MultinomialNB | Código de entrenamiento |
| P4 §5.3 | Métricas y comparación | Macro-F1, accuracy, MAE estrellas, matriz de confusión | JSON y gráficos del test |
| P4 §5.3 | Ajuste con validación cruzada | StratifiedKFold en train sin test | Registro de CV + configuración |
| P4 §5.3 | Análisis de errores | Confusiones 2↔3, 4↔5, etc. con ejemplos anonimizados | Informe de errores |
| P4 §5.4 | Un comando reproducible | `python -m src.models.train --mode full` | Reejecución documentada |
| P4 §5.4 | Pipeline y modelos guardados | `artifacts/reviewiq_pipeline.joblib` con config y manifest | Artefactos verificables |
| P4 §5.4 | Versiones y seed | Lockfile, Python fijo y semilla 42 | Archivo lock y README |
| P4 §5.5 | API REST / estados / validación / pruebas | `/api/v1/predict`, `/api/v1/metrics`, `/api/v1/health`; tests | OpenAPI + pytest |
| P4 §5.6 | Frontend y clasificación | Formulario, estrellas y probabilidades | Demo real contra API |
| P4 §5.6 | Etapas de NLP visibles | Normalizado, tokens, stop words, stem/lema | Vista 'Laboratorio NLP' |
| P4 §5.6 | Panel y comparación | Tabla 2 modelos, matriz de confusión | Vista 'Modelos' |
| P4 §5.7 | README instalar desde cero | Instalación CPU y recuperación de artefactos | Prueba en clon limpio |
| P5 §6 | Git real: identidad, PR revisados, commits regulares | Seguir `09-GIT-ROLES-COMMITS.md` | Historial y PR reales |
| P5 §6 | Todos aportan NLP/ML | Cada participante real hace aporte significativo | PR y código |
| P5/6 §7 | Entregables + etiqueta | Código, notebook, docs, slides, `CONTRIBUCIONES.md`, tag | Checklist final |
| P6 §8 | Cambio en vivo | Flags CLI, tests y estructura modular | Ensayos registrados |
| P6/7 §9 | 40 pts grupo, 60 individual | Métricas, integración, defensa, contribución | Evidencias y respuestas |
| P7 §10 | Atribución y declaración de IA | Créditos y declaración transparente | Informe técnico |

## Alertas del enunciado

- La tabla del docente sugiere modelos de **regresión** para *estimar puntuación*, pero permite otro algoritmo visto en clase si se justifica. ReviewIQ plantea **clasificación ordinal de cinco categorías**, no regresión numérica. Argumentar esta elección claramente.
- Los ejemplos `[completar]` del PDF **no son reglas fijadas**. Confirmar con el ingeniero mínimo de registros y fecha de aprobación para temas propios. ReviewIQ encaja en dominio de reseñas sugerido.
- Para 1 persona, el requisito de PR revisado por **otro integrante** no puede cumplirse honestamente sin otro revisor; pedir excepción formal.

## Regla de cierre

No marcar terminado por tener interfaz bonita; marcar cuando exista código, test, evidencia y commit correspondiente. Después de cualquier cambio NLP/modelo, reentrenar y regenerar métricas cuando sea necesario.
