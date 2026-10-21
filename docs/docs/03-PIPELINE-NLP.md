# 03 — Responsabilidad: NLP en español y pipeline reutilizable

## Objetivo

Implementar **todas** las técnicas del PDF, mostrar entrada/salida por paso y comparar alternativas antes de elegir el pipeline final. La transformación debe ser **idéntica** en entrenamiento y en la API: serializar los mismos objetos del pipeline.

## Procesamiento propuesto y pruebas

| Etapa | Conducta explícita | Casos de prueba |
|---|---|---|
| Normalizar | Unicode NFKC, minúsculas, espacios; conservar o registrar tildes según experimento | `MALÍSIMO`, `envió` frente a `envio` |
| Puntuación | Sustituir/segmentar y justificar signos | `no funciona!!!`, `¿bueno?` |
| URL | Token marcador `urltoken` si se conserva señal; no enviar URL a red | `https://...` |
| Números | Marcador `numerotoken` o conservar dígitos, comparar y justificar | `2 días`, `5 estrellas`, `128 GB` |
| Emojis | Conservar emoji como token o mapear a categoría; documentar decisión | `😍`, `😡` |
| Tokenización | Separar palabras y tokens marcadores sin perder negación | `no me gustó`, `sin garantía` |
| Stop words | Lista española fijada; proteger `no`, `ni`, `sin`, `nunca`, `jamás` | `no es bueno` |
| Stemming | SnowballStemmer('spanish'), con raíces visibles | `funcionando`, `funciona` |
| Lematización | spaCy es_core_news_sm, sin generación; comparar frente a stemming | `compré` → lema esperado por versión |
| N-gramas | Unigramas `(1,1)` contra uni+bi `(1,2)` | `no funciona` debe poder representarse |
| TF-IDF | max_features=50.000 (punto inicial), min_df=2, max_df=0.98, sublinear_tf=True, dtype=float32 | Vocabulario y sparsity medidas |

Los marcadores y reglas de normalización son **decisiones propuestas**, no prescripciones exactas del profesor; la obligación del PDF es implementar, mostrar y justificar cada aspecto.

## Implementación responsable

- Usar `src/nlp/normalize.py`, `tokenize.py`, `stopwords_es.py`, `morphology.py`, `pipeline.py`, `trace.py`.
- Clase `ReviewTextPreprocessor(BaseEstimator, TransformerMixin)` importable desde módulo (no `lambda`, no objeto anónimo). Debe respetar `fit`, `transform`, `get_params`, `set_params`, para que `GridSearchCV` pueda clonar el pipeline.
- Aplicar el preprocesador a texto, luego `TfidfVectorizer` con tokenización coherente; **evitar tokenizar de nuevo con una política incompatible**. Por ejemplo, transformar a texto normalizado `" ".join(tokens)` y configurar `TfidfVectorizer` para esos tokens; testear que la secuencia coincide.
- No duplicar la eliminación de stop words dentro del vectorizador y dentro del preprocesador.
- **Medición exigida:** comparar modo stemming vs lematización en muestra fija de entrenamiento, con validación; seleccionar según Macro-F1 y coste CPU/RAM, no por intuición.
- **Medición exigida:** comparar `(1,1)` vs `(1,2)` a igualdad de splits y configuración.
- Evitar cargar spaCy por reseña. Si se usa, `nlp.pipe()` en lotes y deshabilitar componentes innecesarios, cacheando con controles. En inference, si gana lematización, el mismo modelo español y la misma versión deben estar instalados.
- El preprocesado pesado se puede cachear **por configuración y split sin cruzar datos**; la configuración final debe entrenarse siempre con train. Nunca ajustar IDF con validación/test.
- `Pipeline` guarda **etapas y parámetros**; el backend simplemente lo carga y llama `.predict_proba()`.

## Salida de traza real para el frontend

```json
{
  "original": "No me gustó!!! Llegó roto 😡",
  "normalized": "no me gustó llegó roto 😡",
  "tokens": ["no", "me", "gustó", "llegó", "roto", "😡"],
  "removed_stopwords": ["me"],
  "processed_tokens": ["no", "gust", "lleg", "rot", "😡"],
  "method": "stemming",
  "ngram_range": [1, 2]
}
```

**Solamente ilustrativo:** tokens resultantes exactos, tratamiento de emoji, tildes y stop words deben salir de la ejecución real, no codificarse a mano en la API.

## Controles técnicos

- Stop words españolas **versionadas y testeadas**. Cambiar `no` debe requerir reentrenar y producir artefacto con identificador nuevo.
- Mostrar ejemplos originales y transformaciones sin alterar la política usada al entrenar.
- Todo cambio en `ngram_range` o preprocesado invalida el vectorizador anterior y obliga a reconstruir el pipeline.
- Probar que `.predict_proba([texto])` coincide antes y después de serializar.

## Archivos, aceptación y commits

Archivos: `src/nlp/*`, `tests/test_nlp.py`, `reports/nlp_comparison.csv`, `docs/NLP_DECISIONS.md`.

- [ ] Normalización, tokens y stop words con tests para negaciones.
- [ ] Stemming **y** lematización implementados y comparados.
- [ ] Unigramas frente a unigramas+bigramas evaluados.
- [ ] TF-IDF y tamaño de vocabulario reportados.
- [ ] API traza exactamente las mismas etapas que el pipeline.

Commits de ejemplo:

- `feat(nlp): agregar normalizacion configurable para resenas en español`
- `feat(nlp): preservar negaciones y tokenizar urls emojis y numeros`
- `feat(nlp): implementar stemming y lematizacion como estrategias alternativas`
- `test(nlp): comprobar coherencia de tokens y vectorizacion en prediccion`
- `docs(nlp): comparar unigramas bigramas y estrategias morfologicas`
