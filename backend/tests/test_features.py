"""Tests for feature extraction and the analysis helpers. All text is made up."""

from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from app.ml.preprocess import preprocess_text
from training import analyse_format, analyse_vocabulary
from training import feature_experiments as experiments
from training.features import FEATURE_SETS, build_vectorizer

TRAIN_TEXTS = [
    "win a free prize today",
    "free prize for you",
    "meeting moved to monday",
    "monday meeting notes attached",
    "free money and a free prize",
    "notes from the monday meeting",
]


@pytest.mark.parametrize("name", sorted(FEATURE_SETS))
def test_every_feature_set_builds_and_produces_a_sparse_matrix(name: str) -> None:
    vectorizer = build_vectorizer(name)
    # These small texts would fail min_df, so only test the configured type here.
    vectorizer.set_params(min_df=1, max_df=1.0, stop_words=None)
    matrix = vectorizer.fit_transform(TRAIN_TEXTS)
    assert sparse.issparse(matrix)
    assert matrix.shape[0] == len(TRAIN_TEXTS)
    assert matrix.dtype == np.float32


def test_vocabulary_is_learned_only_from_fitted_text() -> None:
    vectorizer = build_vectorizer("word_1").set_params(min_df=1, max_df=1.0)
    vectorizer.fit(TRAIN_TEXTS)
    unseen = vectorizer.transform(["completelyunseenword"])
    assert "completelyunseenword" not in vectorizer.vocabulary_
    assert unseen.nnz == 0


def test_transform_does_not_change_the_fitted_vocabulary() -> None:
    vectorizer = build_vectorizer("word_1").set_params(min_df=1, max_df=1.0)
    vectorizer.fit(TRAIN_TEXTS)
    before = dict(vectorizer.vocabulary_)
    vectorizer.transform(["brand new words appear here"])
    assert vectorizer.vocabulary_ == before


def test_vectorizer_applies_project_preprocessing_at_inference() -> None:
    vectorizer = build_vectorizer("word_1").set_params(min_df=1, max_df=1.0)
    vectorizer.fit(["call escapenumber now", "http link here"])
    raw_style = vectorizer.transform(["CALL 555 NOW at HTTPS link"]).toarray()
    processed = vectorizer.transform([preprocess_text("CALL 555 NOW at HTTPS link")]).toarray()
    assert np.array_equal(raw_style, processed)
    assert vectorizer.vocabulary_["escapenumber"] < raw_style.shape[1]
    assert raw_style[0, vectorizer.vocabulary_["escapenumber"]] > 0


def test_fitted_vectorizer_keeps_working_after_save_and_reload() -> None:
    vectorizer = build_vectorizer("word_1").set_params(min_df=1, max_df=1.0)
    vectorizer.fit(TRAIN_TEXTS)
    reloaded = pickle.loads(pickle.dumps(vectorizer))
    texts = ["Free prize for 100 people on Monday"]
    assert (vectorizer.transform(texts) != reloaded.transform(texts)).nnz == 0


def test_stratified_sample_keeps_balance_and_is_reproducible() -> None:
    frame = pd.DataFrame({"label": ["Ham"] * 80 + ["Spam"] * 20, "text": [str(i) for i in range(100)]})
    first = experiments.stratified_sample(frame, 50)
    second = experiments.stratified_sample(frame, 50)
    assert first.equals(second)
    assert first["label"].value_counts().to_dict() == {"Ham": 40, "Spam": 10}


def test_stratified_sample_returns_everything_when_rows_is_none() -> None:
    frame = pd.DataFrame({"label": ["Ham", "Spam"], "text": ["a", "b"]})
    assert experiments.stratified_sample(frame, None) is frame


def test_score_treats_spam_as_the_positive_class() -> None:
    labels = pd.Series(["Spam", "Spam", "Spam", "Ham", "Ham"])
    predictions = np.array(["Spam", "Spam", "Ham", "Spam", "Ham"])
    metrics = experiments.score(labels, predictions)
    assert metrics["ham_flagged_as_spam"] == 1
    assert metrics["spam_missed"] == 1
    assert metrics["true_spam"] == 2
    assert metrics["true_ham"] == 1
    assert metrics["precision_spam"] == pytest.approx(2 / 3, abs=1e-4)
    assert metrics["recall_spam"] == pytest.approx(2 / 3, abs=1e-4)
    assert metrics["accuracy"] == pytest.approx(0.6)


def test_every_experiment_uses_known_settings() -> None:
    for experiment in experiments.EXPERIMENTS.values():
        assert experiment.features in FEATURE_SETS
        assert experiment.preprocessing in experiments.PREPROCESSORS


