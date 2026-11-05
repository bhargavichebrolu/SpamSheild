"""Settings for the API."""

from __future__ import annotations

from pathlib import Path

from app.ml.preprocess import MAX_TEXT_CHARS

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BACKEND_DIR / "reports"

# The model only reads this many characters, so longer text is rejected rather than
# being silently cut off.
MAX_INPUT_CHARS = MAX_TEXT_CHARS

# Allows 20,000 characters even in the most verbose JSON escaping, with room for the wrapper.
MAX_BODY_BYTES = 256 * 1024

# How much of a rejected upload to read and discard, so the client can receive the error.
MAX_DISCARD_BYTES = 16 * 1024 * 1024

# How many terms to return for each label in an explanation.
TOP_TERMS = 10

# Only the website's local development addresses may call the API from a browser.
ALLOWED_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
