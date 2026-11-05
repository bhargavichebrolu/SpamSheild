"""Compare preprocessing and TF-IDF options on the validation split.

Every experiment fits on training rows and scores on validation rows, with one fixed
classifier so that only the representation changes. This compares representations; it
does not select a model, which is Milestone 3's job. The test split is never loaded.

Each experiment runs in its own process, so its peak memory is measured separately.

Run from the backend folder:
    python -m training.feature_experiments --list
    python -m training.feature_experiments --experiment sample_word_1_full
    python -m training.feature_experiments --stage sample
    python -m training.feature_experiments --near-duplicates
"""

from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.preprocess import (
    collapse_whitespace,
    preprocess_text,
    remove_escapelong,
    truncate,
    unify_numbers,
    unify_url_scheme,
)
from training.config import RANDOM_SEED, REPORTS_DIR
from training.features import build_vectorizer
from training.inspect_dataset import write_report
from training.prepare_data import load_split

RESULTS_PATH = REPORTS_DIR / "feature_experiments.json"
NEAR_DUPLICATES_PATH = REPORTS_DIR / "near_duplicate_check.json"

SAMPLE_TRAIN_ROWS = 10_000
SAMPLE_VALIDATION_ROWS = 5_000
NEAR_DUPLICATE_BATCH_ROWS = 100
SIMILARITY_THRESHOLDS = (0.80, 0.90, 0.95, 0.99)


def _without_truncation(text: str) -> str:
    return collapse_whitespace(unify_url_scheme(remove_escapelong(unify_numbers(text.lower()))))


def _numbers_only(text: str) -> str:
    return unify_numbers(text.lower())


def _keep_source_formatting(text: str) -> str:
    """Only cap the length, leaving digits, escapelong and https as they are in the data."""
    return truncate(text).lower()


PREPROCESSORS: dict[str, Callable[[str], str]] = {
    "full": preprocess_text,
    "keep_source_formatting": _keep_source_formatting,
    "numbers_only": _numbers_only,
    "no_truncation": _without_truncation,
}


@dataclass(frozen=True)
class Experiment:
    name: str
    stage: str
    preprocessing: str
    features: str
    train_rows: int | None = None
    validation_rows: int | None = None


def _sample(name: str, preprocessing: str, features: str) -> Experiment:
    return Experiment(name, "sample", preprocessing, features, SAMPLE_TRAIN_ROWS, SAMPLE_VALIDATION_ROWS)


EXPERIMENTS = {
    experiment.name: experiment
    for experiment in [
        _sample("sample_word_1_full", "full", "word_1"),
        _sample("sample_word_1_keep_source_formatting", "keep_source_formatting", "word_1"),
        _sample("sample_word_1_numbers_only", "numbers_only", "word_1"),
        _sample("sample_word_1_no_truncation", "no_truncation", "word_1"),
        _sample("sample_word_1_2_full", "full", "word_1_2"),
        _sample("sample_word_1_2_stop_full", "full", "word_1_2_stop"),
        _sample("sample_char_3_5_full", "full", "char_3_5"),
        Experiment("scale_40k_word_1_2_full", "scale", "full", "word_1_2", 40_000, None),
        Experiment("scale_40k_char_3_5_full", "scale", "full", "char_3_5", 40_000, None),
        Experiment("all_train_word_1_full", "all_train", "full", "word_1"),
        Experiment("all_train_word_1_2_full", "all_train", "full", "word_1_2"),
    ]
}


def peak_memory_gb() -> float | None:
    """Return this process's peak memory in GB, or None if it can't be measured."""
    if sys.platform != "win32":
        import resource

        kilobytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(kilobytes / 1024**2, 2)

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32")
    psapi = ctypes.WinDLL("psapi")
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemoryCounters),
        ctypes.c_ulong,
    ]
    if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return None
    return round(counters.PeakWorkingSetSize / 1024**3, 2)


