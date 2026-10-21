# Fase C — Pipeline NLP español reutilizable

Estado: implementada y ejecutada el 21 de octubre de 2026. Se adaptan las rutas src/nlp de la guía 03 a ml/nlp, según ARQUITECTURA.md.

## Cambios y decisiones

Se implementaron normalización configurable, tokenización única, lista propia de stop words, protección de negaciones, Snowball, spaCy por lotes, transformador scikit-learn clonable, factorías de TF-IDF/Pipeline y trazas ligadas a las mismas etapas. Se fijaron las dependencias y el modelo español oficial mediante URL con SHA-256.

Se compararon dos estrategias morfológicas y dos rangos de n-gramas sobre la misma muestra estratificada de 20.000 filas de train y 5.000 de validation. MultinomialNB actúa como baseline fijo para medir NLP: esto no sustituye la fase D de comparación/selección de clasificadores ni la fase E de artefactos finales. Test no se abre.

Archivos principales: ml/nlp/{normalize,tokenize,stopwords,stem_lemma,transformer,pipeline,trace,compare}.py, config.json, requirements.in/txt, requirements-dev.txt, tests/test_nlp.py, reports/nlp_comparison.csv/json, reports/nlp_trace_examples.json y docs/NLP.md.

## Verificación ejecutada

```text
venv/Scripts/python.exe -m unittest discover -s tests -p test_nlp.py -v
  Ran 7 tests
  OK

venv/Scripts/python.exe -m ml.nlp.compare
  Comparando stemming sobre train/validation...
  Comparando lemmatization sobre train/validation...
  morphology: stemming
  ngram_min: 1
  ngram_max: 2
  macro_f1_validation: 0.4782833223643447

venv/Scripts/python.exe -m ml.nlp.trace --text 'No me gusto!!! Llego roto. Sin garantia 2 dias https://ejemplo.invalid' --morphology stemming
  JSON con normalización, tokens, stop words retiradas, tokens procesados y n-gramas
  processed_text: no gust lleg rot sin garanti numerotoken dias urltoken

venv/Scripts/python.exe -m pip check
  No broken requirements found.
```

Las siete pruebas comprueban Unicode/tildes, URL, números decimales y emojis completos; negaciones y marcadores en ambas estrategias; lema español real y stemming; clonación y necesidad de refit tras cambiar parámetros; TF-IDF CSR float32 coherente con la traza y sin ajustar sobre holdout; probabilidades/trazas idénticas tras Joblib; muestreo determinista sin un archivo test.

Las pruebas usan frases sintéticas, sin red ni corpus externo. La comparación real es un experimento requerido por docs, independiente de las pruebas pequeñas. Los informes registran las métricas, CPU/pared, RAM observada, vocabulario, sparsity y procedencia.

## Requisitos cubiertos y pendientes

- Normalización, tokenización y negaciones probadas.
- Stemming y lematización implementados y comparados con validación.
- Unigramas frente a uni+bigramas medidos a igualdad de datos y configuración.
- TF-IDF disperso con vocabulario, nnz y memoria de matriz reportados.
- Traza comparte el transformador y el analizador; su endpoint HTTP se implementará en la fase F.
- Uso de IA actualizado en el informe técnico y contribuciones.

La recomendación experimental es stemming+(1,2), F1 macro de validación 0,4783. No se evaluaron todas las políticas opcionales ni se ejecutó CV. La selección puede cambiar al comparar los dos clasificadores en la fase D. Las cifras no corresponden al test final ni a una precisión de producción.

Commit del bloque: feat(nlp): implementar pipeline espanol y comparar variantes con validacion.