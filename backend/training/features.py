"""Named TF-IDF feature configurations.

This is the one place that defines each feature configuration, so the experiments here
and the model training in Milestone 3 use identical settings. It is training-only:
a saved pipeline already contains its fitted vectoriser, so the API doesn't need this file.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.ml.preprocess import preprocess_text

# Settings shared by every configuration:
# - max_df ignores terms in over 95% of messages, which carry little information.
# - sublinear_tf dampens repetition, so a word seen 100 times doesn't count 100 times as much.
_SHARED = {"max_df": 0.95, "sublinear_tf": True}

FEATURE_SETS: dict[str, dict] = {
    "word_1": {**_SHARED, "analyzer": "word", "ngram_range": (1, 1), "min_df": 2},
    "word_1_2": {
        **_SHARED,
        "analyzer": "word",
        "ngram_range": (1, 2),
        "min_df": 3,
        "max_features": 300_000,
    },
    "word_1_2_stop": {
        **_SHARED,
        "analyzer": "word",
        "ngram_range": (1, 2),
        "min_df": 3,
        "max_features": 300_000,
        "stop_words": "english",
    },
    "char_3_5": {
        **_SHARED,
        "analyzer": "char_wb",
        "ngram_range": (3, 5),
        "min_df": 3,
        "max_features": 300_000,
    },
}


def build_vectorizer(
    name: str,
    preprocessor: Callable[[str], str] | None = preprocess_text,
) -> TfidfVectorizer:
    """Return an unfitted vectoriser for a named configuration.

    lowercase is off because preprocess_text already lowercases. float32 uses half the
    memory of the default float64, with precision that is ample for TF-IDF weights.
    """
    return TfidfVectorizer(
        preprocessor=preprocessor,
        lowercase=False,
        dtype=np.float32,
        **FEATURE_SETS[name],
    )
