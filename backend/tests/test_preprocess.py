"""Tests for the preprocessing shared by training and inference. All text is made up."""

from __future__ import annotations

import pytest

from app.ml.preprocess import (
    MAX_TEXT_CHARS,
    collapse_whitespace,
    preprocess_text,
    remove_escapelong,
    truncate,
    unify_numbers,
    unify_url_scheme,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("call 555 now", "call escapenumber now"),
        ("sha1 hash", "shaescapenumber hash"),
        ("10 / 18 / 01", "escapenumber / escapenumber / escapenumber"),
        ("no numbers here", "no numbers here"),
        ("already escapenumber", "already escapenumber"),
    ],
)
def test_unify_numbers(text: str, expected: str) -> None:
    assert unify_numbers(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("a escapelong b", "a   b"),
        ("escapelong", " "),
        ("escapelongest stays", "escapelongest stays"),
    ],
)
def test_remove_escapelong_matches_whole_word_only(text: str, expected: str) -> None:
    assert remove_escapelong(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("visit https www example", "visit http www example"),
        ("https://example.com", "http://example.com"),
        ("http stays", "http stays"),
        ("httpsx stays", "httpsx stays"),
    ],
)
def test_unify_url_scheme(text: str, expected: str) -> None:
    assert unify_url_scheme(text) == expected


def test_collapse_whitespace_handles_tabs_newlines_and_edges() -> None:
    assert collapse_whitespace("  a\t\tb\n\nc  ") == "a b c"


def test_truncate() -> None:
    assert truncate("abcdef", max_chars=3) == "abc"
    assert truncate("ab", max_chars=3) == "ab"


def test_preprocess_makes_real_style_email_match_the_dataset_style() -> None:
    raw = "WIN  $500 at\nHTTPS://Example.com TODAY!"
    assert preprocess_text(raw) == "win $escapenumber at http://example.com today!"


def test_preprocess_handles_capitalised_escapelong() -> None:
    assert preprocess_text("Hello EscapeLong world") == "hello world"


def test_preprocess_limits_length() -> None:
    assert len(preprocess_text("a" * (MAX_TEXT_CHARS + 500))) == MAX_TEXT_CHARS


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_preprocess_returns_empty_for_blank_text(text: str) -> None:
    assert preprocess_text(text) == ""


@pytest.mark.parametrize(
    "text",
    ["Win $500 NOW at https://example.com", "a  b\nc 12", "escapelong only", ""],
)
def test_preprocess_is_stable_when_repeated(text: str) -> None:
    once = preprocess_text(text)
    assert preprocess_text(once) == once
