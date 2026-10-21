# 13 — Fuentes, licencia, atribución y declaración de IA

## Requisitos del profesor

PDF P2: documentar origen, licencia y fecha de obtención del dataset. PDF P7: citar reutilización y declarar herramientas de IA utilizadas. **Guardar fecha/revisión exactas cuando se descargue**; no registrar falsos hashes.

## Dataset de trabajo

- **SetFit/amazon_reviews_multi_es** (convenience version): https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es
- **Archivos accesibles:** https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es/tree/main
- **Corpus académico original:** *The Multilingual Amazon Reviews Corpus* (Keung, Lu, Szarvas y Smith, EMNLP 2020), fuente documental: https://aclanthology.org/2020.emnlp-main.369/
- **Términos reproducidos en repositorio de corpus:** https://huggingface.co/datasets/mteb/amazon_reviews_multi/blob/main/amazon_reviews_multi.py
- **Documentación AWS:** https://github.com/awslabs/open-data-docs/blob/main/docs/amazon-reviews-ml/README.md

**Hecho crítico de licencia:** el corpus original concede licencia limitada para **investigación académica**, prohíbe la reventa, republicación y uso comercial (también investigación comercial), y prohíbe asociar/reidentificar reseñas con personas. Una tarjeta abreviada de un espejo no elimina esas condiciones. Antes de distribuir modelos/derivados o comercializar, revisar derechos del corpus y obtener un conjunto independiente de datos con permiso suficiente. El proyecto se presenta como **demostración académica**.

## Datos que registrar durante descarga

```text
Dataset repository: SetFit/amazon_reviews_multi_es
Revisión Hugging Face: [SHA REAL PENDIENTE]
Fecha de descarga: [FECHA REAL PENDIENTE]
Splits verificados: [TRAIN REAL] / [VALIDATION REAL] / [TEST REAL]
Licencia examinada: Corpus Amazon Reviews Multi, solo investigación académica
Hashes/snapshot: [REAL, SI SE TOMA]
Fuente de las etiquetas: valoración original, codificada label 0..4
```

No incluir reseñas personales en repositorio, no intentar buscar identidad de autor, no subir corpora completos ni espejos sin autorización.

## Citación bibliográfica sugerida

Keung, P., Lu, Y., Szarvas, G., & Smith, N. A. (2020). *The Multilingual Amazon Reviews Corpus*. Proceedings of EMNLP 2020. https://aclanthology.org/2020.emnlp-main.369/

(Verificar formato requerido por el docente y que la URL resuelva al artículo; el artículo se usa para atribución, no como licencia adicional.)

## Declaración de uso de asistentes IA (plantilla, rellenar fielmente)

> Durante la elaboración de ReviewIQ se utilizaron [HERRAMIENTAS REALES] para [CONSULTAS/DOCUMENTACIÓN/PROPUESTAS/CÓDIGO, SEGÚN SE HAYA HECHO]. Todo el código integrado fue revisado, probado y comprendido por [AUTORES REALES]. Las métricas provienen de entrenamientos reproducibles y no fueron generadas por un asistente. Se citan las fuentes de bibliotecas, métodos y dataset.

No afirmar que el ingeniero aprobó una entrega individual o uso comercial si no consta autorización.

## Fuentes metodológicas útiles

- scikit-learn `Pipeline`: https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
- scikit-learn `TfidfVectorizer`: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- scikit-learn `LogisticRegression`: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- scikit-learn `MultinomialNB`: https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html
- scikit-learn `StratifiedKFold`: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html
- FastAPI: https://fastapi.tiangolo.com/
- Hugging Face `datasets` carga: https://huggingface.co/docs/datasets/loading

## Commits

- `docs(license): describir restricciones academicas del corpus de amazon`
- `docs(report): citar fuente original del dataset y librerias usadas`
- `docs(ai): declarar uso real de asistentes durante el desarrollo`
