"""CV sobre texto crudo: cada fold reajusta NLP y TF-IDF dentro de Pipeline."""

import hashlib
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from ml.data.validate import Review
from ml.training.pipelines import model_pipeline, model_settings


def tune_model(candidate: dict, reviews: list[Review], *, seed: int, cache_dir: Path) -> tuple[dict, dict]:
    settings = model_settings()
    name = candidate["model"]
    parameter = "classifier__alpha" if name == "MultinomialNB" else "classifier__C"
    pipeline = model_pipeline(name, candidate["morphology"], tuple(candidate["ngram_range"]), seed=seed)
    # Memory almacena por X, y y parámetros. Cada fold tiene su propio fit de IDF;
    # solo se reutiliza el mismo fold entre valores de alpha/C.
    pipeline.memory = joblib.Memory(cache_dir, verbose=0)
    splitter = StratifiedKFold(n_splits=settings["cv_folds"], shuffle=True, random_state=seed)
    labels = np.asarray([row.label for row in reviews])
    folds = list(splitter.split(np.zeros(len(reviews)), labels))
    audit = [{"fold": index + 1, "train_rows": len(train), "validation_rows": len(heldout), "train_positions_sha256": hashlib.sha256(np.asarray(train, dtype=np.int64).tobytes()).hexdigest(), "heldout_positions_sha256": hashlib.sha256(np.asarray(heldout, dtype=np.int64).tobytes()).hexdigest(), "overlap": len(set(train) & set(heldout))} for index, (train, heldout) in enumerate(folds)]
    grid = GridSearchCV(pipeline, {parameter: settings["parameter_grid"][name]}, cv=folds, scoring="f1_macro", n_jobs=1, refit=False, error_score="raise", return_train_score=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        grid.fit([row.text for row in reviews], labels)
    if any(issubclass(item.category, ConvergenceWarning) for item in caught):
        raise RuntimeError(f"{name} no convergió; no se continuará hacia test.")
    trials = []
    for index, params in enumerate(grid.cv_results_["params"]):
        trials.append({"params": params, "mean_macro_f1": float(grid.cv_results_["mean_test_score"][index]), "std_macro_f1": float(grid.cv_results_["std_test_score"][index]), "fold_macro_f1": [float(grid.cv_results_[f"split{fold}_test_score"][index]) for fold in range(len(folds))], "mean_fit_sec": float(grid.cv_results_["mean_fit_time"][index])})
    return grid.best_params_, {"model": name, "morphology": candidate["morphology"], "ngram_range": candidate["ngram_range"], "rows": len(reviews), "scoring": "f1_macro", "best_params": grid.best_params_, "best_mean_macro_f1": float(grid.best_score_), "folds": audit, "trials": trials, "convergence_warnings": 0, "idf_fit_scope": "training rows of each fold only; Pipeline cache keyed by exact X/y and parameters"}
