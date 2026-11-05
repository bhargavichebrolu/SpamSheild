"""Compare the candidate classifiers on the validation split.

For each feature set, the TF-IDF matrix is built once from training rows, and every
classifier uses that same matrix. So the models share one split and identical features.
The test split is never loaded.

Each feature set runs in its own process, so its peak memory is measured separately.

Run from the backend folder:
    python -m training.compare_models
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.pipeline import Pipeline

from training.config import RANDOM_SEED, REPORTS_DIR
from training.evaluate import roc_auc, score, spam_scores
from training.feature_experiments import peak_memory_gb, stratified_sample
from training.features import FEATURE_SETS, build_vectorizer
from training.inspect_dataset import write_report
from training.models import F1_TIE_MARGIN, PARAMETER_GRID, build_classifier, select_best
from training.prepare_data import load_split

RESULTS_PATH = REPORTS_DIR / "model_comparison.json"
FEATURES_COMPARED = ("word_1", "word_1_2")
LATENCY_ROWS = 200


def fit_classifier(model: str, setting: float, train_matrix, train_labels: pd.Series) -> tuple[object, bool, float]:
    """Fit one classifier. Return it, whether it converged, and the fit time in seconds."""
    classifier = build_classifier(model, setting)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        started = time.perf_counter()
        classifier.fit(train_matrix, train_labels)
        seconds = time.perf_counter() - started
    converged = not any(issubclass(warning.category, ConvergenceWarning) for warning in caught)
    return classifier, converged, seconds


def message_latency_ms(vectorizer, classifier, texts: pd.Series) -> dict[str, float]:
    """Measure one-message-at-a-time prediction, including preprocessing and TF-IDF."""
    pipeline = Pipeline([("tfidf", vectorizer), ("classifier", classifier)])
    timings = []
    for text in texts:
        started = time.perf_counter()
        pipeline.predict([text])
        timings.append((time.perf_counter() - started) * 1000)
    return {
        "rows": len(timings),
        "median_ms": round(float(np.median(timings)), 2),
        "p95_ms": round(float(np.percentile(timings, 95)), 2),
    }


def compare_for_features(features: str, train: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """Run every candidate and setting on one feature set."""
    vectorizer = build_vectorizer(features)
    started = time.perf_counter()
    train_matrix = vectorizer.fit_transform(train["text"]).tocsr()
    vectorizer_seconds = time.perf_counter() - started
    validation_matrix = vectorizer.transform(validation["text"]).tocsr()
    latency_rows = stratified_sample(validation, LATENCY_ROWS, RANDOM_SEED)["text"]

    results = []
    for model, (setting_name, values) in PARAMETER_GRID.items():
        for value in values:
            classifier, converged, fit_seconds = fit_classifier(model, value, train_matrix, train["label"])
            started = time.perf_counter()
            predictions = classifier.predict(validation_matrix)
            predict_seconds = time.perf_counter() - started
            results.append(
                {
                    "features": features,
                    "model": model,
                    "setting": {setting_name: value},
                    "converged": converged,
                    "metrics": score(validation["label"], predictions),
                    "roc_auc": roc_auc(validation["label"], spam_scores(classifier, validation_matrix)),
                    "classifier_fit_seconds": round(fit_seconds, 1),
                    "classifier_predict_seconds": round(predict_seconds, 2),
                    "single_message_latency": message_latency_ms(vectorizer, classifier, latency_rows),
                }
            )
    return {
        "features": features,
        "feature_settings": {key: repr(value) for key, value in FEATURE_SETS[features].items()},
        "rows_used": {"train": int(len(train)), "validation": int(len(validation))},
        "vocabulary_size": int(len(vectorizer.vocabulary_)),
        "vectorizer_fit_seconds": round(vectorizer_seconds, 1),
        "peak_memory_gb": peak_memory_gb(),
        "results": results,
    }


def write_results(feature_report: dict) -> dict:
    """Add one feature set's results, then apply the selection rule to everything recorded."""
    report = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if RESULTS_PATH.exists() else {}
    runs = report.get("runs", {})
    runs[feature_report["features"]] = feature_report
    all_results = [result for run in runs.values() for result in run["results"]]
    selected = select_best(all_results)
    report = {
        "split_used_for_selection": "validation",
        "selection_rule": {
            "f1_tie_margin": F1_TIE_MARGIN,
            "steps": [
                "Find the highest F1 for Spam, among runs that converged",
                "Treat every run within the margin as tied",
                "Among ties, choose the fewest legitimate messages flagged as spam",
                "If still tied, choose the simplest model, and then the smaller feature set",
            ],
        },
        "selected": {key: selected[key] for key in ("features", "model", "setting", "metrics", "roc_auc")},
        "runs": runs,
    }
    write_report(report, RESULTS_PATH)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare candidate classifiers on validation data.")
    parser.add_argument("--features", choices=FEATURES_COMPARED, help="Run one feature set.")
    args = parser.parse_args(argv)

    if args.features:
        report = compare_for_features(args.features, load_split("train"), load_split("validation"))
        write_results(report)
        print(json.dumps({key: report[key] for key in ("features", "vocabulary_size", "peak_memory_gb")}))
        return 0

    for features in FEATURES_COMPARED:
        command = [sys.executable, "-m", "training.compare_models", "--features", features]
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
