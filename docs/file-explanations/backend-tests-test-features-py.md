# `backend/tests/test_features.py`

Source: [`test_features.py`](../../backend/tests/test_features.py).

## 1. Why the file exists

Feature extraction is where training data can most easily leak into evaluation, and it's what a saved model will rely on at prediction time. These tests also cover the analysis and experiment helpers.

## 2. Responsibility and design intention

It tests the behaviour that later milestones depend on, using small made-up texts and tiny matrices with known answers.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | `TRAIN_TEXTS`, plus other small made-up text and matrices |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_vocabulary_is_learned_only_from_fitted_text` | Unseen words aren't added |
| `test_transform_does_not_change_the_fitted_vocabulary` | Scoring new text can't alter what was learned |
| `test_vectorizer_applies_project_preprocessing_at_inference` | Raw text goes through preprocessing automatically |
| `test_fitted_vectorizer_keeps_working_after_save_and_reload` | Saving doesn't change results |
| `test_score_treats_spam_as_the_positive_class` | Metrics and error types are correct, against a hand-worked example |
| `test_experiments_never_load_the_test_split` | Experiments only request train and validation |
| `test_score_by_similarity_band_puts_each_row_in_exactly_one_band` | No row is counted twice or lost |
| `test_format_report_handles_a_group_with_no_rows` | Records a bug the first run found |

## 5. Key implementation decisions

- **Settings are loosened in some tests:** `min_df` and `max_df` are made less strict, because a handful of sentences can't meet the real thresholds. The tests that need this check how the vectoriser behaves, not those thresholds.
- **`monkeypatch` replaces `load_split`:** a stand-in records which splits are requested, proving the behaviour without needing real data.
- **Save and reload uses `pickle` here:** the saved model uses `joblib`, which builds on the same mechanism, and is tested separately.

## 6. Dependencies

`pytest`, `numpy`, `pandas`, `scipy`, and the project's `preprocess`, `features`, `analyse_format`, `analyse_vocabulary` and `feature_experiments` modules.

## 7. How its output is used next

Passing tests are part of Milestone 2's acceptance check. Saving and reloading a full pipeline is tested in [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py).

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 79 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Separate test files for each helper module | Most helpers have only a few tests, so this would add files without making them clearer |
| Asserting a target F1 score | Scores depend on data, and don't show that the logic is correct |
