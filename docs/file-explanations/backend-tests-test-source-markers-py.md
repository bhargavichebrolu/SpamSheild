# `backend/tests/test_source_markers.py`

Source: [`test_source_markers.py`](../../backend/tests/test_source_markers.py).

## 1. Why the file exists

The word lists must come from training data only, and must be repeatable, or the leakage experiment can't be trusted.

## 2. Responsibility and design intention

It tests the list-building logic on made-up rows with a known answer: `acmecorp` and `listserv` mark number styles, and `pills` marks spam.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Made-up rows from `training_rows`, and a temporary output file |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_styles_use_the_raw_text` | Number style comes from raw text |
| `test_rank_words_breaks_ties_alphabetically` | Results are repeatable |
| `test_derive_finds_style_and_label_words` | Each list finds the expected words |
| `test_derive_ignores_rare_words` | Words below the minimum are skipped |
| `test_list_hash_changes_with_the_list_and_hides_the_words` | Hashes identify lists without revealing words |
| `test_main_uses_training_data_only` | Only the training split is requested |

## 5. Key implementation decisions

- **Invented words:** so no real names or email text enter the repository.
- **A stand-in for `load_split`:** it records which splits are requested, proving the behaviour without real data.

## 6. Dependencies

`pytest`, `numpy`, `pandas`, and `training.source_markers`.

## 7. How its output is used next

Passing tests are part of Milestone 3's acceptance check.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 162 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Checking the real list's contents | The list isn't in Git, and its correct contents aren't independently known |
