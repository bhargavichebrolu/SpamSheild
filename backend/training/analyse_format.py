"""Describe the text format of the raw dataset, to inform preprocessing decisions.

This runs before the data is split, so it may include rows that later become test
data. It is limited to describing the file's format. No model is evaluated, and it
doesn't choose words as features. Word-level analysis runs on training data only,
in analyse_vocabulary.py.

Run from the backend folder:
    python -m training.analyse_format
"""

from __future__ import annotations

import re

import pandas as pd

from training.config import REPORTS_DIR
from training.inspect_dataset import (
    DEFAULT_CSV,
    EXPECTED_SHA256,
    is_blank,
    load_dataset,
    validate_schema,
    verify_hash,
    write_report,
)

DEFAULT_REPORT = REPORTS_DIR / "format_analysis.json"

FORMAT_PATTERNS = {
    "has_uppercase": r"[A-Z]",
    "has_digit": r"[0-9]",
    "has_escapenumber": r"(?<![a-z])escapenumber(?![a-z])",
    "has_escapelong": r"(?<![a-z])escapelong(?![a-z])",
    "has_non_ascii": r"[^\x00-\x7f]",
    "has_spaced_punctuation": r" [.,!?;:] ",
    "has_url_scheme": r"https?://",
    "has_https_word": r"(?<![a-z])https(?![a-z])",
    "has_at_sign": r"@",
}

ALPHANUMERIC_TOKEN = re.compile(r"[A-Za-z0-9]+")


def format_flags(text: pd.Series) -> pd.DataFrame:
    """Return one True/False column per format pattern."""
    return pd.DataFrame(
        {name: text.str.contains(pattern, regex=True) for name, pattern in FORMAT_PATTERNS.items()}
    )


def number_style(has_digit: pd.Series, has_placeholder: pd.Series) -> pd.Series:
    """Classify how each row represents numbers."""
    styles = pd.Series("neither", index=has_digit.index, dtype="str")
    styles[has_digit & ~has_placeholder] = "digits_only"
    styles[~has_digit & has_placeholder] = "placeholder_only"
    styles[has_digit & has_placeholder] = "both"
    return styles


def longest_token_length(text: str) -> int:
    """Return the length of the longest run of letters and digits in the text."""
    return max(map(len, ALPHANUMERIC_TOKEN.findall(text)), default=0)


def describe(values: pd.Series) -> dict:
    """Summarise integer values with actual observed percentiles.

    An empty group has no statistics, so they are reported as None.
    """
    if values.empty:
        return {"rows": 0, "median": None, "p99": None, "p999": None, "max": None}
    return {
        "rows": int(values.size),
        "median": int(values.quantile(0.5, interpolation="lower")),
        "p99": int(values.quantile(0.99, interpolation="lower")),
        "p999": int(values.quantile(0.999, interpolation="lower")),
        "max": int(values.max()),
    }


def build_report(df: pd.DataFrame) -> dict:
    """Build the format report. It contains aggregates only, with no email text."""
    non_blank = df[~is_blank(df["text"])]
    flags = format_flags(non_blank["text"])
    labels = non_blank["label"]

    styles = number_style(flags["has_digit"], flags["has_escapenumber"])
    style_rows = pd.crosstab(styles, labels)
    label_totals = labels.value_counts()

    longest = non_blank["text"].map(longest_token_length)

    return {
        "rows_analysed": int(len(non_blank)),
        "flags_by_label": {
            name: {
                label: {"rows": int(found.sum()), "share": round(float(found.mean()), 4)}
                for label, found in flags[name].groupby(labels)
            }
            for name in flags.columns
        },
        "number_style": {
            style: {
                label: {
                    "rows": int(style_rows.loc[style, label]),
                    "share": round(float(style_rows.loc[style, label] / label_totals[label]), 4),
                }
                for label in style_rows.columns
            }
            for style in style_rows.index
        },
        "spaced_punctuation_share_by_number_style": {
            style: round(float(share), 4)
            for style, share in flags["has_spaced_punctuation"].groupby(styles).mean().items()
        },
        "longest_token_length": {
            "by_number_style": {style: describe(group) for style, group in longest.groupby(styles)},
            "with_escapelong": describe(longest[flags["has_escapelong"]]),
            "without_escapelong": describe(longest[~flags["has_escapelong"]]),
        },
    }


def main() -> int:
    verify_hash(DEFAULT_CSV, EXPECTED_SHA256)
    df = load_dataset(DEFAULT_CSV)
    validate_schema(df)
    report = build_report(df)
    write_report(report, DEFAULT_REPORT)
    print(DEFAULT_REPORT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
