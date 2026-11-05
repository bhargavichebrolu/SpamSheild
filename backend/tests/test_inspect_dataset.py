"""Tests for the dataset inspection script. All text here is made up."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from training import inspect_dataset as inspect

SAMPLE_CSV = (
    "label,text\n"
    "Spam,win a free prize\n"
    "Ham,Meeting moved to Monday\n"
    "Ham,  meeting   MOVED to monday  \n"
    "Spam,hi\n"
    "Ham,hi\n"
    "Ham,\n"
    "Spam,\n"
    'Ham,"   "\n'
    "Ham,null\n"
    "Spam,NA\n"
    "Ham,enron deal notes\n"
    "Spam,enronic words and enron1 text\n"
    'Spam,"line one\nline two, with a comma"\n'
)


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    path.write_text(SAMPLE_CSV, encoding="utf-8", newline="\n")
    return path


@pytest.fixture
def df(csv_path: Path) -> pd.DataFrame:
    return inspect.load_dataset(csv_path)


def report_for(csv_path: Path) -> dict:
    frame = inspect.load_dataset(csv_path)
    return inspect.build_report(frame, csv_path, inspect.sha256_file(csv_path))


def test_load_keeps_null_like_text_as_literal_text(df: pd.DataFrame) -> None:
    assert df["text"].isna().sum() == 0
    assert {"null", "NA"} <= set(df["text"])


def test_load_handles_quoted_newlines_and_commas(df: pd.DataFrame) -> None:
    assert len(df) == 13
    assert df["text"].iloc[-1] == "line one\nline two, with a comma"


def test_load_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_bytes(b"label,text\nHam,caf\xe9\n")
    with pytest.raises(UnicodeDecodeError):
        inspect.load_dataset(path)


def test_validate_schema_accepts_expected_structure(df: pd.DataFrame) -> None:
    inspect.validate_schema(df)


@pytest.mark.parametrize(
    "frame, message",
    [
        (pd.DataFrame({"category": ["Ham"], "text": ["hello"]}), "Expected columns"),
        (pd.DataFrame({"text": ["hello"], "label": ["Ham"]}), "Expected columns"),
        (pd.DataFrame({"label": ["ham"], "text": ["hello"]}), "Unexpected label"),
    ],
)
def test_validate_schema_rejects_unexpected_structure(frame: pd.DataFrame, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        inspect.validate_schema(frame)


def test_verify_hash(csv_path: Path) -> None:
    expected = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert inspect.verify_hash(csv_path, expected) == expected
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        inspect.verify_hash(csv_path, "0" * 64)


def test_blank_text_counts(csv_path: Path) -> None:
    report = report_for(csv_path)
    assert report["blank_text"] == {
        "empty_rows": {"Ham": 1, "Spam": 1},
        "whitespace_only_rows": 1,
    }


def test_counts_text_pandas_would_treat_as_missing(csv_path: Path) -> None:
    assert report_for(csv_path)["text_pandas_would_treat_as_missing_by_default"] == 2


def test_duplicate_and_conflict_counts(df: pd.DataFrame) -> None:
    duplicates = inspect.summarise_duplicates(df)
    assert duplicates["identical_rows"] == 0
    # "hi" repeats once, and the empty text repeats once.
    assert duplicates["exact_duplicate_text_rows"] == 2
    assert duplicates["exact_conflicting_labels"] == {"texts": 2, "rows": 4}
    # "hi" again, plus the two "meeting moved" rows that differ only in case and spacing.
    assert duplicates["normalised_duplicate_rows"] == 2
    assert duplicates["normalised_conflicting_labels"] == {"texts": 1, "rows": 2}


def test_lengths_exclude_blank_rows_and_group_by_label() -> None:
    frame = pd.DataFrame(
        {"label": ["Ham", "Ham", "Ham", "Spam"], "text": ["a", "abc", "", "abcd"]}
    )
    lengths = inspect.summarise_lengths(frame)
    assert lengths["by_label"]["Ham"]["rows"] == 2
    assert lengths["by_label"]["Ham"]["min"] == 1
    assert lengths["by_label"]["Ham"]["max"] == 3
    assert lengths["by_label"]["Spam"]["median"] == 4
    assert lengths["rows_under_20_chars"] == {"Ham": 2, "Spam": 1}
    assert lengths["rows_over_chars"]["20000"] == 0


def test_marker_matches_whole_words_case_insensitively() -> None:
    frame = pd.DataFrame(
        {
            "label": ["Ham", "Ham", "Spam", "Spam"],
            "text": ["Enron memo", "enron1 notes", "enronic text", "plain text"],
        }
    )
    frequency = inspect.marker_document_frequency(frame, ("enron",))
    assert frequency == {"enron": {"Ham": 1.0, "Spam": 0.0}}


def test_report_contains_no_email_text_or_local_paths(csv_path: Path) -> None:
    serialised = json.dumps(report_for(csv_path))
    assert "prize" not in serialised
    assert str(csv_path.parent) not in serialised


def test_identical_input_writes_identical_report(csv_path: Path, tmp_path: Path) -> None:
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    expected = inspect.sha256_file(csv_path)
    for report in (first, second):
        args = ["--csv", str(csv_path), "--report", str(report), "--expected-sha256", expected]
        assert inspect.main(args) == 0
    assert first.read_bytes() == second.read_bytes()


def test_main_reports_failure_without_writing_a_report(csv_path: Path, tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    wrong_hash = ["--csv", str(csv_path), "--report", str(report), "--expected-sha256", "0" * 64]
    missing_file = ["--csv", str(tmp_path / "missing.csv"), "--report", str(report)]
    assert inspect.main(wrong_hash) == 1
    assert inspect.main(missing_file) == 1
    assert not report.exists()


def test_print_examples_truncates_text(df: pd.DataFrame, capsys: pytest.CaptureFixture[str]) -> None:
    inspect.print_examples(df, per_label=1, max_chars=5)
    assert capsys.readouterr().out.splitlines() == ["[Ham] Meeti", "[Spam] win a"]
