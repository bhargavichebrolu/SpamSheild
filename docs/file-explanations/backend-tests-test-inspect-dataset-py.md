# `backend/tests/test_inspect_dataset.py`

Source: [`test_inspect_dataset.py`](../../backend/tests/test_inspect_dataset.py). [`backend/pytest.ini`](../../backend/pytest.ini) lets the tests import from `backend/` and tells `pytest` where to find them.

## 1. Why the file exists

The inspection report is only useful if its calculations are right. These tests catch mistakes in the logic, including if it's changed later.

## 2. Responsibility and design intention

It tests the behaviour of `inspect_dataset.py` on a tiny made-up CSV with known answers. Each awkward case, such as a repeated `hi` under both labels, is included on purpose.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The `SAMPLE_CSV` text and small in-memory tables defined in the test file |
| **Output** | Pass or fail results from `pytest`. Temporary files are created in a folder `pytest` manages. |

The real dataset isn't needed.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `SAMPLE_CSV` | 13 made-up rows covering duplicates, conflicts, blanks, `null`-like text and quoted newlines |
| `csv_path`, `df` | Fixtures: reusable test setup that provides the sample as a file and as a table |
| `report_for` | Builds a full report from a sample file |

## 5. Key implementation decisions

- **Made-up text:** no private email, and no copying of a dataset whose licence is not verified.
- **Exact expected values:** each one was worked out by hand from the sample, so the tests don't just repeat what the code returns.
- **Failure behaviour is tested:** the tests check that a wrong hash or missing file returns exit code `1` and writes no report.

## 6. Dependencies

`pytest`, `pandas`, and `training.inspect_dataset`.

## 7. How its output is used next

A passing run is part of Milestone 1's acceptance check. Later milestones will add their own test files alongside this one.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: 17 passed.

| Area | What is checked |
|---|---|
| Loading | Literal `null` and `NA`, quoted newlines and commas, invalid UTF-8 |
| Validation | Correct structure is accepted; wrong column names, wrong column order and unexpected labels are rejected |
| Hashing | Matching and mismatching hashes |
| Statistics | Blank counts, `null`-like text, duplicates, conflicts, lengths, marker matching |
| Report | No email text or local paths, and identical input gives an identical file |
| Command line | Failure paths, and truncated previews |

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing against the real CSV | Slow, needs a file that isn't in Git, and its correct answers aren't independently known |
| Storing a fixture file | An inline sample keeps the data and expected values together in one file |
