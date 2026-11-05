"""Find the words that most separate the labels, using training data only.

This shows what a model is likely to rely on, including words that may reveal a
message's source rather than whether it is spam. Milestone 3's source-leakage
experiment can use this list, so it must not be influenced by validation or test data.

The report is excluded from Git because its words can include people's surnames.

Run from the backend folder:
    python -m training.analyse_vocabulary
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from app.ml.preprocess import preprocess_text
from training.config import REPORTS_DIR
from training.inspect_dataset import write_report
from training.prepare_data import load_split

DEFAULT_REPORT = REPORTS_DIR / "vocabulary_analysis.json"

# Ignore words in very few messages, whose scores would be unreliable.
MIN_ROWS_PER_WORD = 50
TOP_WORDS = 40
WATCHED_WORDS = ("enron", "subject", "http", "https", "www", "escapenumber", "unsubscribe")


def log_odds_ratio(spam_rows: np.ndarray, ham_rows: np.ndarray, spam_total: int, ham_total: int) -> np.ndarray:
    """Return how much more likely each word is in spam than in ham.

    Positive scores lean towards spam, and negative scores towards ham. Adding 0.5 to
    every count avoids dividing by zero for words seen under only one label.
    """
    spam_odds = (spam_rows + 0.5) / (spam_total - spam_rows + 0.5)
    ham_odds = (ham_rows + 0.5) / (ham_total - ham_rows + 0.5)
    return np.log(spam_odds / ham_odds)


def build_report(train: pd.DataFrame) -> dict:
    """Build the vocabulary report from training rows. It holds single words and counts only."""
    vectorizer = CountVectorizer(
        preprocessor=preprocess_text,
        lowercase=False,
        binary=True,
        min_df=MIN_ROWS_PER_WORD,
        dtype=np.int32,
    )
    counts = vectorizer.fit_transform(train["text"])
    words = vectorizer.get_feature_names_out()

    is_spam = (train["label"] == "Spam").to_numpy()
    spam_total, ham_total = int(is_spam.sum()), int((~is_spam).sum())
    spam_rows = np.asarray(counts[is_spam].sum(axis=0)).ravel()
    ham_rows = np.asarray(counts[~is_spam].sum(axis=0)).ravel()
    scores = log_odds_ratio(spam_rows, ham_rows, spam_total, ham_total)

    def describe(position: int) -> dict:
        return {
            "word": str(words[position]),
            "log_odds": round(float(scores[position]), 3),
            "spam_share": round(float(spam_rows[position] / spam_total), 4),
            "ham_share": round(float(ham_rows[position] / ham_total), 4),
        }

    order = np.argsort(scores)
    position_of = {str(word): position for position, word in enumerate(words)}
    return {
        "rows_analysed": {"spam": spam_total, "ham": ham_total},
        "split_used": "train",
        "words_scored": int(len(words)),
        "min_rows_per_word": MIN_ROWS_PER_WORD,
        "most_ham_leaning": [describe(int(position)) for position in order[:TOP_WORDS]],
        "most_spam_leaning": [describe(int(position)) for position in order[::-1][:TOP_WORDS]],
        "watched_words": {
            word: describe(position_of[word]) if word in position_of else None
            for word in WATCHED_WORDS
        },
    }


def main() -> int:
    report = build_report(load_split("train"))
    write_report(report, DEFAULT_REPORT)
    print(f"Report written to {DEFAULT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
