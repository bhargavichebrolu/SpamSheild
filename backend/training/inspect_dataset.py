"""Inspect the raw spam/ham CSV and write a reproducible JSON report.

The input file is only read, never changed. The saved report holds aggregate
statistics and no email text. Use --show-examples to print short previews to
the terminal instead.

Run from the repository root:
    python backend/training/inspect_dataset.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BACKEND_DIR / "data" / "raw" / "spam_Emails_data.csv"
DEFAULT_REPORT = BACKEND_DIR / "reports" / "dataset_inspection.json"

EXPECTED_SHA256 = "e7f57b47676e456ebf9866dc1fd311a93e923458c76a22b6ea5c9439f4da58aa"
EXPECTED_COLUMNS = ["label", "text"]
EXPECTED_LABELS = {"Ham", "Spam"}

# Words that may reveal where a message came from, or how it was processed.
MARKER_WORDS = ("enron", "subject", "escapenumber", "escapelong", "http")

# Text values that pandas.read_csv would treat as missing by default (empty text excluded).
PANDAS_DEFAULT_NA_TEXT = frozenset({
    "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND",
    "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None", "n/a", "nan", "null",
})


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256, reading in chunks so the file is not held in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_hash(path: Path, expected: str) -> str:
    """Return the file's hash, or raise ValueError if it differs from the expected one."""
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}: expected {expected}, got {actual}")
    return actual


def load_dataset(path: Path) -> pd.DataFrame:
    """Load the CSV as literal text.

    keep_default_na=False stops email text such as "null" or "NA" becoming missing
    values. Strict UTF-8 decoding makes invalid bytes an error instead of hiding them.
    """
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        encoding_errors="strict",
    )


def validate_schema(df: pd.DataFrame) -> None:
    """Raise ValueError if the columns or label values are not the verified ones."""
    columns = list(df.columns)
    if columns != EXPECTED_COLUMNS:
        raise ValueError(f"Expected columns {EXPECTED_COLUMNS}, got {columns}")
    unexpected = set(df["label"].dropna().unique()) - EXPECTED_LABELS
    if unexpected:
        raise ValueError(f"Unexpected label values: {sorted(unexpected)}")


def fingerprint(text: str) -> str:
    """Return a short hash of the text, so duplicates can be found without a second copy."""
    return hashlib.blake2b(text.encode("utf-8"), digest_size=16).hexdigest()


def normalise_for_comparison(text: str) -> str:
    """Lowercase and collapse whitespace. Used only to compare texts, never to change the data."""
    return " ".join(text.lower().split())


def is_blank(text: pd.Series) -> pd.Series:
    """Return True for empty or whitespace-only text."""
    return text.str.strip() == ""


def count_conflicts(fingerprints: pd.Series, labels: pd.Series) -> dict[str, int]:
    """Count texts that appear under more than one label, and the rows involved."""
    label_counts = labels.groupby(fingerprints, sort=False).transform("nunique")
    conflicting = label_counts > 1
    return {
        "texts": int(fingerprints[conflicting].nunique()),
        "rows": int(conflicting.sum()),
    }


def summarise_duplicates(df: pd.DataFrame) -> dict:
    """Count exact duplicates over all rows, and near-duplicates over non-blank rows."""
    exact = df["text"].map(fingerprint)
    non_blank = df[~is_blank(df["text"])]
    normalised = non_blank["text"].map(lambda value: fingerprint(normalise_for_comparison(value)))
    return {
        "identical_rows": int(df.duplicated().sum()),
        "exact_duplicate_text_rows": int(exact.duplicated().sum()),
        "exact_conflicting_labels": count_conflicts(exact, df["label"]),
        "normalised_duplicate_rows": int(normalised.duplicated().sum()),
        "normalised_conflicting_labels": count_conflicts(normalised, non_blank["label"]),
    }


def describe_lengths(lengths: pd.Series) -> dict:
    """Summarise lengths in characters. Percentiles use actual values, without interpolation."""
    return {
        "rows": int(lengths.size),
        "min": int(lengths.min()),
        "median": int(lengths.quantile(0.5, interpolation="lower")),
        "p95": int(lengths.quantile(0.95, interpolation="lower")),
        "p99": int(lengths.quantile(0.99, interpolation="lower")),
        "max": int(lengths.max()),
        "mean": round(float(lengths.mean()), 1),
    }


