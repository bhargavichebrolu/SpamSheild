"""Text preprocessing shared by training and inference.

This lives in app/ because a saved model pipeline refers to preprocess_text by its
import path, so the API must be able to import it without any training code.

The dataset's text was already processed before this project received it. These
steps make real email look like that text, and remove what real email can't match.
"""

from __future__ import annotations

import re

# Longer messages are cut to this many characters. The value is chosen and justified
# in docs/PROJECT_EXPLANATION.md, using the results of the feature experiments.
MAX_TEXT_CHARS = 20_000

NUMBER_PLACEHOLDER = "escapenumber"

_DIGITS = re.compile(r"[0-9]+")
_ESCAPELONG = re.compile(r"(?<![a-z])escapelong(?![a-z])")
_HTTPS = re.compile(r"(?<![a-z])https(?![a-z])")


def truncate(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    """Keep only the first max_chars characters."""
    return text[:max_chars]


def unify_numbers(text: str) -> str:
    """Replace each run of digits with the placeholder already used in most of the dataset.

    No spaces are added, because the dataset has joined forms such as "shaescapenumber".
    """
    return _DIGITS.sub(NUMBER_PLACEHOLDER, text)


def remove_escapelong(text: str) -> str:
    """Remove the escapelong placeholder, whose rule can't be reproduced on real email."""
    return _ESCAPELONG.sub(" ", text)


def unify_url_scheme(text: str) -> str:
    """Treat "https" as "http", so a model can't learn that the secure form means legitimate."""
    return _HTTPS.sub("http", text)


def collapse_whitespace(text: str) -> str:
    """Replace any run of whitespace with one space, and trim both ends."""
    return " ".join(text.split())


def preprocess_text(text: str) -> str:
    """Apply the project's preprocessing to one message.

    Truncating first limits the work done on extremely long messages. Lowercasing
    comes before remove_escapelong so that a capitalised form is also matched.
    """
    text = truncate(text).lower()
    return collapse_whitespace(unify_url_scheme(remove_escapelong(unify_numbers(text))))
