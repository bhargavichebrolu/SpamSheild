# `backend/tests/test_prepare_data.py`

Source: [`test_prepare_data.py`](../../backend/tests/test_prepare_data.py).

## 1. Why the file exists

A mistake in cleaning or splitting could make every later result misleading, without any visible error. These tests check the leakage safeguards work.

## 2. Responsibility and design intention

It tests the cleaning rules, the split, overlap detection and the test-set guard, using small tables with known answers.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Small made-up tables, and temporary CSV files in a folder `pytest` manages |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `make_frame`, `balanced_labels` | Build small test data |
| `split_files` | A fixture that creates a small raw CSV and split file |
| `test_clean_keeps_first_copy_of_rows_identical_after_preprocessing` | Texts differing only in numbers or spacing count as repeats |
| `test_clean_removes_every_copy_of_text_with_conflicting_labels` | All copies go, not just the later ones |
| `test_clean_counts_add_up` | Every row is either kept or counted under one rule |
| `test_assign_splits_uses_expected_shares_and_keeps_label_balance` | The 80/10/10 shares and label balance hold |
| `test_verify_no_overlap_rejects_text_in_two_splits` | The safeguard really does stop the run |
| `test_load_split_refuses_the_test_split_by_default` | The guard raises an error |

## 5. Key implementation decisions

- **Safeguards are tested for failure:** a check that never fires looks the same as one that works, so tests give it bad input on purpose.
- **Different seeds are tested too:** this confirms the seed really controls the split.

## 6. Dependencies

`pytest`, `pandas`, and `training.prepare_data`.

## 7. How its output is used next

Passing tests are part of Milestone 2's acceptance check, and support the trust placed in Milestone 3's evaluation.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 79 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Checking only the real dataset's results | The right answers aren't independently known, so errors could go unnoticed |
| Testing only success paths | Wouldn't show that the safeguards trigger |
