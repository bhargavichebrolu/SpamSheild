"""Measure how much the selected model depends on likely source signals.

Two kinds of experiment run on training and validation rows only, using the model and
features chosen by compare_models.py:

- Marker removal: retrain without the words listed by source_markers.py, removing them
  before bigrams are formed, and compare validation results with the baseline.
- Cross-style: train on one number style and score on the other. The styles are a proxy
  for separately processed sources, so this tests a harder shift than a random split.

These results show dependence on signals found in this dataset. They are NOT proof of
how the model generalises to unseen sources, because the sources aren't verified, the
word lists are estimates, and all rows still come from this one dataset.

Run from the backend folder, after compare_models and source_markers:
    python -m training.source_leakage
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass

import pandas as pd
from sklearn.pipeline import Pipeline

from training.compare_models import RESULTS_PATH as MODEL_COMPARISON_PATH
from training.config import RANDOM_SEED, REPORTS_DIR
from training.evaluate import roc_auc, score, spam_scores
from training.feature_experiments import peak_memory_gb, stratified_sample
from training.features import build_vectorizer
from training.inspect_dataset import write_report
from training.models import F1_TIE_MARGIN, build_classifier
from training.prepare_data import load_split
from training.source_markers import list_hash, load_markers, styles_of

RESULTS_PATH = REPORTS_DIR / "source_leakage.json"

INTERPRETATION_NOTE = (
    "These results show dependence on signals found in this dataset. They are not proof of "
    "generalisation to unseen sources: the sources are unverified, the word lists are "
    "estimates, and all rows come from this one dataset."
)


@dataclass(frozen=True)
class MarkerRemoval:
    name: str
    lists: tuple[tuple[str, int], ...] = ()


MARKER_REMOVALS = {
    removal.name: removal
    for removal in [
        MarkerRemoval("baseline_no_removal"),
        MarkerRemoval("remove_style_300", (("style_leaning", 300),)),
        MarkerRemoval("remove_style_1000", (("style_leaning", 1000),)),
        MarkerRemoval("remove_ham_300", (("ham_leaning", 300),)),
        MarkerRemoval("remove_style_300_and_ham_300", (("style_leaning", 300), ("ham_leaning", 300))),
        MarkerRemoval("remove_ham_300_and_spam_300", (("ham_leaning", 300), ("spam_leaning", 300))),
    ]
}

CROSS_STYLE_RUNS = (
    "train_placeholder_only",
    "train_digits_only",
    "train_placeholder_only_matched_size",
    "train_placeholder_only_remove_style_300_and_ham_300",
    "train_digits_only_remove_style_300_and_ham_300",
)

# Fixed before any leakage result was seen. The final model uses this removal only if
# validation F1 stays within F1_TIE_MARGIN of the baseline, and cross-style F1 improves in
# both directions. Otherwise the model stays as the baseline, and the results are reported.
CANDIDATE_REMOVAL = "remove_style_300_and_ham_300"


def selected_model() -> dict:
    """Return the model and features chosen on validation data."""
    return json.loads(MODEL_COMPARISON_PATH.read_text(encoding="utf-8"))["selected"]


def build_pipeline(selected: dict, stop_words: list[str] | None = None) -> Pipeline:
    """Return an unfitted pipeline for the selected model, optionally without some words."""
    vectorizer = build_vectorizer(selected["features"])
    if stop_words:
        vectorizer.set_params(stop_words=stop_words)
    setting = next(iter(selected["setting"].values()))
    return Pipeline(
        [("tfidf", vectorizer), ("classifier", build_classifier(selected["model"], setting))]
    )


def words_to_remove(removal: MarkerRemoval, lists: dict[str, list[str]]) -> list[str]:
    """Combine the top words from each named list, without repeats, in a fixed order."""
    words: dict[str, None] = {}
    for list_name, count in removal.lists:
        words.update(dict.fromkeys(lists[list_name][:count]))
    return list(words)


def evaluate_pipeline(pipeline: Pipeline, rows: pd.DataFrame) -> dict:
    """Score a fitted pipeline on the given rows."""
    return {
        "rows": int(len(rows)),
        "spam_share": round(float((rows["label"] == "Spam").mean()), 4),
        "metrics": score(rows["label"], pipeline.predict(rows["text"])),
        "roc_auc": roc_auc(rows["label"], spam_scores(pipeline, rows["text"])),
    }


def run_marker_removal(name: str, selected: dict, train: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """Retrain without one set of words, and score on validation rows."""
    removal = MARKER_REMOVALS[name]
    words = words_to_remove(removal, load_markers()["lists"])
    pipeline = build_pipeline(selected, words or None)

    started = time.perf_counter()
    pipeline.fit(train["text"], train["label"])
    fit_seconds = time.perf_counter() - started

    return {
        "name": name,
        "lists_used": [{"list": list_name, "top_words": count} for list_name, count in removal.lists],
        "words_removed": len(words),
        "removed_words_sha256": list_hash(words),
        "training_rows": int(len(train)),
        "vocabulary_size": int(len(pipeline.named_steps["tfidf"].vocabulary_)),
        "validation": evaluate_pipeline(pipeline, validation),
        "fit_seconds": round(fit_seconds, 1),
        "peak_memory_gb": peak_memory_gb(),
    }


def run_cross_style(name: str, selected: dict, train: pd.DataFrame, validation: pd.DataFrame) -> dict:
    """Train on one number style, and score on each style's validation rows."""
    if name not in CROSS_STYLE_RUNS:
        raise ValueError(f"Unknown cross-style run: {name!r}")
    train_styles = styles_of(train["text"])
    validation_styles = styles_of(validation["text"])

    style = "digits_only" if name.startswith("train_digits_only") else "placeholder_only"
    subset = train[train_styles == style]
    if name.endswith("matched_size"):
        digits_rows = int((train_styles == "digits_only").sum())
        subset = stratified_sample(subset.reset_index(drop=True), digits_rows, RANDOM_SEED)

    words: list[str] = []
    if name.endswith(CANDIDATE_REMOVAL):
        words = words_to_remove(MARKER_REMOVALS[CANDIDATE_REMOVAL], load_markers()["lists"])

    pipeline = build_pipeline(selected, words or None)
    started = time.perf_counter()
    pipeline.fit(subset["text"], subset["label"])
    fit_seconds = time.perf_counter() - started

    return {
        "name": name,
        "training_style": style,
        "words_removed": len(words),
        "training_rows": int(len(subset)),
        "training_spam_share": round(float((subset["label"] == "Spam").mean()), 4),
        "validation_by_style": {
            style: evaluate_pipeline(pipeline, validation[validation_styles == style])
            for style in ("digits_only", "placeholder_only", "neither")
        },
        "fit_seconds": round(fit_seconds, 1),
        "peak_memory_gb": peak_memory_gb(),
    }


