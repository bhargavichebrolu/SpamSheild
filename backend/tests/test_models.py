"""Tests for the candidate models, selection rule and shared metrics. All text is made up."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from training import compare_models, evaluate
from training.models import F1_TIE_MARGIN, PARAMETER_GRID, build_classifier, select_best

TEXTS = [
    "win a free prize today",
    "free money and a prize",
    "claim your free prize now",
    "meeting moved to monday",
    "monday meeting notes attached",
    "notes from the monday meeting",
]
LABELS = pd.Series(["Spam", "Spam", "Spam", "Ham", "Ham", "Ham"])


def result(model: str, f1: float, flagged: int, *, features: str = "word_1", converged: bool = True) -> dict:
    return {
        "model": model,
        "features": features,
        "converged": converged,
        "metrics": {"f1_spam": f1, "ham_flagged_as_spam": flagged},
    }


def test_grid_is_small_and_covers_the_three_candidates() -> None:
    assert set(PARAMETER_GRID) == {"multinomial_nb", "logistic_regression", "linear_svm"}
    assert all(len(values) == 3 for _, values in PARAMETER_GRID.values())


@pytest.mark.parametrize(
    "model, setting",
    [(model, value) for model, (_, values) in PARAMETER_GRID.items() for value in values],
)
def test_every_candidate_fits_and_separates_simple_text(model: str, setting: float) -> None:
    matrix = TfidfVectorizer().fit_transform(TEXTS)
    classifier = build_classifier(model, setting).fit(matrix, LABELS)
    assert classifier.predict(matrix).tolist() == LABELS.tolist()
    assert evaluate.roc_auc(LABELS, evaluate.spam_scores(classifier, matrix)) == 1.0


def test_build_classifier_rejects_unknown_model() -> None:
    with pytest.raises(ValueError, match="Unknown model"):
        build_classifier("random_forest", 1.0)


def test_select_best_picks_clear_f1_winner_despite_more_flagged_ham() -> None:
    results = [result("linear_svm", 0.99, 50), result("multinomial_nb", 0.95, 1)]
    assert select_best(results)["model"] == "linear_svm"


def test_select_best_breaks_f1_ties_by_fewest_flagged_ham() -> None:
    gap = F1_TIE_MARGIN / 2
    results = [result("linear_svm", 0.98, 50), result("logistic_regression", 0.98 - gap, 40)]
    assert select_best(results)["model"] == "logistic_regression"


def test_select_best_does_not_treat_a_gap_at_the_margin_as_a_tie() -> None:
    results = [result("linear_svm", 0.98, 50), result("logistic_regression", 0.97, 1)]
    assert select_best(results)["model"] == "linear_svm"


def test_select_best_prefers_simpler_model_when_otherwise_equal() -> None:
    results = [result("linear_svm", 0.98, 10), result("logistic_regression", 0.98, 10)]
    assert select_best(results)["model"] == "logistic_regression"


def test_select_best_prefers_smaller_features_when_otherwise_equal() -> None:
    results = [
        result("linear_svm", 0.98, 10, features="word_1_2"),
        result("linear_svm", 0.98, 10, features="word_1"),
    ]
    assert select_best(results)["features"] == "word_1"


def test_select_best_ignores_runs_that_did_not_converge() -> None:
    results = [result("linear_svm", 0.99, 1, converged=False), result("multinomial_nb", 0.90, 5)]
    assert select_best(results)["model"] == "multinomial_nb"


def test_select_best_fails_clearly_with_nothing_eligible() -> None:
    with pytest.raises(ValueError, match="No converged results"):
        select_best([result("linear_svm", 0.99, 1, converged=False)])


def test_fit_classifier_reports_convergence() -> None:
    matrix = TfidfVectorizer().fit_transform(TEXTS)
    _, converged, seconds = compare_models.fit_classifier("logistic_regression", 1.0, matrix, LABELS)
    assert converged is True
    assert seconds >= 0


def test_spam_scores_rank_spam_above_ham_for_every_candidate() -> None:
    matrix = TfidfVectorizer().fit_transform(TEXTS)
    for model, (_, values) in PARAMETER_GRID.items():
        classifier = build_classifier(model, values[1]).fit(matrix, LABELS)
        scores = evaluate.spam_scores(classifier, matrix)
        assert scores[:3].min() > scores[3:].max()


def test_message_latency_measures_each_row() -> None:
    vectorizer = TfidfVectorizer().fit(TEXTS)
    classifier = build_classifier("multinomial_nb", 1.0).fit(vectorizer.transform(TEXTS), LABELS)
    latency = compare_models.message_latency_ms(vectorizer, classifier, pd.Series(TEXTS))
    assert latency["rows"] == len(TEXTS)
    assert latency["p95_ms"] >= latency["median_ms"] > 0


def test_comparison_never_loads_the_test_split(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: list[str] = []
    frame = pd.DataFrame({"label": LABELS, "text": TEXTS})

    def fake_load(split: str, **_: object) -> pd.DataFrame:
        requested.append(split)
        return frame

    monkeypatch.setattr(compare_models, "load_split", fake_load)
    monkeypatch.setattr(compare_models, "write_results", lambda report: report)
    monkeypatch.setitem(compare_models.FEATURE_SETS, "word_1", {"analyzer": "word"})
    monkeypatch.setattr(compare_models, "LATENCY_ROWS", 2)
    assert compare_models.main(["--features", "word_1"]) == 0
    assert requested == ["train", "validation"]


def test_similarity_to_training_finds_a_copy_and_is_low_for_unrelated_text() -> None:
    train = pd.Series(["free prize money today", "project meeting agenda notes"] * 2)
    texts = pd.Series(["free prize money today", "completely different words here"])
    vectorizer_settings = {"min_df": 1, "max_df": 1.0}

    original = evaluate.build_vectorizer

    def relaxed(name: str):
        return original(name).set_params(**vectorizer_settings)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(evaluate, "build_vectorizer", relaxed)
        similarity = evaluate.similarity_to_training(train, texts)
    assert similarity[0] == pytest.approx(1.0)
    assert similarity[1] == pytest.approx(0.0)


def test_roc_auc_is_half_for_uninformative_scores() -> None:
    assert evaluate.roc_auc(pd.Series(["Spam", "Ham", "Spam", "Ham"]), np.array([1, 1, 1, 1])) == 0.5
