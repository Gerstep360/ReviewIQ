# NLP español: políticas y comparación experimental

Fase C implementada en `ml/nlp/`, según la arquitectura Django/DRF del proyecto. El backend futuro importará este módulo; no debe copiar su lógica en las vistas.

## Contrato compartido

`ReviewTextPreprocessor` implementa fit, transform, get_params y set_params de scikit-learn. Sus parámetros pueden clonarse para búsquedas futuras. No aprende vocabulario ni usa etiquetas: el aprendizaje de TF-IDF se limita a train.

`build_pipeline` compone el transformador, TF-IDF y, opcionalmente, un clasificador. `trace_pipeline` llama al mismo transformador y al analizador real del vectorizador. Muestra texto normalizado, tokens, stop words retiradas, tokens procesados y n-gramas. Con un vectorizador ajustado también distingue rasgos conocidos y desconocidos. La traza aún no es un endpoint HTTP.

Las probabilidades y trazas se verificaron antes y después de serializar pipelines locales de prueba con Joblib. Se congelan stop words y parámetros al hacer fit; cambiar parámetros del transformador exige volver a ajustarlo y reentrenar el pipeline completo. Los cambios en stop words, normalización o n-gramas requieren vocabulario y artefacto nuevos. La fase E se encargará del manifest del modelo de producción.

## Políticas explícitas

| Etapa | Política de este experimento |
|---|---|
| Unicode | NFKC y casefold; espacios colapsados |
| Tildes | Se conservan al normalizar. Existe una opción experimental de quitar marcas diacríticas, que también convierte ñ en n; no se evaluó ni seleccionó aquí |
| Puntuación | Se reemplaza por espacios, evitando unir palabras. No se conservan intensidad ni límites de oración |
| URL | Marcador urltoken, sin visitar el enlace |
| Números | Marcador numerotoken; secuencias decimales cuentan como un número. La opción keep existe pero no se comparó aquí |
| Emojis | Marcadores específicos emojitoken_<nombre>, mediante la biblioteca emoji. Se reconocen secuencias completas, incluyendo ZWJ; la opción remove no se comparó aquí |
| Tokens | Una sola separación por espacios tras normalizar; el vectorizador usa la misma función importable, sin otra política de regex |
| Stop words | Lista propia y explícita en stopwords.py, versión reviewiq-es-1, sin descargas de corpus |
| Negaciones | Se protegen no, ni, sin, nunca, jamás/jamas y negadores adicionales. No se quitan ni se reducen morfológicamente |
| Stemming | Snowball español de NLTK; no necesita descargar datos de NLTK |
| Lematización | es_core_news_sm 3.8.0 en CPU, cacheado por proceso; nlp.pipe por lotes de 128, un proceso |
| TF-IDF | Matriz CSR float32, máximo 50.000 rasgos, min_df=2, max_df=0.98, sublinear_tf=True |

Los marcadores quedan protegidos de stemming y lematización. Las palabras de valoración, como bien, mal, bueno, malo, mejor y peor, no forman parte de la lista base de stop words. El vectorizador no vuelve a quitar stop words ni a normalizar mayúsculas/tildes.

Para la lematización se crea un Doc con los tokens exactos del normalizador. Los auxiliares y pronombres se conservan temporalmente como contexto gramatical del modelo; la salida aplica la misma máscara de stop words a los lemas correspondientes. Se excluyen parser, senter y ner; se mantienen tok2vec, morphologizer, attribute_ruler y lemmatizer. Los nombres de componentes y las versiones están fijados; no se descarga ningún recurso por reseña.

## Comparación realizada

Se usó una muestra estratificada fija de **20.000 filas** de las 197.572 de train preparado, con semilla 42, y las **5.000 filas de validation**. El baseline es MultinomialNB con alpha=1. No se abrió test, no se hizo CV ni se eligió el clasificador definitivo. El manifiesto del experimento incluye hashes de archivos preparados, IDs de la muestra, configuración, fuentes NLP y stop words.

| Morfología | N-gramas | Macro-F1 validation | Accuracy validation | Vocabulario |
|---|---|---:|---:|---:|
| Stemming | (1,1) | 0,4467 | 0,4490 | 5.710 |
| Stemming | (1,2) | **0,4783** | 0,4812 | 36.851 |
| Lematización | (1,1) | 0,4373 | 0,4390 | 8.291 |
| Lematización | (1,2) | 0,4689 | 0,4718 | 36.737 |

Stemming con uni+bigramas dio el mejor Macro-F1 y menor coste de morfología. Se recomienda como punto de partida experimental para la fase D. No se modifica automáticamente una supuesta configuración ganadora de producción: la comparación con regresión logística, la CV y el entrenamiento completo siguen pendientes.

En la ejecución registrada, el preprocesamiento de las 25.000 reseñas tomó 13,38 s de pared / 13,19 s de CPU con stemming y 81,63 s / 79,48 s con lematización. El pico RSS observado por proceso fue de 272,98 MiB y 409,61 MiB, respectivamente. Para stemming+(1,2), la matriz train tiene 442.474 valores no nulos, 99,9400 % de dispersión y ocupa 3,45 MiB en CSR.

Cada morfología se midió en un proceso separado, con un hilo de cálculo. El preprocesamiento se reutiliza para sus dos configuraciones de n-gramas: sus tiempos no deben sumarse dos veces. RSS es el pico del proceso completo muestreado cada 50 ms, incluyendo intérprete, datos y recursos; no mide únicamente el modelo ni es un pico exacto por candidato. CPU/pared excluyen iniciar el intérprete. Los valores completos están en `reports/nlp_comparison.csv` y `.json`; los tiempos y memoria varían con la máquina.

## Reproducción y límites

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ml.nlp.compare
.\venv\Scripts\python.exe -m ml.nlp.trace --text "No me gustó, sin garantía tras 2 días" --morphology lemmatization
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_nlp.py -v
```

`reports/nlp_trace_examples.json` contiene la salida real de ambas estrategias sobre una frase sintética escrita para demostración, sin reseñas del corpus. Las trazas de ejemplo no tienen un vocabulario TF-IDF ajustado ni son predicciones. No se guardó un modelo experimental como artefacto final.

Las políticas de tildes, números y emojis están configuradas y probadas funcionalmente, pero no se compararon todas sus alternativas por F1. La lematización usa un modelo entrenado en noticias y puede cometer errores en reseñas; Snowball reduce palabras a raíces, no a lemas lingüísticos. La protección de negaciones no equivale a modelar su alcance sintáctico, y los bigramas no resuelven ironía ni contexto largo.

## Fuentes y versiones

- [NLTK SnowballStemmer](https://www.nltk.org/api/nltk.stem.snowball.html), NLTK 3.10.4.
- [Procesamiento por lotes de spaCy](https://spacy.io/usage/processing-pipelines), spaCy 3.8.16.
- [Modelo oficial es_core_news_sm 3.8.0 y checksum](https://github.com/explosion/spacy-models/releases/tag/es_core_news_sm-3.8.0). Su metadata declara GNU GPL 3.0; el proyecto referencia el wheel oficial y no copia sus binarios al repositorio.
- [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), scikit-learn 1.9.1.
- [Biblioteca emoji](https://emoji-python.readthedocs.io/en/stable/), versión instalada 2.16.0.

Las dependencias están fijadas en requirements.txt y requirements-dev.txt; config.json guarda los candidatos y las políticas del experimento.