# `backend/training/inspect_dataset.py`

Source: [`inspect_dataset.py`](../../backend/training/inspect_dataset.py). `backend/training/__init__.py` is an empty file that lets Python import `training` as a package.

## 1. Why the file exists

The PRD requires dataset facts to be verified rather than assumed, and the checks to be reproducible. This script is the single, repeatable way to do that.

## 2. Responsibility and design intention

It answers one question: is this the expected file, and what does it contain? It reads the data and never changes it. It doesn't clean or split anything, because those are Milestone 2 decisions.

Most functions take data and return results, with file writing and printing kept apart. This lets the tests check the logic on small made-up data.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | `backend/data/raw/spam_Emails_data.csv`, or a path given with `--csv` |
| **Output file** | `backend/reports/dataset_inspection.json`, or a path given with `--report` |
| **Terminal output** | The report, plus short previews with `--show-examples` |
| **Exit code** | `0` on success; `1` if the file is missing, its hash differs, or it can't be read or validated. No report is written on failure. |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `EXPECTED_SHA256`, `EXPECTED_COLUMNS`, `EXPECTED_LABELS` | The verified facts about the dataset |
| `MARKER_WORDS` | Words to measure because they may reveal a message's source or processing |
| `verify_hash` | Stops the run if the file differs from the verified one |
| `load_dataset` | Reads the CSV as literal, strictly decoded text |
| `validate_schema` | Rejects unexpected columns or labels |
| `fingerprint` | Returns a short hash of a text, for memory-efficient comparison |
| `summarise_duplicates`, `count_conflicts` | Count exact and near-duplicates, and texts with both labels |
| `summarise_lengths`, `describe_lengths` | Give length statistics per label |
| `marker_document_frequency` | Gives the share of each label's rows containing each marker word |
| `build_report` | Combines the results into one dictionary |
| `write_report` | Writes sorted JSON with no timestamp |
| `main` | Runs the steps and turns dataset errors into a clear message and exit code `1` |

## 5. Key implementation decisions

- **`keep_default_na=False`:** otherwise Pandas converts text such as `null` into missing values. In this dataset that only affects the 2 empty rows, but other text would be altered silently if the data changed.
- **Strict UTF-8:** invalid bytes raise an error rather than being replaced.
- **Percentiles with `interpolation="lower"`:** each result is a real message length, not a value between two lengths.
- **Markers matched by letter boundaries:** `enron1` counts as `enron`, but `enronic` doesn't. This isn't the same as regex `\b`, which wouldn't match `enron1`.
- **Hash check before loading:** a wrong file fails quickly, without using memory on a full load.

## 6. Dependencies

- **Packages:** `pandas`, plus `argparse`, `hashlib`, `json`, `pathlib` and `sys` from the standard library.
- **Project files:** it imports nothing from the project, and `backend/tests/test_inspect_dataset.py` imports it.

## 7. How its output is used next

- [`docs/dataset-card.md`](../dataset-card.md) records the verified facts by hand from the report.
- Milestone 2 will use the duplicate, conflict and length findings to set its cleaning rules.
- Milestone 5's dataset explorer can read the report directly.

## 8. Tests

Tests are in [`backend/tests/test_inspect_dataset.py`](../../backend/tests/test_inspect_dataset.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| A notebook | Harder to rerun and test, and the PRD makes scripts the core format |
| Reading in chunks | More complex, and the measured peak of about 0.78 GB didn't require it |
| Comparing full normalised text | Would keep a second copy of the text in memory |
| Saving example records in the report | The report is committed, and the licence is not verified |
