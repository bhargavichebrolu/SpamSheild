"""Candidate classifiers, their small settings grid, and the model-selection rule.

The selection rule was fixed before any model comparison was run, so it can't be
adjusted to favour a particular result. It only ever sees validation metrics.
"""

from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from training.config import RANDOM_SEED

# Each candidate tries three values of its main setting, and no more, to limit cost.
# alpha is Naive Bayes smoothing. C is the inverse of regularisation strength.
PARAMETER_GRID: dict[str, tuple[str, tuple[float, ...]]] = {
    "multinomial_nb": ("alpha", (0.01, 0.1, 1.0)),
    "logistic_regression": ("C", (0.1, 1.0, 10.0)),
    "linear_svm": ("C", (0.1, 1.0, 10.0)),
}

# A smaller F1 gap than this is treated as a tie, as it's about the size of random variation.
F1_TIE_MARGIN = 0.002

# Used only for a tie on both F1 and flagged ham: prefer the simpler model.
SIMPLICITY_ORDER = ("multinomial_nb", "logistic_regression", "linear_svm")


def build_classifier(model: str, setting: float):
    """Return an unfitted classifier with the given value of its main setting."""
    if model == "multinomial_nb":
        return MultinomialNB(alpha=setting)
    if model == "logistic_regression":
        return LogisticRegression(solver="liblinear", C=setting, random_state=RANDOM_SEED)
    if model == "linear_svm":
        return LinearSVC(C=setting, random_state=RANDOM_SEED)
    raise ValueError(f"Unknown model: {model!r}")


def select_best(results: list[dict]) -> dict:
    """Choose a result using validation metrics, by the fixed rule.

    1. Find the highest F1 for Spam, among runs that converged.
    2. Treat every run within F1_TIE_MARGIN of it as tied.
    3. Among ties, choose the fewest legitimate messages flagged as spam.
    4. If still tied, choose the simplest model, and then the smaller feature set.
    """
    eligible = [result for result in results if result["converged"]]
    if not eligible:
        raise ValueError("No converged results to select from")
    best_f1 = max(result["metrics"]["f1_spam"] for result in eligible)
    tied = [result for result in eligible if best_f1 - result["metrics"]["f1_spam"] < F1_TIE_MARGIN]
    return min(
        tied,
        key=lambda result: (
            result["metrics"]["ham_flagged_as_spam"],
            SIMPLICITY_ORDER.index(result["model"]),
            result["features"],
        ),
    )