def save_result(section: str, result: dict, selected: dict) -> None:
    """Add one result to the report, replacing any earlier run of that name."""
    report = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if RESULTS_PATH.exists() else {}
    report.setdefault("marker_removal", {})
    report.setdefault("cross_style", {})
    report[section][result["name"]] = result
    report["model"] = {key: selected[key] for key in ("features", "model", "setting")}
    report["split_used"] = "train to fit, validation to score"
    report["interpretation_note"] = INTERPRETATION_NOTE
    write_report(report, RESULTS_PATH)


def decide_removal(report: dict, margin: float = F1_TIE_MARGIN) -> dict:
    """Apply the rule fixed in CANDIDATE_REMOVAL's comment to validation results."""
    removals = report["marker_removal"]
    cross = report["cross_style"]

    def validation_f1(name: str) -> float:
        return removals[name]["validation"]["metrics"]["f1_spam"]

    def cross_f1(run: str, style: str) -> float:
        return cross[run]["validation_by_style"][style]["metrics"]["f1_spam"]

    f1_drop = validation_f1("baseline_no_removal") - validation_f1(CANDIDATE_REMOVAL)
    digits_to_placeholder = cross_f1(f"train_digits_only_{CANDIDATE_REMOVAL}", "placeholder_only") - cross_f1(
        "train_digits_only", "placeholder_only"
    )
    placeholder_to_digits = cross_f1(f"train_placeholder_only_{CANDIDATE_REMOVAL}", "digits_only") - cross_f1(
        "train_placeholder_only", "digits_only"
    )
    return {
        "candidate": CANDIDATE_REMOVAL,
        "validation_f1_drop": round(f1_drop, 4),
        "f1_margin": margin,
        "cross_style_f1_change": {
            "digits_to_placeholder": round(digits_to_placeholder, 4),
            "placeholder_to_digits": round(placeholder_to_digits, 4),
        },
        "adopt": bool(f1_drop < margin and digits_to_placeholder > 0 and placeholder_to_digits > 0),
    }


def run_one(name: str) -> None:
    selected = selected_model()
    train, validation = load_split("train"), load_split("validation")
    if name in MARKER_REMOVALS:
        save_result("marker_removal", run_marker_removal(name, selected, train, validation), selected)
    else:
        save_result("cross_style", run_cross_style(name, selected, train, validation), selected)
    print(f"Finished {name}")


def main(argv: list[str] | None = None) -> int:
    names = [*MARKER_REMOVALS, *CROSS_STYLE_RUNS]
    parser = argparse.ArgumentParser(description="Measure dependence on likely source signals.")
    parser.add_argument("--experiment", choices=names, help="Run one experiment.")
    parser.add_argument("--decide", action="store_true", help="Apply the removal rule to saved results.")
    args = parser.parse_args(argv)

    if args.experiment:
        run_one(args.experiment)
        return 0
    if not args.decide:
        for name in names:
            command = [sys.executable, "-m", "training.source_leakage", "--experiment", name]
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                return completed.returncode

    report = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    report["removal_decision"] = decide_removal(report)
    write_report(report, RESULTS_PATH)
    print(json.dumps(report["removal_decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
