"""Fit the chosen pipeline on the training split, save it, and record what was saved.

Only training rows are used, so the final test result describes exactly the saved file.
The configuration comes from FINAL_MODEL in config.py, set after the validation results.

Run from the backend folder:
    python -m training.train_final
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from importlib import metadata
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.ml.predict import DEFAULT_PIPELINE_PATH, MODELS_DIR, load_pipeline, model_fingerprint
from training.config import FINAL_MODEL, RANDOM_SEED, SPLIT_ASSIGNMENTS
from training.features import FEATURE_SETS, build_vectorizer
from training.feature_experiments import peak_memory_gb
from training.inspect_dataset import EXPECTED_SHA256, sha256_file, write_report
from training.models import build_classifier
from training.prepare_data import load_split
from training.source_leakage import MARKER_REMOVALS, words_to_remove
from training.source_markers import list_hash, load_markers

METADATA_PATH = MODELS_DIR / "pipeline_metadata.json"
PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "joblib")


def final_removed_words(final_model: dict = FINAL_MODEL) -> list[str]:
    """Return the words the final model excludes, from the training-only marker lists."""
    removal_name = final_model.get("removed_words")
    if not removal_name:
        return []
    return words_to_remove(MARKER_REMOVALS[removal_name], load_markers()["lists"])


def build_final_pipeline(final_model: dict = FINAL_MODEL) -> Pipeline:
    """Return the unfitted pipeline described by the final configuration."""
    vectorizer = build_vectorizer(final_model["features"])
    removed_words = final_removed_words(final_model)
    if removed_words:
        vectorizer.set_params(stop_words=removed_words)
    return Pipeline(
        [
            ("tfidf", vectorizer),
            ("classifier", build_classifier(final_model["model"], final_model["setting_value"])),
        ]
    )


def save_pipeline(pipeline: Pipeline, path: Path) -> str:
    """Save the pipeline and return the saved file's SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path, compress=3)
    return sha256_file(path)


def build_metadata(pipeline: Pipeline, final_model: dict, pipeline_sha256: str, rows: int) -> dict:
    """Describe the saved pipeline. It holds settings and hashes, with no words or email text."""
    removed_words = final_removed_words(final_model)
    return {
        "model_version": final_model["model_version"],
        "model": final_model["model"],
        "setting": {final_model["setting_name"]: final_model["setting_value"]},
        "features": final_model["features"],
        "removed_words": {
            "rule": final_model.get("removed_words"),
            "count": len(removed_words),
            "sha256": list_hash(removed_words),
        },
        "feature_settings": {key: repr(value) for key, value in FEATURE_SETS[final_model["features"]].items()},
        "classes": [str(label) for label in pipeline.classes_],
        "vocabulary_size": int(len(pipeline.named_steps["tfidf"].vocabulary_)),
        "training_split": "train",
        "training_rows": rows,
        "random_seed": RANDOM_SEED,
        "dataset_sha256": EXPECTED_SHA256,
        "split_assignments_sha256": sha256_file(SPLIT_ASSIGNMENTS),
        "pipeline_file": DEFAULT_PIPELINE_PATH.name,
        "pipeline_sha256": pipeline_sha256,
        "model_content_sha256": model_fingerprint(pipeline),
        "versions": {
            "python": platform.python_version(),
            **{package: metadata.version(package) for package in PACKAGES},
        },
    }


def learned_values_differences(first: Pipeline, second: Pipeline) -> list[str]:
    """Return the names of any learned values that differ between two fitted pipelines.

    This compares what the models learned, not their files, because two runs can save
    different bytes while learning identical values. The likely cause, not yet proved, is
    that scikit-learn stores a memory address on the vectoriser when it has stop words.
    """
    first_tfidf, second_tfidf = first.named_steps["tfidf"], second.named_steps["tfidf"]
    first_model, second_model = first.named_steps["classifier"], second.named_steps["classifier"]
    differences = []
    if first_tfidf.vocabulary_ != second_tfidf.vocabulary_:
        differences.append("vocabulary")
    elif not np.array_equal(first_tfidf.idf_, second_tfidf.idf_):
        differences.append("idf")
    if set(first_tfidf.stop_words or ()) != set(second_tfidf.stop_words or ()):
        differences.append("removed words")
    if not np.array_equal(first_model.classes_, second_model.classes_):
        differences.append("classes")
    if not np.array_equal(first_model.coef_, second_model.coef_):
        differences.append("classifier weights")
    if not np.array_equal(first_model.intercept_, second_model.intercept_):
        differences.append("classifier intercept")
    return differences


