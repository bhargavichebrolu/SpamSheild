"""Load the saved model pipeline for inference, and identify what it contains.

The file holds a scikit-learn Pipeline: TF-IDF, including its reference to preprocess_text,
followed by the classifier. Python's pickle format can run code while loading, so only
load a file this project created.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DEFAULT_PIPELINE_PATH = MODELS_DIR / "spamshield_pipeline.joblib"

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
