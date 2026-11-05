# `backend/training/analyse_format.py`

Source: [`analyse_format.py`](../../backend/training/analyse_format.py).

## 1. Why the file exists

Preprocessing decisions depend on what the text actually looks like. This script measures that rather than guessing from a few samples.

## 2. Responsibility and design intention

It describes the format of the raw text: casing, digits, placeholders, URLs and token lengths. It runs before the split, so it may include rows that later become test data. It's deliberately limited to format: it evaluates no model and doesn't choose words as features.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The raw CSV, after a hash check |
| **Output** | `backend/reports/format_analysis.json`, with aggregate counts only |

Run it from `backend/` with `python -m training.analyse_format`.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `FORMAT_PATTERNS` | The regular expressions to measure |
| `format_flags` | Returns a True or False column for each pattern |
| `number_style` | Classifies each row as digits, placeholder, both or neither |
| `longest_token_length` | Finds the longest run of letters and digits in a message |
| `describe` | Summarises values, reporting `None` for an empty group |
| `build_report` | Combines the results, by label and by number style |

## 5. Key implementation decisions

- **Number style is a key measure:** no row mixes digits and placeholders, which is evidence of separately processed sources.
- **Spaced punctuation is reported by number style:** it appears in 89.3% of digit rows and 0.0% of placeholder rows, supporting the same conclusion.
- **Token length is compared with and without `escapelong`:** this tested whether a clear length rule explains the placeholder. Rows containing it still have tokens up to 77 characters long, so no clear rule emerged.

## 6. Dependencies

- **Packages:** `pandas`, plus `re` from the standard library.
- **Project files:** `config.py`, and helpers from `inspect_dataset.py`.

## 7. How its output is used next

Its findings led to the steps in `preprocess.py`, and to the "Text format" section of the [dataset card](../dataset-card.md).

## 8. Tests

Tests are in [`test_features.py`](../../backend/tests/test_features.py). Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Reading sample messages by eye | Can't show that a pattern never occurs, such as digits alongside placeholders |
| Running only on training data | Would need the split first, but the split depends on preprocessing, which depends on this analysis. Limiting this script to format avoids that loop. |