def stratified_sample(df: pd.DataFrame, rows: int | None, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Return a seeded sample with the same label balance, or all rows if rows is None."""
    if rows is None or rows >= len(df):
        return df
    sample, _ = train_test_split(df, train_size=rows, stratify=df["label"], random_state=seed)
    return sample.reset_index(drop=True)


def matrix_size_mb(matrix: sparse.csr_matrix) -> float:
    """Return the memory held by a sparse matrix's arrays, in MB."""
    size = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
    return round(size / 1024**2, 1)


def score(labels: pd.Series, predictions: np.ndarray) -> dict:
    """Return metrics with Spam as the positive class, and the two error types."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, pos_label="Spam", average="binary", zero_division=0
    )
    (true_ham, false_positive), (false_negative, true_spam) = confusion_matrix(
        labels, predictions, labels=["Ham", "Spam"]
    )
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 4),
        "precision_spam": round(float(precision), 4),
        "recall_spam": round(float(recall), 4),
        "f1_spam": round(float(f1), 4),
        "ham_flagged_as_spam": int(false_positive),
        "spam_missed": int(false_negative),
        "true_ham": int(true_ham),
        "true_spam": int(true_spam),
    }


def run_experiment(experiment: Experiment, train: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """Fit on the training rows and score on the validation rows."""
    train = stratified_sample(train, experiment.train_rows)
    validation = stratified_sample(validation, experiment.validation_rows)

    vectorizer = build_vectorizer(experiment.features, PREPROCESSORS[experiment.preprocessing])
    classifier = LogisticRegression(solver="liblinear", random_state=RANDOM_SEED)
    pipeline = Pipeline([("tfidf", vectorizer), ("classifier", classifier)])

    started = time.perf_counter()
    pipeline.fit(train["text"], train["label"])
    fit_seconds = time.perf_counter() - started

    started = time.perf_counter()
    predictions = pipeline.predict(validation["text"])
    predict_seconds = time.perf_counter() - started

    train_matrix = vectorizer.transform(train["text"].head(1000))
    return {
        **asdict(experiment),
        "classifier": "LogisticRegression(solver=liblinear)",
        "rows_used": {"train": int(len(train)), "validation": int(len(validation))},
        "metrics": score(validation["label"], predictions),
        "vocabulary_size": int(len(vectorizer.vocabulary_)),
        "mean_terms_per_row": round(float(train_matrix.nnz / train_matrix.shape[0]), 1),
        "cost": {
            "fit_seconds": round(fit_seconds, 1),
            "predict_seconds": round(predict_seconds, 1),
            "peak_memory_gb": peak_memory_gb(),
        },
    }


def save_result(result: dict, path: Path = RESULTS_PATH) -> None:
    """Add one result to the shared results file, replacing any earlier run of that name."""
    results = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    results[result["name"]] = result
    write_report(results, path)


def closest_training_similarity(
    rows: sparse.csr_matrix,
    train_matrix: sparse.csr_matrix,
    batch_rows: int = NEAR_DUPLICATE_BATCH_ROWS,
) -> np.ndarray:
    """Return each row's cosine similarity to its most similar training row.

    TF-IDF rows have unit length, so multiplying them gives their cosine similarity.
    Working in batches limits how much memory the multiplication needs.
    """
    closest: list[np.ndarray] = []
    for start in range(0, rows.shape[0], batch_rows):
        similarities = rows[start : start + batch_rows] @ train_matrix.T
        closest.append(similarities.max(axis=1).toarray().ravel())
    return np.concatenate(closest) if closest else np.empty(0)


def shares_at_or_above(
    similarity: np.ndarray,
    thresholds: tuple[float, ...] = SIMILARITY_THRESHOLDS,
) -> dict[str, float]:
    """Return the share of rows whose closest training row reaches each similarity."""
    return {f"{threshold:.2f}": round(float((similarity >= threshold).mean()), 4) for threshold in thresholds}


def score_by_similarity_band(
    similarity: np.ndarray,
    labels: pd.Series,
    predictions: np.ndarray,
) -> dict[str, dict]:
    """Score rows separately by how similar they are to their closest training row.

    The lowest band shows performance on messages with no close match in training.
    """
    edges = (0.0, *SIMILARITY_THRESHOLDS[:3], np.inf)
    names = [
        f"{low:.2f}_to_{high:.2f}" if np.isfinite(high) else f"{low:.2f}_and_above"
        for low, high in zip(edges, edges[1:])
    ]
    bands = {}
    label_values = labels.to_numpy()
    for name, low, high in zip(names, edges, edges[1:]):
        mask = (similarity >= low) & (similarity < high)
        band_labels = pd.Series(label_values[mask])
        bands[name] = {
            "rows": int(mask.sum()),
            "share_of_rows": round(float(mask.mean()), 4),
            "spam_share": round(float((band_labels == "Spam").mean()), 4) if mask.any() else None,
            "metrics": score(band_labels, predictions[mask]) if mask.any() else None,
        }
    return bands


def run_near_duplicate_check() -> dict:
    """Measure template-like similarity to training rows, and its effect on scores.

    Both the similarity and the model use word_1 TF-IDF, fitted on training rows only.
    """
    train = load_split("train")
    validation = load_split("validation")
    vectorizer = build_vectorizer("word_1")
    train_matrix = vectorizer.fit_transform(train["text"]).tocsr()
    validation_matrix = vectorizer.transform(validation["text"]).tocsr()

    classifier = LogisticRegression(solver="liblinear", random_state=RANDOM_SEED)
    classifier.fit(train_matrix, train["label"])
    predictions = classifier.predict(validation_matrix)

    similarity = closest_training_similarity(validation_matrix, train_matrix)
    is_spam = (validation["label"] == "Spam").to_numpy()
    return {
        "method": "cosine similarity of word_1 TF-IDF vectors, fitted on training rows",
        "classifier": "LogisticRegression(solver=liblinear) on word_1 TF-IDF",
        "rows_used": {"train": int(len(train)), "validation": int(len(validation))},
        "share_of_validation_rows_at_or_above_similarity": {
            "Ham": shares_at_or_above(similarity[~is_spam]),
            "Spam": shares_at_or_above(similarity[is_spam]),
        },
        "overall_metrics": score(validation["label"], predictions),
        "metrics_by_similarity_band": score_by_similarity_band(similarity, validation["label"], predictions),
        "peak_memory_gb": peak_memory_gb(),
    }


def run_one(name: str) -> None:
    experiment = EXPERIMENTS[name]
    result = run_experiment(experiment, load_split("train"), load_split("validation"))
    save_result(result)
    print(json.dumps(result, indent=2))


def run_stage(stage: str) -> int:
    """Run each experiment in a stage in its own process, stopping at the first failure."""
    for experiment in EXPERIMENTS.values():
        if experiment.stage == stage:
            command = [sys.executable, "-m", "training.feature_experiments", "--experiment", experiment.name]
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                return completed.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare preprocessing and TF-IDF options.")
    parser.add_argument("--list", action="store_true", help="List the experiments and exit.")
    parser.add_argument("--experiment", choices=sorted(EXPERIMENTS), help="Run one experiment.")
    parser.add_argument("--stage", choices=["sample", "scale", "all_train"], help="Run a stage.")
    parser.add_argument("--near-duplicates", action="store_true", help="Run the similarity check.")
    args = parser.parse_args(argv)

    if args.list:
        for experiment in EXPERIMENTS.values():
            print(f"{experiment.stage:10} {experiment.name}")
        return 0
    if args.experiment:
        run_one(args.experiment)
        return 0
    if args.stage:
        return run_stage(args.stage)
    if args.near_duplicates:
        report = run_near_duplicate_check()
        write_report(report, NEAR_DUPLICATES_PATH)
        print(json.dumps(report, indent=2))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
