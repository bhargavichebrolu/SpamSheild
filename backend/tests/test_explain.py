"""Tests for prediction explanations. All text is made up."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from app.ml.explain import NOTE, explain
from app.ml.predict import LoadedModel, classify
from tests.conftest import REMOVED_WORD

FEATURES = np.array(["alpha", "beta", "delta", "gamma", "omega"])
WEIGHTS = np.array([2.0, -3.0, 1.0, -1.0, 100.0])


def row(values: dict[int, float]) -> sparse.csr_matrix:
    data = np.zeros((1, len(FEATURES)))
    for position, value in values.items():
        data[0, position] = value
    return sparse.csr_matrix(data)


def total(explanation: dict) -> float:
    listed = explanation["spam_terms"] + explanation["ham_terms"]
    return (
        explanation["intercept"]
        + explanation["other_terms_total"]
        + sum(item["contribution"] for item in listed)
    )


def test_contribution_is_the_tfidf_value_times_the_weight() -> None:
    explanation = explain(row({0: 0.5, 1: 0.2}), WEIGHTS, 0.0, FEATURES, top_terms=5)
    assert explanation["spam_terms"] == [{"term": "alpha", "contribution": 1.0}]
    assert explanation["ham_terms"] == [{"term": "beta", "contribution": -0.6}]


def test_terms_are_sorted_with_the_strongest_first() -> None:
    explanation = explain(row({0: 0.5, 2: 0.5, 1: 0.5, 3: 0.5}), WEIGHTS, 0.0, FEATURES, top_terms=5)
    assert [item["term"] for item in explanation["spam_terms"]] == ["alpha", "delta"]
    assert [item["term"] for item in explanation["ham_terms"]] == ["beta", "gamma"]


def test_only_terms_in_the_message_appear() -> None:
    explanation = explain(row({0: 0.5}), WEIGHTS, 0.0, FEATURES, top_terms=5)
    assert "omega" not in str(explanation)


def test_parts_add_up_to_the_score_even_when_terms_are_left_out() -> None:
    message = row({0: 0.5, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.1})
    explanation = explain(message, WEIGHTS, -0.7, FEATURES, top_terms=1)
    assert len(explanation["spam_terms"]) == 1
    assert len(explanation["ham_terms"]) == 1
    expected = -0.7 + float((message @ WEIGHTS)[0])
    assert total(explanation) == pytest.approx(expected, abs=1e-5)


def test_a_term_with_zero_weight_is_not_listed() -> None:
    explanation = explain(row({0: 0.5}), np.zeros(5), 0.0, FEATURES, top_terms=5)
    assert explanation["spam_terms"] == []
    assert explanation["ham_terms"] == []


def test_ties_have_a_repeatable_order() -> None:
    weights = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    explanation = explain(row({3: 0.5, 0: 0.5, 2: 0.5}), weights, 0.0, FEATURES, top_terms=5)
    assert [item["term"] for item in explanation["spam_terms"]] == ["alpha", "delta", "gamma"]


def test_note_does_not_claim_certainty() -> None:
    assert "do not prove" in NOTE


def test_explanation_adds_up_to_the_real_models_score(loaded_model: LoadedModel) -> None:
    text = "Win a FREE prize today, and review the meeting notes"
    result = classify(loaded_model, text)
    direct = float(loaded_model.pipeline.decision_function([text])[0])
    assert result["score"] == pytest.approx(direct, abs=1e-5)
    assert total(result["explanation"]) == pytest.approx(direct, abs=1e-4)


def test_explanation_never_shows_a_removed_word(loaded_model: LoadedModel) -> None:
    result = classify(loaded_model, f"{REMOVED_WORD} free prize")
    assert REMOVED_WORD not in str(result)