def test_experiments_never_load_the_test_split(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: list[str] = []
    frame = pd.DataFrame(
        {"label": ["Ham", "Spam"] * 5, "text": ["meeting monday notes", "free prize money"] * 5}
    )

    def fake_load(split: str, **_: object) -> pd.DataFrame:
        requested.append(split)
        return frame

    monkeypatch.setattr(experiments, "load_split", fake_load)
    monkeypatch.setattr(experiments, "save_result", lambda result: None)
    monkeypatch.setitem(
        experiments.EXPERIMENTS,
        "tiny",
        experiments.Experiment("tiny", "sample", "full", "word_1"),
    )
    experiments.run_one("tiny")
    assert requested == ["train", "validation"]


def test_closest_training_similarity_finds_the_best_match_across_batches() -> None:
    train = sparse.csr_matrix(np.array([[1.0, 0.0], [0.0, 1.0]]))
    rows = sparse.csr_matrix(np.array([[1.0, 0.0], [0.6, 0.8], [0.8, 0.6]]))
    similarity = experiments.closest_training_similarity(rows, train, batch_rows=2)
    assert similarity == pytest.approx([1.0, 0.8, 0.8])


def test_shares_at_or_above_counts_rows_reaching_each_threshold() -> None:
    similarity = np.array([1.0, 0.8, 0.5, 0.95])
    assert experiments.shares_at_or_above(similarity, thresholds=(0.75, 0.9)) == {"0.75": 0.75, "0.90": 0.5}


def test_score_by_similarity_band_puts_each_row_in_exactly_one_band() -> None:
    similarity = np.array([0.1, 0.79, 0.8, 0.9, 0.95, 1.0])
    labels = pd.Series(["Spam", "Ham", "Spam", "Ham", "Spam", "Ham"])
    predictions = np.array(["Ham", "Ham", "Spam", "Spam", "Spam", "Ham"])
    bands = experiments.score_by_similarity_band(similarity, labels, predictions)

    assert sum(band["rows"] for band in bands.values()) == len(labels)
    novel = bands["0.00_to_0.80"]
    assert novel["rows"] == 2
    assert novel["metrics"]["spam_missed"] == 1
    assert novel["metrics"]["true_ham"] == 1
    assert bands["0.95_and_above"]["rows"] == 2


def test_score_by_similarity_band_handles_an_empty_band() -> None:
    bands = experiments.score_by_similarity_band(
        np.array([0.1]), pd.Series(["Ham"]), np.array(["Ham"])
    )
    assert bands["0.95_and_above"] == {
        "rows": 0,
        "share_of_rows": 0.0,
        "spam_share": None,
        "metrics": None,
    }


def test_peak_memory_is_measured() -> None:
    peak = experiments.peak_memory_gb()
    assert peak is None or peak > 0


def test_log_odds_sign_follows_the_leaning_label() -> None:
    scores = analyse_vocabulary.log_odds_ratio(
        np.array([90, 10, 50]), np.array([10, 90, 50]), 100, 100
    )
    assert scores[0] > 0
    assert scores[1] < 0
    assert scores[2] == pytest.approx(0)


def test_vocabulary_report_uses_single_words_and_no_message_text() -> None:
    train = pd.DataFrame(
        {
            "label": ["Spam"] * 60 + ["Ham"] * 60,
            "text": ["cheap pills offer"] * 60 + ["project meeting agenda"] * 60,
        }
    )
    report = analyse_vocabulary.build_report(train)
    assert report["split_used"] == "train"
    assert report["most_spam_leaning"][0]["word"] in {"cheap", "pills", "offer"}
    assert report["most_ham_leaning"][0]["word"] in {"project", "meeting", "agenda"}
    assert "cheap pills offer" not in str(report)


def test_number_style_classifies_each_combination() -> None:
    digits = pd.Series([True, False, True, False])
    placeholder = pd.Series([False, True, True, False])
    styles = analyse_format.number_style(digits, placeholder)
    assert styles.tolist() == ["digits_only", "placeholder_only", "both", "neither"]


def test_longest_token_length() -> None:
    assert analyse_format.longest_token_length("ab abcd-efg") == 4
    assert analyse_format.longest_token_length("...") == 0


def test_format_report_contains_no_message_text() -> None:
    frame = pd.DataFrame({"label": ["Ham", "Spam", "Ham"], "text": ["secret phrase 12", "other WORDS", ""]})
    report = analyse_format.build_report(frame)
    assert report["rows_analysed"] == 2
    assert report["flags_by_label"]["has_uppercase"]["Spam"]["rows"] == 1
    assert "secret" not in str(report)


def test_format_report_handles_a_group_with_no_rows() -> None:
    frame = pd.DataFrame({"label": ["Ham"], "text": ["no placeholder here"]})
    summary = analyse_format.build_report(frame)["longest_token_length"]["with_escapelong"]
    assert summary == {"rows": 0, "median": None, "p99": None, "p999": None, "max": None}
