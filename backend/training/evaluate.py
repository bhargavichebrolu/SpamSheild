"""Metrics shared by the experiments, model comparison and final evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

from training.features import build_vectorizer

NEAR_DUPLICATE_BATCH_ROWS = 100
SIMILARITY_THRESHOLDS = (0.80, 0.90, 0.95, 0.99)


def score(labels: pd.Series, predictions: np.ndarray) -> dict:
    """Return metrics with Spam as the positive class, and the two error types."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, pos_label="Spam", average="binary", zero_division=0
    )
    (true_ham, false_positive), (false_negative, true_spam) = confusion_matrix(
        labels, predictions, labels=["Ham", "Spam"]
    )
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 4),
        "precision_spam": round(float(precision), 4),
        "recall_spam": round(float(recall), 4),
        "f1_spam": round(float(f1), 4),
        "ham_flagged_as_spam": int(false_positive),
        "spam_missed": int(false_negative),
        "true_ham": int(true_ham),
        "true_spam": int(true_spam),
    }


def spam_scores(classifier, matrix: sparse.csr_matrix) -> np.ndarray:
    """Return a value that ranks rows from least to most spam-like.

    Linear SVM and Logistic Regression provide decision_function, and Naive Bayes
    provides predict_proba. These values rank rows, but aren't comparable across
    models, and only some models' values can be read as probabilities.
    """
    spam_column = list(classifier.classes_).index("Spam")
    if hasattr(classifier, "decision_function"):
        values = classifier.decision_function(matrix)
        return values if spam_column == 1 else -values
    return classifier.predict_proba(matrix)[:, spam_column]


def roc_auc(labels: pd.Series, ranking_scores: np.ndarray) -> float:
    """Return the chance that a random spam row ranks above a random ham row."""
    return round(float(roc_auc_score(labels == "Spam", ranking_scores)), 4)


def closest_training_similarity(
    rows: sparse.csr_matrix,
    train_matrix: sparse.csr_matrix,
    batch_rows: int = NEAR_DUPLICATE_BATCH_ROWS,
) -> np.ndarray:
    """Return each row's cosine similarity to its most similar training row.

    TF-IDF rows have unit length, so multiplying them gives their cosine similarity.
    Working in batches limits how much memory the multiplication needs.
    """
    closest: list[np.ndarray] = []
    for start in range(0, rows.shape[0], batch_rows):
        similarities = rows[start : start + batch_rows] @ train_matrix.T
        closest.append(similarities.max(axis=1).toarray().ravel())
    return np.concatenate(closest) if closest else np.empty(0)


def similarity_to_training(train_texts: pd.Series, texts: pd.Series) -> np.ndarray:
    """Return each text's closest similarity to the training texts, using word_1 TF-IDF.

    The vectoriser is fitted on the training texts only.
    """
    vectorizer = build_vectorizer("word_1")
    train_matrix = vectorizer.fit_transform(train_texts).tocsr()
    return closest_training_similarity(vectorizer.transform(texts).tocsr(), train_matrix)


def shares_at_or_above(
    similarity: np.ndarray,
    thresholds: tuple[float, ...] = SIMILARITY_THRESHOLDS,
) -> dict[str, float]:
    """Return the share of rows whose closest training row reaches each similarity."""
    return {f"{threshold:.2f}": round(float((similarity >= threshold).mean()), 4) for threshold in thresholds}


def score_by_similarity_band(
    similarity: np.ndarray,
    labels: pd.Series,
    predictions: np.ndarray,
) -> dict[str, dict]:
    """Score rows separately by how similar they are to their closest training row.

    The lowest band shows performance on messages with no close match in training.
    """
    edges = (0.0, *SIMILARITY_THRESHOLDS[:3], np.inf)
    names = [
        f"{low:.2f}_to_{high:.2f}" if np.isfinite(high) else f"{low:.2f}_and_above"
        for low, high in zip(edges, edges[1:])
    ]
    bands = {}
    label_values = labels.to_numpy()
    for name, low, high in zip(names, edges, edges[1:]):
        mask = (similarity >= low) & (similarity < high)
        band_labels = pd.Series(label_values[mask])
        bands[name] = {
            "rows": int(mask.sum()),
            "share_of_rows": round(float(mask.mean()), 4),
            "spam_share": round(float((band_labels == "Spam").mean()), 4) if mask.any() else None,
            "metrics": score(band_labels, predictions[mask]) if mask.any() else None,
        }
    return bands
