"""Load the saved model pipeline for inference, identify it, and classify messages.

The file holds a scikit-learn Pipeline: TF-IDF, including its reference to preprocess_text,
followed by the classifier. Python's pickle format can run code while loading, so only
load a file this project created. load_verified_model checks the file's hash first.

Nothing here, or anywhere in app/, imports from training/.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from importlib import metadata as package_metadata
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.config import TOP_TERMS
from app.ml.explain import explain
from app.ml.preprocess import preprocess_text

logger = logging.getLogger("spamshield.model")

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_PIPELINE_PATH = MODELS_DIR / "spamshield_pipeline.joblib"
DEFAULT_METADATA_PATH = MODELS_DIR / "pipeline_metadata.json"

# The default TF-IDF word tokeniser keeps tokens of two or more word characters.
_WORD_TOKEN = re.compile(r"\w\w")

# Fixed strings used to include preprocessing behaviour in the fingerprint. Comparing the
# results, not the source code, means editing a comment doesn't change the fingerprint.
PREPROCESSING_PROBES = (
    "",
    "  Mixed CASE and   SPACING\n\tacross lines  ",
    "Call 555 0199 or sha1 now",
    "Visit HTTPS://Example.com and http://example.org",
    "keep escapelong out but escapelongest stays",
    "a" * 20_100,
)


def load_pipeline(path: Path = DEFAULT_PIPELINE_PATH) -> Pipeline:
    """Load the saved pipeline, or raise FileNotFoundError with instructions to create it."""
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path.name}. Create it from the backend folder with "
            "`python -m training.train_final`."
        )
    return joblib.load(path)


def _callable_name(function) -> str | None:
    """Return a function's import path, which is stable where its repr isn't."""
    if function is None:
        return None
    module = getattr(function, "__module__", None) or type(function).__module__
    return f"{module}.{function.__qualname__}"


def _pipeline_configuration(pipeline: Pipeline) -> dict:
    """Return the settings that affect predictions, in a form with a single JSON encoding."""
    tfidf = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]
    return {
        "steps": [name for name, _ in pipeline.steps],
        "tfidf": {
            "analyzer": tfidf.analyzer,
            "ngram_range": list(tfidf.ngram_range),
            "min_df": tfidf.min_df,
            "max_df": tfidf.max_df,
            "max_features": tfidf.max_features,
            "sublinear_tf": tfidf.sublinear_tf,
            "norm": tfidf.norm,
            "use_idf": tfidf.use_idf,
            "smooth_idf": tfidf.smooth_idf,
            "lowercase": tfidf.lowercase,
            "binary": tfidf.binary,
            "strip_accents": tfidf.strip_accents,
            "token_pattern": tfidf.token_pattern,
            "dtype": np.dtype(tfidf.dtype).name,
            "preprocessor": _callable_name(tfidf.preprocessor),
            "removed_words": sorted(tfidf.stop_words) if tfidf.stop_words else [],
        },
        "classifier": {
            "type": type(classifier).__name__,
            "parameters": classifier.get_params(deep=False),
        },
    }


def model_fingerprint(pipeline: Pipeline) -> str:
    """Return a SHA-256 of what the fitted pipeline learned and how it's configured.

    It's calculated from the values themselves, in a fixed order and encoding, so it doesn't
    depend on how the file was written, or on memory addresses or hash randomisation. Two
    pipelines with the same fingerprint have the same learned numbers exactly.

    This is different from the file's SHA-256, which covers the saved bytes.
    """
    tfidf = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]
    preprocess = tfidf.preprocessor or (lambda text: text)

    def encode_json(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("ascii")

    def encode_array(values: np.ndarray) -> bytes:
        return np.asarray(values, dtype="<f8").tobytes()

    sections = {
        "configuration": encode_json(_pipeline_configuration(pipeline)),
        "preprocessing_behaviour": encode_json([preprocess(probe) for probe in PREPROCESSING_PROBES]),
        "vocabulary": encode_json(sorted((term, int(index)) for term, index in tfidf.vocabulary_.items())),
        "idf": encode_array(tfidf.idf_),
        "classes": encode_json([str(label) for label in classifier.classes_]),
        "coefficients": encode_array(classifier.coef_),
        "intercept": encode_array(classifier.intercept_),
    }

    digest = hashlib.sha256()
    for name, content in sections.items():
        # The lengths stop content from one section being mistaken for another's.
        digest.update(f"{name}:{len(content)}:".encode("ascii"))
        digest.update(content)
    return digest.hexdigest()


class ModelUnavailable(Exception):
    """Raised when the saved model can't be used. Its message is safe to show to a user."""


