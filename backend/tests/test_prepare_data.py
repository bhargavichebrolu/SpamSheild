"""Tests for cleaning, splitting and the leakage safeguards. All text is made up."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from training import prepare_data as prepare


def make_frame(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["label", "text"])


def balanced_labels(rows_per_label: int = 500) -> pd.Series:
    return pd.Series(["Ham"] * rows_per_label + ["Spam"] * rows_per_label)


def test_clean_removes_blank_rows_and_rows_without_word_tokens() -> None:
    kept, counts = prepare.clean_rows(
        make_frame([("Ham", ""), ("Spam", "   "), ("Ham", "."), ("Spam", "a !"), ("Ham", "real text")])
    )
    assert counts["removed_blank"] == 2
    assert counts["removed_no_word_tokens"] == 2
    assert kept.index.tolist() == [4]


def test_clean_keeps_first_copy_of_rows_identical_after_preprocessing() -> None:
    kept, counts = prepare.clean_rows(
        make_frame(
            [
                ("Spam", "Win 100 dollars"),
                ("Spam", "win   200 DOLLARS"),
                ("Spam", "win escapenumber dollars"),
                ("Ham", "different text"),
            ]
        )
    )
    assert counts["removed_duplicates"] == 2
    assert counts["removed_conflicting_labels"] == 0
    assert kept.index.tolist() == [0, 3]


def test_clean_removes_every_copy_of_text_with_conflicting_labels() -> None:
    kept, counts = prepare.clean_rows(
        make_frame(
            [
                ("Ham", "hello there"),
                ("Spam", "HELLO there"),
                ("Ham", "hello  there"),
                ("Ham", "kept text"),
            ]
        )
    )
    assert counts["removed_conflicting_labels"] == 3
    assert counts["conflicting_label_texts"] == 1
    assert counts["removed_duplicates"] == 0
    assert kept.index.tolist() == [3]


def test_clean_counts_add_up() -> None:
    rows = [("Ham", ""), ("Ham", "."), ("Ham", "dup"), ("Ham", "dup"), ("Ham", "x y"), ("Spam", "ab"), ("Ham", "ab")]
    _, counts = prepare.clean_rows(make_frame(rows))
    removed = sum(value for key, value in counts.items() if key.startswith("removed_"))
    assert counts["rows_in"] == removed + counts["rows_kept"]


def test_clean_returned_frame_contains_no_text() -> None:
    kept, _ = prepare.clean_rows(make_frame([("Ham", "secret words")]))
    assert list(kept.columns) == ["label", "fingerprint"]


def test_assign_splits_uses_expected_shares_and_keeps_label_balance() -> None:
    labels = balanced_labels()
    splits = prepare.assign_splits(labels)
    assert splits.value_counts().to_dict() == {"train": 800, "validation": 100, "test": 100}
    balance = pd.crosstab(splits, labels)
    assert (balance["Ham"] == balance["Spam"]).all()


def test_assign_splits_is_reproducible_for_a_seed() -> None:
    labels = balanced_labels()
    assert prepare.assign_splits(labels, seed=1).equals(prepare.assign_splits(labels, seed=1))
    assert not prepare.assign_splits(labels, seed=1).equals(prepare.assign_splits(labels, seed=2))


def test_assign_splits_gives_every_row_exactly_one_split() -> None:
    labels = balanced_labels()
    splits = prepare.assign_splits(labels)
    assert splits.index.equals(labels.index)
    assert splits.notna().all()


def test_verify_no_overlap_accepts_separate_texts() -> None:
    fingerprints = pd.Series(["a", "a", "b"])
    splits = pd.Series(["train", "train", "test"])
    assert prepare.verify_no_overlap(fingerprints, splits) == 0


def test_verify_no_overlap_rejects_text_in_two_splits() -> None:
    fingerprints = pd.Series(["a", "a", "b"])
    splits = pd.Series(["train", "test", "test"])
    with pytest.raises(ValueError, match="1 preprocessed texts"):
        prepare.verify_no_overlap(fingerprints, splits)


@pytest.fixture
def split_files(tmp_path: Path) -> tuple[Path, Path]:
    csv_path = tmp_path / "raw.csv"
    csv_path.write_text(
        "label,text\nHam,zero\nSpam,one\nHam,two\nSpam,three\n", encoding="utf-8", newline="\n"
    )
    assignments = tmp_path / "assignments.csv"
    prepare.save_assignments(
        pd.Series(["train", "test", "validation", "train"], index=[0, 1, 2, 3], name="split"),
        assignments,
    )
    return csv_path, assignments


def test_load_split_returns_only_that_splits_rows(split_files: tuple[Path, Path]) -> None:
    csv_path, assignments = split_files
    train = prepare.load_split("train", csv_path=csv_path, assignments_path=assignments)
    assert train["text"].tolist() == ["zero", "three"]
    validation = prepare.load_split("validation", csv_path=csv_path, assignments_path=assignments)
    assert validation["text"].tolist() == ["two"]


def test_load_split_refuses_the_test_split_by_default(split_files: tuple[Path, Path]) -> None:
    csv_path, assignments = split_files
    with pytest.raises(PermissionError, match="reserved for final evaluation"):
        prepare.load_split("test", csv_path=csv_path, assignments_path=assignments)


def test_load_split_returns_test_rows_only_when_explicitly_allowed(split_files: tuple[Path, Path]) -> None:
    csv_path, assignments = split_files
    test = prepare.load_split("test", allow_test=True, csv_path=csv_path, assignments_path=assignments)
    assert test["text"].tolist() == ["one"]


def test_load_split_rejects_unknown_split(split_files: tuple[Path, Path]) -> None:
    csv_path, assignments = split_files
    with pytest.raises(ValueError, match="No rows found"):
        prepare.load_split("training", csv_path=csv_path, assignments_path=assignments)
