"""Renderiza análisis de errores guardados; no abre corpus ni vuelve a predecir."""

import json
from pathlib import Path

from ml.config import REPORTS_DIR


def render_errors(reports_dir: Path = REPORTS_DIR) -> Path:
    selection = json.loads((reports_dir / "model_selection.json").read_text(encoding="utf-8"))
    final = json.loads((reports_dir / "test_metrics.json").read_text(encoding="utf-8"))
    if selection["model_id"] != final["model_id"]:
        raise ValueError("La selección y las métricas no pertenecen al mismo modelo.")
    lines = ["# Análisis de errores del campeón", "", f"Modelo: `{selection['model_id']}`. Etiquetas convertidas a estrellas 1–5.", "", "Validation se usó para seleccionar; test solo estima el rendimiento del campeón ya congelado. No se retocó el modelo usando este análisis. No se publican textos ni IDs del corpus.", ""]
    for split, metrics in (("validation", selection["champion"]["metrics"]), ("test", final["metrics"])):
        analysis = metrics["error_analysis"]
        severe = sum(count for distance, count in metrics["ordinal_error_counts"].items() if int(distance) >= 2)
        weakest = min(metrics["per_class"], key=lambda row: row["f1"])
        lines += [f"## {split}", "", f"Errores: {analysis['errors']} de {metrics['rows']}; {severe} predicciones se alejan al menos dos estrellas. La clase con menor F1 es {weakest['stars']} estrellas (F1={weakest['f1']:.4f}).", "", "### Confusiones más frecuentes", "", "| Estrellas reales | Predichas | Casos |", "|---:|---:|---:|"]
        lines += [f"| {row['actual_stars']} | {row['predicted_stars']} | {row['count']} |" for row in analysis["largest_confusions"]]
        lines += ["", "### Rasgos observados entre los errores", "", "Los grupos se superponen; su presencia no demuestra la causa del error.", "", "| Rasgo | Casos |", "|---|---:|"]
        lines += [f"| {name} | {count} |" for name, count in analysis["groups_non_exclusive"].items()]
        lines += ["", "### Casos para inspección local", "", "Posiciones contadas desde 1 en el archivo del split evaluado. Validation corresponde al archivo preparado; test al JSONL original fijado. Solo se muestran estadísticas y etiquetas.", "", "| Fila | Reales | Predichas | Distancia | Palabras |", "|---:|---:|---:|---:|---:|"]
        lines += [f"| {row['row_position_1based']} | {row['actual_stars']} | {row['predicted_stars']} | {row['distance']} | {row['word_count']} |" for row in analysis["cases_for_local_review"]]
        lines.append("")
    notes_path = reports_dir / "error_review.json"
    if notes_path.exists():
        notes = json.loads(notes_path.read_text(encoding="utf-8"))
        if notes["model_id"] == selection["model_id"]:
            lines += ["## Lectura cualitativa asistida de casos reales", "", "Las siguientes descripciones son paráfrasis; las hipótesis no se tratan como causas comprobadas.", ""]
            lines += [f"- {item['split']}, fila {item['row_position_1based']}: {item['observation']}" for item in notes["cases"]]
            lines.append("")
    lines += ["## Límites", "", "No se infiere sarcasmo automáticamente. Los marcadores de negación y contraste son indicadores descriptivos; no capturan alcance sintáctico. Los conjuntos reservados conservan sus duplicados originales documentados en DATASET.md. Estas observaciones sirven para explicar límites, no para optimizar usando test.", ""]
    path = reports_dir / "errors.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(render_errors().name)
