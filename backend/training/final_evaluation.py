"""Evaluate the saved, frozen pipeline on one split.

Validation runs can be repeated, and rehearse this code. The test split can be evaluated
only once: the run refuses if a test report already exists, and whenever the saved file
doesn't match the hash recorded when it was frozen. Nothing here fits or changes the model.

Run from the backend folder:
    python -m training.final_evaluation --split validation
    python -m training.final_evaluation --split test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.predict import DEFAULT_PIPELINE_PATH, load_pipeline
from training.config import REPORTS_DIR, SPLIT_ASSIGNMENTS
from training.evaluate import (
    roc_auc,
    score,
    score_by_similarity_band,
    shares_at_or_above,
    similarity_to_training,
    spam_scores,
)
from training.feature_experiments import peak_memory_gb, stratified_sample
from training.inspect_dataset import sha256_file, write_report
from training.prepare_data import load_split
from training.train_final import METADATA_PATH

LATENCY_ROWS = 200
REPORT_PATHS = {
    "validation": REPORTS_DIR / "final_validation_evaluation.json",
    "test": REPORTS_DIR / "final_test_evaluation.json",
}


class EvaluationRefused(Exception):
    """Raised when a safeguard stops the evaluation."""


def verify_frozen(metadata_path: Path, pipeline_path: Path, assignments_path: Path) -> dict:
    """Return the metadata, or refuse if the pipeline or split differs from what was frozen."""
    if not metadata_path.exists():
        raise EvaluationRefused("No pipeline metadata found. Run training.train_final first.")
    if not pipeline_path.exists():
        raise EvaluationRefused("No saved pipeline found. Run training.train_final first.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if sha256_file(pipeline_path) != metadata["pipeline_sha256"]:
        raise EvaluationRefused("The saved pipeline doesn't match the hash recorded when it was frozen.")
    if sha256_file(assignments_path) != metadata["split_assignments_sha256"]:
        raise EvaluationRefused("The split file doesn't match the one the pipeline was trained with.")
    return metadata


def refuse_repeat_test_run(split: str, report_path: Path) -> None:
    """Refuse to evaluate the test split a second time."""
    if split == "test" and report_path.exists():
        raise EvaluationRefused(
            f"{report_path.name} already exists. The test split is evaluated only once, "
            "so that its result can't influence further changes."
        )


def class_results(metrics: dict) -> dict:
    """Return precision, recall and error rates for each class, from the confusion counts."""
    true_ham, true_spam = metrics["true_ham"], metrics["true_spam"]
    flagged, missed = metrics["ham_flagged_as_spam"], metrics["spam_missed"]

    def ratio(part: int, whole: int) -> float | None:
        return round(part / whole, 4) if whole else None

    return {
        "Ham": {
            "rows": true_ham + flagged,
            "precision": ratio(true_ham, true_ham + missed),
            "recall": ratio(true_ham, true_ham + flagged),
            "share_wrongly_flagged_as_spam": ratio(flagged, true_ham + flagged),
        },
        "Spam": {
            "rows": true_spam + missed,
            "precision": ratio(true_spam, true_spam + flagged),
            "recall": ratio(true_spam, true_spam + missed),
            "share_missed": ratio(missed, true_spam + missed),
        },
    }


def single_message_latency(pipeline, texts: pd.Series) -> dict:
    """Measure one-message-at-a-time prediction, including preprocessing and TF-IDF."""
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


def build_report(
    split: str,
    pipeline,
    metadata: dict,
    rows: pd.DataFrame,
    train_texts: pd.Series,
) -> dict:
    """Evaluate the pipeline on the rows. It reports aggregates only, with no email text."""
    predictions = pipeline.predict(rows["text"])
    metrics = score(rows["label"], predictions)
    similarity = similarity_to_training(train_texts, rows["text"])
    is_spam = (rows["label"] == "Spam").to_numpy()
    return {
        "split": split,
        "rows": int(len(rows)),
        "spam_share": round(float(is_spam.mean()), 4),
        "model_version": metadata["model_version"],
        "pipeline_sha256": metadata["pipeline_sha256"],
        "overall_metrics": metrics,
        "roc_auc": roc_auc(rows["label"], spam_scores(pipeline, rows["text"])),
        "class_results": class_results(metrics),
        "similarity_method": "closest training row, cosine similarity of word_1 TF-IDF fitted on training rows",
        "share_of_rows_at_or_above_similarity": {
            "Ham": shares_at_or_above(similarity[~is_spam]),
            "Spam": shares_at_or_above(similarity[is_spam]),
        },
        "metrics_by_similarity_band": score_by_similarity_band(similarity, rows["label"], predictions),
        "single_message_latency": single_message_latency(
            pipeline, stratified_sample(rows, LATENCY_ROWS)["text"]
        ),
        "peak_memory_gb": peak_memory_gb(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the frozen pipeline on one split.")
    parser.add_argument("--split", choices=sorted(REPORT_PATHS), required=True)
    args = parser.parse_args(argv)

    report_path = REPORT_PATHS[args.split]
    try:
        refuse_repeat_test_run(args.split, report_path)
        metadata = verify_frozen(METADATA_PATH, DEFAULT_PIPELINE_PATH, SPLIT_ASSIGNMENTS)
    except EvaluationRefused as refusal:
        print(f"Evaluation refused: {refusal}", file=sys.stderr)
        return 1

    pipeline = load_pipeline()
    train_texts = load_split("train")["text"]
    rows = load_split(args.split, allow_test=args.split == "test")
    report = build_report(args.split, pipeline, metadata, rows, train_texts)
    write_report(report, report_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