def verify_reproducible() -> int:
    """Refit without saving, and compare what was learned with the saved pipeline."""
    train = load_split("train")
    refit = build_final_pipeline().fit(train["text"], train["label"])
    saved = load_pipeline()

    differences = learned_values_differences(saved, refit)
    fingerprints_match = model_fingerprint(saved) == model_fingerprint(refit)
    validation_texts = load_split("validation")["text"]
    predictions_match = bool(np.array_equal(saved.predict(validation_texts), refit.predict(validation_texts)))

    print(f"Learned values that differ: {differences or 'none'}")
    print(f"Identical content fingerprint: {fingerprints_match}")
    print(f"Identical predictions on {len(validation_texts)} validation rows: {predictions_match}")
    return 0 if fingerprints_match and predictions_match and not differences else 1


def record_fingerprint(
    metadata_path: Path = METADATA_PATH,
    pipeline_path: Path = DEFAULT_PIPELINE_PATH,
) -> int:
    """Add the content fingerprint to the metadata of an existing saved pipeline.

    This reads the saved file, and changes only the metadata. It refuses if the file isn't
    the one the metadata describes, so a fingerprint can't be attached to the wrong model.
    """
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    file_sha256 = sha256_file(pipeline_path)
    if file_sha256 != metadata["pipeline_sha256"]:
        print("Refused: the saved pipeline doesn't match its metadata.", file=sys.stderr)
        return 1

    metadata["model_content_sha256"] = model_fingerprint(load_pipeline(pipeline_path))
    write_report(metadata, metadata_path)
    if sha256_file(pipeline_path) != file_sha256:
        print("Refused: the saved pipeline changed while recording.", file=sys.stderr)
        return 1
    print(f"File SHA-256:          {metadata['pipeline_sha256']}")
    print(f"Model content SHA-256: {metadata['model_content_sha256']}")
    return 0


def verify_fingerprint(
    metadata_path: Path = METADATA_PATH,
    pipeline_path: Path = DEFAULT_PIPELINE_PATH,
) -> int:
    """Check the saved file against its metadata, and print a hash of its validation predictions.

    Comparing the printed hash between runs shows predictions survive reloading.
    """
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    pipeline = load_pipeline(pipeline_path)

    file_matches = sha256_file(pipeline_path) == metadata["pipeline_sha256"]
    fingerprint_matches = model_fingerprint(pipeline) == metadata.get("model_content_sha256")
    predictions = pipeline.predict(load_split("validation")["text"])
    predictions_sha256 = hashlib.sha256("\n".join(map(str, predictions)).encode("utf-8")).hexdigest()

    print(f"File matches metadata: {file_matches}")
    print(f"Fingerprint matches metadata: {fingerprint_matches}")
    print(f"Validation predictions SHA-256: {predictions_sha256}")
    return 0 if file_matches and fingerprint_matches else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train and save the final pipeline.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--verify-reproducible",
        action="store_true",
        help="Refit without saving, and compare with the saved pipeline.",
    )
    actions.add_argument(
        "--record-fingerprint",
        action="store_true",
        help="Add the content fingerprint to the metadata, without changing the saved pipeline.",
    )
    actions.add_argument(
        "--verify-fingerprint",
        action="store_true",
        help="Check the saved pipeline against its metadata, without changing anything.",
    )
    args = parser.parse_args(argv)
    if args.verify_reproducible:
        return verify_reproducible()
    if args.record_fingerprint:
        return record_fingerprint()
    if args.verify_fingerprint:
        return verify_fingerprint()

    train = load_split("train")
    pipeline = build_final_pipeline()

    started = time.perf_counter()
    pipeline.fit(train["text"], train["label"])
    fit_seconds = time.perf_counter() - started

    pipeline_sha256 = save_pipeline(pipeline, DEFAULT_PIPELINE_PATH)
    write_report(build_metadata(pipeline, FINAL_MODEL, pipeline_sha256, int(len(train))), METADATA_PATH)

    size_mb = DEFAULT_PIPELINE_PATH.stat().st_size / 1024**2
    print(f"Saved {DEFAULT_PIPELINE_PATH.name}: {size_mb:.1f} MB, sha256 {pipeline_sha256}")
    print(f"Fit seconds: {fit_seconds:.1f}. Peak memory GB: {peak_memory_gb()}", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
