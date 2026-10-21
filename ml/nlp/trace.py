"""Traza del mismo transformador y analizador usados por el pipeline."""

import argparse
import json
import sys

from sklearn.pipeline import Pipeline

from ml.nlp.pipeline import build_pipeline, nlp_settings


def trace_pipeline(pipeline: Pipeline, text: str) -> dict:
    trace = pipeline.named_steps["nlp"].trace(text)
    vectorizer = pipeline.named_steps["tfidf"]
    trace["ngram_range"] = list(vectorizer.ngram_range)
    trace["ngrams"] = vectorizer.build_analyzer()(trace["processed_text"])
    if hasattr(vectorizer, "vocabulary_"):
        trace["known_ngrams"] = [value for value in trace["ngrams"] if value in vectorizer.vocabulary_]
        trace["unknown_ngrams"] = [value for value in trace["ngrams"] if value not in vectorizer.vocabulary_]
    return trace


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True)
    parser.add_argument("--morphology", choices=["stemming", "lemmatization"], default="stemming")
    args = parser.parse_args()
    settings = nlp_settings()
    pipeline = build_pipeline(morphology=args.morphology, **settings["preprocessing"])
    pipeline.named_steps["nlp"].fit([])
    print(json.dumps(trace_pipeline(pipeline, args.text), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
