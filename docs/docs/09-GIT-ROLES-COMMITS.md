# 09 — Git, responsabilidades y evidencia auténtica para el ingeniero

## Regla de honestidad (importantísima)

El PDF exige: **cada integrante usa su propia cuenta**, rama por funcionalidad, PR revisado por otro integrante, commits frecuentes en distintas fechas, `CONTRIBUCIONES.md` fiel al historial y **al menos un aporte significativo de NLP o ML por persona**. Está prohibido atribuir commits a quien no los hizo o inventar autores.

**Situación declarada: una persona pretende hacer todo el proyecto.** Organizar el trabajo por áreas sirve, pero **NO** convertir áreas en «cuatro integrantes ficticios». Si el docente acepta trabajo individual, pedir por escrito excepción para mínimo de integrantes y revisión de PR por otro integrante. Si exige grupo, reunir 3–4 personas reales que hagan y puedan explicar cambios reales.

## Distribución de responsabilidades (no identidades)

| Área | Entregables | Evidencia útil |
|---|---|---|
| A — Datos y EDA | Dataset, limpieza, auditoría, notebook | Commits en `src/data`, `notebooks`, `docs/DATASET.md` |
| B — NLP | stop words, stemming/lematización, n-gramas, TF-IDF | Commits en `src/nlp`, tests, comparativas |
| C — ML | baseline, CV, métricas, errores, serialización | Commits en `src/models`, `reports`, `artifacts` |
| D — Backend | rutas, validaciones, modelos cargados, tests | Commits en `api`, `tests/test_api.py` |
| E — Frontend | predicción, traza, métricas, manejo de errores | Commits en `frontend` |
| F — QA y docs | e2e, README, informe y defensa | Commits `tests`, `docs`, `README.md` |

Si hay un grupo real, dividir áreas entre personas y garantizar un aporte de NLP/ML auténtico por todas.

## Flujo Git recomendado por tarea

```bash
# Una sola vez, usando TU nombre y TU email reales
git config user.name "TU_NOMBRE_REAL"
git config user.email "TU_CORREO_REAL"

git switch main
git pull --ff-only
git switch -c feat/data-eda
# Implementar y probar un cambio concreto
git status
git add src/data/ tests/test_data.py
git commit -m "feat(data): verificar esquema y etiquetas del corpus"
git push -u origin feat/data-eda
# Abrir PR en GitHub; solicitar revisión REAL cuando haya revisor real.
```

Al integrar, usar merge commit o método que **preserve trazabilidad**, sin forzar push ni compactar todos los cambios en uno. Cada módulo abre su propia rama, por ejemplo `feat/nlp-negaciones`, `feat/ml-logreg`, `feat/api-predict`, `feat/web-stars`, `test/e2e-pipeline`.

## Cómo redactar commits que demuestren conocimiento

**Formato** `tipo(alcance): cambio específico con intención`

- Mal: `avance`, `final`, `fix`, `todo`, `version 2`, `mi trabajo`, `update files`.
- Bien: `feat(nlp): conservar no ni y sin para modelar negacion en reseñas`.
- Bien: `perf(ml): limitar vocabulario tfidf para reducir memoria sin densificar`.
- Bien: `fix(api): mapear etiqueta cero a una estrella en respuesta`.
- Bien: `test(api): rechazar reseñas vacias y demasiado largas`.

En descripción extensa de commit (o PR) documentar: **qué cambió**, **por qué**, **cómo se verificó**, **alternativas consideradas** y **qué archivo lo demuestra**.

## Plan ejemplo de PR reales por área

| PR/branch | Cambio verificable | Tests / documentación |
|---|---|---|
| `feat/data-audit` | dataset+schema, conteos, nulos | `test_data.py`, EDA |
| `feat/nlp-normalization` | normalizador+casos de símbolos | `test_nlp.py` |
| `feat/nlp-morphology` | stem/lemma y comparación | tabla de NLP |
| `feat/ml-naive-bayes` | baseline NB y métricas | `test_models.py` |
| `feat/ml-logreg` | segundo candidato y CV | reporte de CV |
| `feat/reproducible-train` | CLI quick/full, manifest, joblib | `test_artifacts.py` |
| `feat/api-rest` | endpoints, Pydantic, errores | `test_api.py` |
| `feat/web-inference` | formulario real y barras | tests React |
| `feat/web-laboratory` | traza NLP y matriz | integración real |
| `docs/final-report` | informe, README, CONTRIBUCIONES | checklist rúbrica |

No hagas 10 commits falsos de documentos antes de implementar. Los ejemplos son **secuencia futura**: realizar cambio → correr test → commit → PR → revisión auténtica → merge.

## Si trabajas solo (con aprobación)

- Una sola cuenta, autores verdaderos y un `CONTRIBUCIONES.md` que enumere **una persona** y todas sus tareas.
- Puedes separar ramas y PR para orden, pero **autorrevisión ≠ revisión por compañero**. Señalar la diferencia y pedir autorización al ingeniero.
- No agregar colaboradores fantasma, no falsificar `Co-authored-by`, no cambiar `git author` para simular equipo.
- Hacer commits conforme avances, repartidos en los días reales de trabajo; no alterar fechas ni reescribir historial.

## Comprobación de evidencia para defensa

```bash
git log --date=short --format='%h %ad %an %s' --reverse
git shortlog -sne
git show --stat <HASH_DE_TU_COMMIT>
git show <HASH_DE_TU_COMMIT>
git tag -a entrega-final -m "Entrega del proyecto integrador ReviewIQ"
git push origin entrega-final
```

Crear `entrega-final` **únicamente** sobre el commit final aceptado y antes del límite de entrega. No modificar historia del tag; cambios de defensa se hacen **después** en commits nuevos claramente diferenciados.

## Aceptación

- [ ] Git contiene trabajo real, distribuido y testeado.
- [ ] PR tienen descripción y revisión verdadera, o consta la excepción individual autorizada.
- [ ] No existe falsa atribución; CONTRIBUCIONES coincide con logs.
- [ ] El docente agregado como colaborador desde el inicio conforme a instrucciones.
- [ ] Cada autor real puede explicar sus commits y cambios en vivo.
