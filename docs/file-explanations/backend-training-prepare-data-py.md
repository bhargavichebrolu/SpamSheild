# `backend/training/prepare_data.py`

Source: [`prepare_data.py`](../../backend/training/prepare_data.py).

## 1. Why the file exists

Models need clean, separate data for training, validation and testing. How that's done decides whether evaluation can be trusted, so it needs to be explicit and repeatable.

## 2. Responsibility and design intention

It decides which rows are kept and which split each belongs to, and it guards the test set. It never changes the raw file or copies text.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | `backend/data/raw/spam_Emails_data.csv`, after a hash check |
| **Output** | `backend/data/processed/split_assignments.csv`: raw row numbers and split names (not in Git) |
| **Output** | `backend/reports/data_preparation.json`: counts, seed and the split file's hash |

Run it from `backend/` with `python -m training.prepare_data`.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `profile_text` | Returns a fingerprint of the preprocessed text, and whether it has a word token |
| `clean_rows` | Applies the four cleaning rules and counts what each removes |
| `assign_splits` | Makes the seeded, stratified 80/10/10 split |
| `count_shared_texts`, `verify_no_overlap` | Check that no preprocessed text is in two splits, and stop the run if one is |
| `save_assignments` | Writes the split file with fixed line endings, so its hash is stable |
| `load_split` | Returns one split's rows, and refuses the test split unless `allow_test=True` |
| `build_report` | Summarises the results with counts only |

## 5. Key implementation decisions

- **Rows are compared after preprocessing:** this catches 2,974 repeats, compared with 1,733 when comparing only case and spacing.
- **All copies of conflicting text are removed:** neither label can be trusted, and keeping one would be an arbitrary choice.
- **Rows with no word token are removed:** the 39 rows would produce empty word features.
- **Row numbers, not text, are stored:** this avoids a second copy of the data, and the file is only about 2.4 MB.
- **Split in two steps:** first 80% against 20%, then that 20% in half. Both steps stratify by label, so each split has the same 47.3% spam share.
- **The guard is an error, not a convention:** forgetting the rule can't quietly read the test split.

## 6. Dependencies

- **Packages:** `pandas`, `scikit-learn` (`train_test_split`).
- **Project files:** `preprocess.py`, `config.py`, and helpers from `inspect_dataset.py`.

## 7. How its output is used next

`load_split` provides rows to `analyse_vocabulary.py` and `feature_experiments.py`, and later to Milestone 3's training. Only the final evaluation should use `allow_test=True`.

## 8. Tests

Tests are in [`test_prepare_data.py`](../../backend/tests/test_prepare_data.py). Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Comparing on raw text | Rows that look identical to the model could land in separate splits |
| Saving a cleaned copy of each split | Duplicates about 350 MB of text, with no benefit |
| Keeping the first copy of conflicting text | Arbitrary, since neither label is more trustworthy |
| A group-aware split that keeps similar messages together | Needs clustering across about 190,000 rows; template effects are reported by similarity band instead |
