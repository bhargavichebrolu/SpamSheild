# Project explanation

This document explains SpamShield AI as one connected system. It grows with each milestone and describes only what exists now. Anything not built yet is listed under [Not built yet](#not-built-yet).

**Current state:** Milestone 1. The project can verify and describe its dataset, but it has no preprocessing, models, API or frontend.

## Problem and objective

The project investigates whether machine learning and natural language processing can distinguish spam from legitimate email using labelled examples, and how to present those predictions honestly in a web application. It is a learning and research prototype, and it does not provide guaranteed email security.

## Dataset and labels

The project uses a Kaggle CSV of 193,852 messages with two columns, `label` (`Ham` or `Spam`) and `text`. Its reported source is Kaggle and its licence is not verified, so the raw data is not committed or redistributed. The [dataset card](dataset-card.md) has the verified details and known limitations.

## End-to-end data flow

Only the first step exists so far:

```text
spam_Emails_data.csv (raw, not in Git)
        │
        ▼
training/inspect_dataset.py
  1. Check the file's SHA-256 hash
  2. Load the CSV as literal text
  3. Validate columns and label values
  4. Compute aggregate statistics
        │
        ▼
reports/dataset_inspection.json (in Git, no email text)
        │
        ▼
docs/dataset-card.md (a person writes this from the report)
```

## Why the inspection works this way

- **Hash check first:** results only mean something for a known file. If the file changes, the script stops instead of quietly reporting on different data.
- **Literal text:** by default Pandas turns text such as `null` or `NA` into missing values, which would be wrong for email. On this dataset the setting only affects the 2 empty rows, but it makes the behaviour explicit.
- **Strict decoding:** invalid UTF-8 causes an error instead of being silently altered.
- **Fingerprints for duplicates:** comparing short hashes finds duplicates without keeping a second copy of the text in memory. The script peaked at about 0.78 GB of memory.
- **Near-duplicates:** messages that differ only in letter case or spacing are treated as near-duplicates. If one copy landed in training and another in testing, the test would partly measure memory instead of generalisation.
- **No email text in the report:** the report is committed to Git, and the dataset's licence is not verified. Aggregates also make it safe to use later in the dataset explorer.
- **No timestamp in the report:** identical input produces a byte-identical file, so reproducibility is easy to check.

## Source-file map

| File | Responsibility | Used by |
|---|---|---|
| [`backend/training/inspect_dataset.py`](../backend/training/inspect_dataset.py) | Verify the dataset and write the report | People running the inspection; the tests |
| [`backend/tests/test_inspect_dataset.py`](../backend/tests/test_inspect_dataset.py) | Test the inspection logic on made-up data | `pytest` |
| [`backend/reports/dataset_inspection.json`](../backend/reports/dataset_inspection.json) | Generated dataset statistics | The dataset card, and later the dataset explorer |
| [`backend/requirements.txt`](../backend/requirements.txt) | Pinned Python dependencies | `pip` |
| [`backend/pytest.ini`](../backend/pytest.ini) | Lets tests import from `backend/` and tells `pytest` where they are | `pytest` |

Each source file also has a detailed log in [`file-explanations/`](file-explanations/).

## Structure decisions

- **`backend/training/` is separate from API code.** Inspection and training run before the application does, and the API only needs to make predictions.
- **`features.py` is added only if it has a distinct responsibility.** It would be redundant if feature extraction is already contained in the scikit-learn pipeline.

## Testing strategy so far

The 17 tests use small made-up CSVs, so they run quickly without the real dataset and contain no private email. They cover literal text loading, quoted newlines, invalid UTF-8, schema validation, hash checking, duplicate and conflict counts, length statistics, whole-word marker matching, report privacy and reproducibility.

Run them from the repository root:

```powershell
python -m pytest backend
```

## Limitations so far

- The dataset's licence, label accuracy and original sources have not been verified.
- Marker words suggest possible source leakage, but this has not been measured.
- The tests check the script's logic. The real dataset's results were checked by running the script twice and comparing them with an earlier independent count.

## Not built yet

| Topic | Planned milestone |
|---|---|
| Text preprocessing, feature extraction, data splitting and leakage safeguards | 2 |
| Candidate models, training, evaluation, source-leakage experiment and model persistence | 3 |
| Backend request flow, prediction and explanations | 4 |
| Frontend request flow and display | 5 |
| Alternative approaches, and final limitations | Updated in each milestone, finalised in 6 |