def summarise_lengths(df: pd.DataFrame) -> dict:
    """Describe message lengths per label, plus counts of extreme lengths, for non-blank rows."""
    non_blank = df[~is_blank(df["text"])]
    lengths = non_blank["text"].str.len()
    return {
        "by_label": {
            label: describe_lengths(group)
            for label, group in lengths.groupby(non_blank["label"], sort=True)
        },
        "rows_under_20_chars": lengths[lengths < 20].groupby(non_blank["label"], sort=True).size().to_dict(),
        "rows_over_chars": {
            str(limit): int((lengths > limit).sum())
            for limit in (20_000, 50_000, 100_000, 1_000_000)
        },
    }


def marker_document_frequency(df: pd.DataFrame, markers: tuple[str, ...] = MARKER_WORDS) -> dict:
    """Return the share of each label's non-blank rows containing each marker as a whole word.

    A word boundary here means "not next to another letter", so "enron1" counts but
    "enronic" does not.
    """
    non_blank = df[~is_blank(df["text"])]
    result: dict[str, dict[str, float]] = {}
    for marker in markers:
        found = non_blank["text"].str.contains(
            rf"(?<![a-z]){marker}(?![a-z])", case=False, regex=True
        )
        shares = found.groupby(non_blank["label"], sort=True).mean()
        result[marker] = {label: round(float(share), 4) for label, share in shares.items()}
    return result


def build_report(df: pd.DataFrame, csv_path: Path, sha256: str) -> dict:
    """Build the inspection report. It contains no email text and no local file paths."""
    blank = is_blank(df["text"])
    labels = df["label"].value_counts().sort_index()
    return {
        "file": {
            "name": csv_path.name,
            "format": "CSV, UTF-8",
            "size_bytes": csv_path.stat().st_size,
            "sha256": sha256,
        },
        "environment": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
        },
        "structure": {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        },
        "labels": {
            label: {"rows": int(count), "share": round(count / len(df), 4)}
            for label, count in labels.items()
        },
        "missing_values": {column: int(count) for column, count in df.isna().sum().items()},
        "blank_text": {
            "empty_rows": df.loc[df["text"] == "", "label"].value_counts().sort_index().to_dict(),
            "whitespace_only_rows": int((blank & (df["text"] != "")).sum()),
        },
        "text_pandas_would_treat_as_missing_by_default": int(
            df["text"].isin(PANDAS_DEFAULT_NA_TEXT).sum()
        ),
        "duplicates": summarise_duplicates(df),
        "lengths": summarise_lengths(df),
        "marker_document_frequency": marker_document_frequency(df),
    }


def write_report(report: dict, path: Path) -> None:
    """Write sorted JSON with no timestamp, so identical input gives an identical file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")


def print_examples(df: pd.DataFrame, per_label: int = 2, max_chars: int = 90) -> None:
    """Print short previews to the terminal. These are never written to the report."""
    for label, group in df[~is_blank(df["text"])].groupby("label", sort=True):
        for text in group["text"].head(per_label):
            preview = " ".join(text.split())[:max_chars].encode("ascii", "replace").decode()
            print(f"[{label}] {preview}")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the raw spam/ham dataset.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the raw CSV.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Where to write the report.")
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA256, help="Hash the CSV must match.")
    parser.add_argument("--show-examples", action="store_true", help="Print short text previews.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the inspection. Return 0 on success, or 1 if the dataset fails a check."""
    args = parse_args(argv)
    try:
        sha256 = verify_hash(args.csv, args.expected_sha256)
        df = load_dataset(args.csv)
        validate_schema(df)
    except (FileNotFoundError, ValueError) as error:
        print(f"Dataset check failed: {error}", file=sys.stderr)
        return 1

    report = build_report(df, args.csv, sha256)
    write_report(report, args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.show_examples:
        print_examples(df)
    print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
