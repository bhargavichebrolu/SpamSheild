"""Explain a prediction from a linear model, using the model's own numbers.

A Linear SVM's score is a sum: intercept + (TF-IDF value x learned weight) for each term.
So each term's part in the score can be calculated exactly, with no approximation.

This shows which terms moved this score. It doesn't show why a message is spam, how the
model would respond to other wording, or that a term would mean the same in another message.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

NOTE = (
    "These terms influenced this score, using the model's learned weights. They do not "
    "prove why a message is or isn't spam. Terms are shown as the model sees them, so "
    "'escapenumber' means a number."
)


def explain(
    row: sparse.csr_matrix,
    weights: np.ndarray,
    intercept: float,
    feature_names: np.ndarray,
    top_terms: int,
) -> dict:
    """Return the terms that pushed one message's score most towards each label.

    Only terms present in the message can appear. Positive contributions lean towards
    spam, and negative ones towards ham. other_terms_total covers everything not listed,
    so intercept + all listed contributions + other_terms_total equals the model's score.
    """
    indices = row.indices
    contributions = np.asarray(row.data, dtype=np.float64) * weights[indices]

    # Sorting by value, then by term, gives a repeatable order when contributions tie.
    terms = feature_names[indices]
    order = np.lexsort((terms, -contributions))
    towards_spam = [position for position in order if contributions[position] > 0][:top_terms]
    towards_ham = [position for position in order[::-1] if contributions[position] < 0][:top_terms]

    listed = np.zeros(len(indices), dtype=bool)
    listed[towards_spam] = True
    listed[towards_ham] = True

    def describe(position: int) -> dict:
        return {"term": str(terms[position]), "contribution": round(float(contributions[position]), 6)}

    return {
        "spam_terms": [describe(position) for position in towards_spam],
        "ham_terms": [describe(position) for position in towards_ham],
        "other_terms_total": round(float(contributions[~listed].sum()), 6),
        "intercept": round(float(intercept), 6),
        "note": NOTE,
    }