class ClassificationRejected(Exception):
    """Raised when valid input gives the model nothing to work with."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LoadedModel:
    """A verified pipeline, with the values its explanations need."""

    pipeline: Pipeline
    metadata: dict
    weights: np.ndarray
    intercept: float
    feature_names: np.ndarray


def file_sha256(path: Path) -> str:
    """Return a file's SHA-256, reading in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _warn_about_version_differences(metadata: dict) -> None:
    """Log any package that differs from the versions the model was trained with."""
    for package, expected in metadata.get("versions", {}).items():
        if package == "python":
            continue
        try:
            installed = package_metadata.version(package)
        except package_metadata.PackageNotFoundError:
            continue
        if installed != expected:
            logger.warning("%s is %s, but the model was trained with %s", package, installed, expected)


def load_verified_model(
    pipeline_path: Path = DEFAULT_PIPELINE_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
) -> LoadedModel:
    """Load the saved pipeline, or raise ModelUnavailable if it can't be trusted.

    The file's hash is checked before the file is loaded, because loading a tampered
    file could run code. The content fingerprint is checked afterwards.
    """
    instructions = "Create it from the backend folder with `python -m training.train_final`."
    if not pipeline_path.exists():
        raise ModelUnavailable(f"The model file was not found. {instructions}")
    if not metadata_path.exists():
        raise ModelUnavailable(f"The model metadata was not found. {instructions}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected_file_hash = metadata["pipeline_sha256"]
        expected_fingerprint = metadata["model_content_sha256"]
    except (ValueError, KeyError) as error:
        raise ModelUnavailable("The model metadata is invalid or incomplete.") from error

    if file_sha256(pipeline_path) != expected_file_hash:
        raise ModelUnavailable("The model file doesn't match the hash in its metadata, so it wasn't loaded.")

    _warn_about_version_differences(metadata)
    pipeline = load_pipeline(pipeline_path)

    if model_fingerprint(pipeline) != expected_fingerprint:
        raise ModelUnavailable("The model's contents don't match the fingerprint in its metadata.")

    classifier = pipeline.named_steps["classifier"]
    if [str(label) for label in classifier.classes_] != ["Ham", "Spam"] or classifier.coef_.shape[0] != 1:
        raise ModelUnavailable("The model isn't a two-class linear model with Ham and Spam labels.")

    return LoadedModel(
        pipeline=pipeline,
        metadata=metadata,
        weights=classifier.coef_[0],
        intercept=float(classifier.intercept_[0]),
        feature_names=pipeline.named_steps["tfidf"].get_feature_names_out(),
    )


def classify(model: LoadedModel, text: str) -> dict:
    """Classify one message, and explain the score.

    Raises ClassificationRejected if the message gives the model nothing to use, because
    any label would then only reflect the model's default, not the message.
    """
    if not _WORD_TOKEN.search(preprocess_text(text)):
        raise ClassificationRejected(
            "no_usable_words",
            "The text has no words of two or more characters, so it can't be classified.",
        )

    tfidf = model.pipeline.named_steps["tfidf"]
    classifier = model.pipeline.named_steps["classifier"]
    row = tfidf.transform([text]).tocsr()
    if row.nnz == 0:
        raise ClassificationRejected(
            "no_recognised_terms",
            "None of the words in this text are in the model's vocabulary, so it can't be classified.",
        )

    return {
        "label": str(classifier.predict(row)[0]).lower(),
        "score": round(float(classifier.decision_function(row)[0]), 6),
        "terms_recognised": int(row.nnz),
        "explanation": explain(row, model.weights, model.intercept, model.feature_names, TOP_TERMS),
    }
