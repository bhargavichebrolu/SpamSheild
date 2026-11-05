"""Derive lists of words that may reveal a message's source, using training data only.

The dataset's sources aren't verified, so there's no list of true source words. These
lists are estimates, built by two rules:

- Style-leaning words differ most between the two number styles, within one label. The
  styles (digits or placeholder) are evidence of separately processed sources, so these
  words may mark a source, whatever their label.
- Label-leaning words differ most between Ham and Spam. Ham's strongest words include
  organisation and mailing-list terms, but this rule also catches real spam content. So
  removing Spam-leaning words shows reliance on strong words, and not only on sources.

The saved lists can include people's surnames, so the file is excluded from Git.

Run from the backend folder:
    python -m training.source_markers
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from app.ml.preprocess import preprocess_text
from training.analyse_format import number_style
from training.analyse_vocabulary import log_odds_ratio
from training.config import REPORTS_DIR
from training.inspect_dataset import write_report
from training.prepare_data import load_split

MARKERS_PATH = REPORTS_DIR / "source_markers.json"

MIN_ROWS_PER_WORD = 50
MAX_WORDS_PER_LIST = 1_000


def styles_of(text: pd.Series) -> pd.Series:
    """Return each raw message's number style. Preprocessing would hide this difference."""
    return number_style(
        text.str.contains(r"[0-9]", regex=True),
        text.str.contains(r"(?<![a-z])escapenumber(?![a-z])", regex=True),
    )


def rank_words(words: np.ndarray, scores: np.ndarray, limit: int) -> list[str]:
    """Return up to limit words, highest score first, with ties in alphabetical order."""
    order = np.lexsort((words, -scores))
    return [str(words[position]) for position in order[:limit]]


def derive_markers(
    train: pd.DataFrame,
    min_rows: int = MIN_ROWS_PER_WORD,
    limit: int = MAX_WORDS_PER_LIST,
) -> dict[str, list[str]]:
    """Return ranked word lists, calculated only from the given training rows."""
    vectorizer = CountVectorizer(
        preprocessor=preprocess_text,
        lowercase=False,
        binary=True,
        min_df=min_rows,
        dtype=np.int32,
    )
    counts = vectorizer.fit_transform(train["text"]).tocsr()
    words = vectorizer.get_feature_names_out()

    is_spam = (train["label"] == "Spam").to_numpy()
    spam_rows = np.asarray(counts[is_spam].sum(axis=0)).ravel()
    ham_rows = np.asarray(counts[~is_spam].sum(axis=0)).ravel()
    label_scores = log_odds_ratio(spam_rows, ham_rows, int(is_spam.sum()), int((~is_spam).sum()))

    styles = styles_of(train["text"]).to_numpy()
    style_scores = np.zeros(len(words))
    for label_mask in (is_spam, ~is_spam):
        digit_mask = label_mask & (styles == "digits_only")
        placeholder_mask = label_mask & (styles == "placeholder_only")
        scores = log_odds_ratio(
            np.asarray(counts[digit_mask].sum(axis=0)).ravel(),
            np.asarray(counts[placeholder_mask].sum(axis=0)).ravel(),
            int(digit_mask.sum()),
            int(placeholder_mask.sum()),
        )
        style_scores = np.maximum(style_scores, np.abs(scores))

    return {
        "style_leaning": rank_words(words, style_scores, limit),
        "ham_leaning": rank_words(words, -label_scores, limit),
        "spam_leaning": rank_words(words, label_scores, limit),
    }


def list_hash(words: list[str]) -> str:
    """Return a hash that identifies a word list without revealing its words."""
    return hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()


def load_markers() -> dict:
    """Read the saved lists."""
    return json.loads(MARKERS_PATH.read_text(encoding="utf-8"))


def main() -> int:
    train = load_split("train")
    lists = derive_markers(train)
    write_report(
        {
            "split_used": "train",
            "min_rows_per_word": MIN_ROWS_PER_WORD,
            "lists": lists,
            "list_sha256": {name: list_hash(words) for name, words in lists.items()},
        },
        MARKERS_PATH,
    )
    print({name: len(words) for name, words in lists.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
