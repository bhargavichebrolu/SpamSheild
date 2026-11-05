"""Tests for deriving source-marker word lists. All text is made up."""

from __future__ import annotations

import pandas as pd
import pytest

from training import source_markers


def training_rows() -> pd.DataFrame:
    """Build rows where acmecorp marks one style in both labels, and pills marks spam."""
    rows = []
    for number in range(30):
        rows.append(("Ham", f"acmecorp project notes {number}"))
        rows.append(("Spam", f"acmecorp cheap pills offer {number}"))
        rows.append(("Ham", "listserv project notes escapenumber"))
        rows.append(("Spam", "listserv cheap pills offer escapenumber"))
    return pd.DataFrame(rows, columns=["label", "text"])


def test_styles_use_the_raw_text() -> None:
    styles = source_markers.styles_of(pd.Series(["call 555", "call escapenumber", "no numbers"]))
    assert styles.tolist() == ["digits_only", "placeholder_only", "neither"]


def test_rank_words_breaks_ties_alphabetically() -> None:
    import numpy as np

    words = np.array(["b", "a", "c"])
    scores = np.array([1.0, 1.0, 2.0])
    assert source_markers.rank_words(words, scores, 3) == ["c", "a", "b"]
    assert source_markers.rank_words(words, scores, 1) == ["c"]


def test_derive_finds_style_and_label_words() -> None:
    lists = source_markers.derive_markers(training_rows(), min_rows=5, limit=2)
    assert set(lists["style_leaning"]) == {"acmecorp", "listserv"}
    assert "pills" in source_markers.derive_markers(training_rows(), min_rows=5, limit=3)["spam_leaning"]
    assert "project" in source_markers.derive_markers(training_rows(), min_rows=5, limit=2)["ham_leaning"]


def test_derive_is_reproducible() -> None:
    first = source_markers.derive_markers(training_rows(), min_rows=5)
    second = source_markers.derive_markers(training_rows(), min_rows=5)
    assert first == second


def test_derive_ignores_rare_words() -> None:
    rows = training_rows()
    rows.loc[len(rows)] = ["Spam", "onceonlyword"]
    lists = source_markers.derive_markers(rows, min_rows=5)
    assert all("onceonlyword" not in words for words in lists.values())


def test_list_hash_changes_with_the_list_and_hides_the_words() -> None:
    first = source_markers.list_hash(["alpha", "beta"])
    assert first != source_markers.list_hash(["alpha"])
    assert "alpha" not in first


def test_main_uses_training_data_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    requested: list[str] = []

    def fake_load(split: str, **_: object) -> pd.DataFrame:
        requested.append(split)
        return training_rows()

    monkeypatch.setattr(source_markers, "load_split", fake_load)
    monkeypatch.setattr(source_markers, "MARKERS_PATH", tmp_path / "markers.json")
    monkeypatch.setattr(source_markers, "MIN_ROWS_PER_WORD", 5)
    assert source_markers.main() == 0
    assert requested == ["train"]
    assert source_markers.load_markers()["split_used"] == "train"
