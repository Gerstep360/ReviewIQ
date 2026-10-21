"""Métricas y diagnóstico agregado, sin publicar reseñas ni IDs del corpus."""

import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, mean_absolute_error, precision_recall_fscore_support

from ml.data.validate import Review

LABELS = np.arange(5)


def labels_to_stars(labels) -> np.ndarray:
    values = np.asarray(labels)
    if not np.issubdtype(values.dtype, np.integer) or not np.isin(values, LABELS).all():
        raise ValueError("Las etiquetas deben ser enteros de 0 a 4.")
    return values + 1


def validate_probabilities(probabilities, classes) -> np.ndarray:
    values = np.asarray(probabilities)
    if not np.array_equal(np.asarray(classes), LABELS):
        raise ValueError("El clasificador debe conservar las cinco clases en orden 0–4.")
    if values.ndim != 2 or values.shape[1] != 5 or not np.isfinite(values).all():
        raise ValueError("Matriz de probabilidades inválida.")
    if (values < 0).any() or (values > 1).any() or not np.allclose(values.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError("Las probabilidades deben estar entre 0 y 1 y sumar uno.")
    return values


def classification_metrics(y_true, y_pred) -> dict:
    actual, predicted = np.asarray(y_true), np.asarray(y_pred)
    true_stars, predicted_stars = labels_to_stars(actual), labels_to_stars(predicted)
    if len(actual) == 0 or actual.shape != predicted.shape or actual.ndim != 1:
        raise ValueError("Se requieren vectores no vacíos del mismo tamaño.")
    precision, recall, f1, support = precision_recall_fscore_support(actual, predicted, labels=LABELS, zero_division=0)
    return {
        "rows": len(actual), "macro_f1": float(f1_score(actual, predicted, labels=LABELS, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(actual, predicted)),
        "mae_stars": float(mean_absolute_error(true_stars, predicted_stars)),
        "per_class": [{"label": int(label), "stars": int(label + 1), "precision": float(precision[label]), "recall": float(recall[label]), "f1": float(f1[label]), "support": int(support[label])} for label in LABELS],
        "confusion_matrix": confusion_matrix(actual, predicted, labels=LABELS).tolist(),
        "ordinal_error_counts": {str(distance): int((np.abs(actual - predicted) == distance).sum()) for distance in range(5)},
    }


def error_analysis(reviews: list[Review], predictions) -> dict:
    predicted = np.asarray(predictions)
    errors = []
    groups = Counter()
    confusion_pairs = Counter()
    for position, (review, prediction) in enumerate(zip(reviews, predicted)):
        if review.label == prediction:
            continue
        words = re.findall(r"[^\W\d_]+", review.text.casefold())
        tags = []
        if len(words) <= 8:
            tags.append("short_text_at_most_8_words")
        if set(words) & {"no", "ni", "sin", "nunca", "jamás", "tampoco"}:
            tags.append("contains_negation")
        if set(words) & {"pero", "aunque"}:
            tags.append("contains_contrast_connector")
        if review.label in (1, 2, 3):
            tags.append("intermediate_rating")
        distance = abs(review.label - int(prediction))
        groups.update(tags)
        confusion_pairs[(review.label + 1, int(prediction) + 1)] += 1
        errors.append({"row_position_1based": position + 1, "actual_stars": review.label + 1, "predicted_stars": int(prediction) + 1, "distance": distance, "word_count": len(words), "tags": tags})
    return {
        "errors": len(errors), "groups_non_exclusive": dict(groups),
        "largest_confusions": [{"actual_stars": pair[0], "predicted_stars": pair[1], "count": count} for pair, count in confusion_pairs.most_common(8)],
        "cases_for_local_review": sorted(errors, key=lambda row: -row["distance"])[:8],
        "interpretation": "Observed text features, not causal diagnoses. Sarcasm/mixed sentiment require human review. Positions allow local inspection without publishing text or review IDs.",
    }


def evaluate_pipeline(pipeline, reviews: list[Review]) -> tuple[dict, np.ndarray]:
    probabilities = validate_probabilities(pipeline.predict_proba([row.text for row in reviews]), pipeline.classes_)
    predictions = np.asarray(pipeline.classes_)[np.argmax(probabilities, axis=1)]
    metrics = classification_metrics([row.label for row in reviews], predictions)
    metrics["probabilities_sum_to_one"] = True
    metrics["error_analysis"] = error_analysis(reviews, predictions)
    return metrics, probabilities


def plot_confusion(metrics: dict, path: Path, *, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matrix = np.asarray(metrics["confusion_matrix"])
    figure, axis = plt.subplots(figsize=(6.5, 5.5), layout="constrained")
    picture = axis.imshow(matrix, cmap="Blues")
    for (row, column), value in np.ndenumerate(matrix):
        axis.text(column, row, str(value), ha="center", va="center", color="white" if value > matrix.max() / 2 else "black")
    axis.set(title=title, xlabel="Estrellas predichas", ylabel="Estrellas reales", xticks=range(5), yticks=range(5), xticklabels=range(1, 6), yticklabels=range(1, 6))
    figure.colorbar(picture, ax=axis, label="Reseñas")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)
