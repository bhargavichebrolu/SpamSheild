"""Clean the dataset and assign each row to the train, validation or test split.

The raw CSV is never changed, and no text is copied. The output is a small file that
maps raw row numbers to splits, so the splits can be rebuilt from the raw data.

Run from the backend folder:
    python -m training.prepare_data
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from app.ml.preprocess import preprocess_text
from training.config import (
    RANDOM_SEED,
    REPORTS_DIR,
    SPLIT_ASSIGNMENTS,
    TEST_SHARE,
    VALIDATION_SHARE,
)
from training.inspect_dataset import (
    DEFAULT_CSV,
    EXPECTED_SHA256,
    fingerprint,
    is_blank,
    load_dataset,
    sha256_file,
    validate_schema,
    verify_hash,
    write_report,
)

DEFAULT_REPORT = REPORTS_DIR / "data_preparation.json"

# The default TF-IDF word tokeniser keeps tokens of two or more word characters.
_WORD_TOKEN = re.compile(r"\w\w")


def profile_text(text: str) -> tuple[str, bool]:
    """Return a fingerprint of the preprocessed text, and whether it has any word token."""
    processed = preprocess_text(text)
    return fingerprint(processed), bool(_WORD_TOKEN.search(processed))


def clean_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the cleaning rules and return the kept rows and a count for each rule.

    Rows are compared after preprocessing, because two rows that look identical to the
    model must not land in different splits. The returned frame's index holds the raw
    row positions, and it has a "fingerprint" column instead of a preprocessed copy.
    """
    blank = is_blank(df["text"])
    profiles = [profile_text(text) for text in df["text"]]
    frame = pd.DataFrame(
        {"label": df["label"], "fingerprint": [fingerprint_ for fingerprint_, _ in profiles]},
        index=df.index,
    )
    has_token = pd.Series([has_token_ for _, has_token_ in profiles], index=df.index)

    no_tokens = ~blank & ~has_token
    usable = frame[~blank & ~no_tokens]

    labels_per_text = usable["label"].groupby(usable["fingerprint"], sort=False).transform("nunique")
    conflicting = labels_per_text > 1
    consistent = usable[~conflicting]

    duplicate = consistent["fingerprint"].duplicated(keep="first")
    kept = consistent[~duplicate]

    counts = {
        "rows_in": int(len(df)),
        "removed_blank": int(blank.sum()),
        "removed_no_word_tokens": int(no_tokens.sum()),
        "removed_conflicting_labels": int(conflicting.sum()),
        "conflicting_label_texts": int(usable.loc[conflicting, "fingerprint"].nunique()),
        "removed_duplicates": int(duplicate.sum()),
        "rows_kept": int(len(kept)),
    }
    return kept, counts


def assign_splits(
    labels: pd.Series,
    seed: int = RANDOM_SEED,
    validation_share: float = VALIDATION_SHARE,
    test_share: float = TEST_SHARE,
) -> pd.Series:
    """Return a stratified, seeded split name for each row, sorted by row position."""
    train_index, holdout_index = train_test_split(
        labels.index.to_numpy(),
        test_size=validation_share + test_share,
        stratify=labels,
        random_state=seed,
    )
    validation_index, test_index = train_test_split(
        holdout_index,
        test_size=test_share / (validation_share + test_share),
        stratify=labels.loc[holdout_index],
        random_state=seed,
    )
    splits = pd.Series(index=labels.index, dtype="str", name="split")
    splits.loc[train_index] = "train"
    splits.loc[validation_index] = "validation"
    splits.loc[test_index] = "test"
    return splits.sort_index()


def count_shared_texts(fingerprints: pd.Series, splits: pd.Series) -> int:
    """Return how many preprocessed texts appear in more than one split."""
    splits_per_text = splits.groupby(fingerprints, sort=False).nunique()
    return int((splits_per_text > 1).sum())


def verify_no_overlap(fingerprints: pd.Series, splits: pd.Series) -> int:
    """Raise ValueError if any preprocessed text is in two splits. Otherwise return the count, 0."""
    shared = count_shared_texts(fingerprints, splits)
    if shared:
        raise ValueError(f"{shared} preprocessed texts appear in more than one split")
    return shared


def save_assignments(splits: pd.Series, path: Path) -> None:
    """Save raw row positions and split names, with fixed line endings for a stable hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = splits.rename_axis("row_index").reset_index()
    table.to_csv(path, index=False, lineterminator="\n")


def load_split(
    split: str,
    *,
    allow_test: bool = False,
    csv_path: Path = DEFAULT_CSV,
    assignments_path: Path = SPLIT_ASSIGNMENTS,
) -> pd.DataFrame:
    """Return one split's raw label and text columns.

    Loading the test split requires allow_test=True, so that analysis and experiment
    code can't read it by accident. Only the final evaluation should pass that flag.
    """
    if split == "test" and not allow_test:
        raise PermissionError("The test split is reserved for final evaluation")
    assignments = pd.read_csv(assignments_path)
    positions = assignments.loc[assignments["split"] == split, "row_index"].to_numpy()
    if positions.size == 0:
        raise ValueError(f"No rows found for split {split!r}")
    return load_dataset(csv_path).iloc[positions].reset_index(drop=True)


def build_report(
    counts: dict[str, int],
    kept: pd.DataFrame,
    splits: pd.Series,
    sha256: str,
    shared_texts: int,
) -> dict:
    """Summarise the cleaning and split. It contains aggregates only, with no email text."""
    table = pd.crosstab(splits, kept["label"])
    return {
        "source_sha256": sha256,
        "cleaning": counts,
        "split": {
            "random_seed": RANDOM_SEED,
            "validation_share": VALIDATION_SHARE,
            "test_share": TEST_SHARE,
            "stratified_by": "label",
            "assignments_sha256": sha256_file(SPLIT_ASSIGNMENTS),
            "rows": {
                split: {
                    "total": int(table.loc[split].sum()),
                    **{label: int(table.loc[split, label]) for label in table.columns},
                    "spam_share": round(float(table.loc[split, "Spam"] / table.loc[split].sum()), 4),
                }
                for split in table.index
            },
        },
        "leakage_checks": {
            "preprocessed_texts_shared_between_splits": shared_texts,
        },
    }


def main() -> int:
    sha256 = verify_hash(DEFAULT_CSV, EXPECTED_SHA256)
    df = load_dataset(DEFAULT_CSV)
    validate_schema(df)

    kept, counts = clean_rows(df)
    splits = assign_splits(kept["label"])
    shared_texts = verify_no_overlap(kept["fingerprint"], splits)
    save_assignments(splits, SPLIT_ASSIGNMENTS)

    report = build_report(counts, kept, splits, sha256, shared_texts)
    write_report(report, DEFAULT_REPORT)
    print(DEFAULT_REPORT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
