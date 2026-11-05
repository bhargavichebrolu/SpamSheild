# `backend/tests/test_final_pipeline.py`

Source: [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py).

## 1. Why the file exists

The saved pipeline is what the API will rely on, and the test-set safeguards protect the final result. Both need to be shown to work, including when they should refuse.

## 2. Responsibility and design intention

It tests saving, loading, freezing, the one-run guard, and the source-leakage logic, using a tiny pipeline fitted on six made-up messages.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Made-up messages, and temporary files in a folder `pytest` manages |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_saved_pipeline_loads_without_any_training_code` | In a fresh process, loading and predicting imports no `training` modules |
| `test_saved_pipeline_gives_the_same_predictions_after_reloading` | Saving doesn't change results |
| `test_verify_frozen_refuses_a_changed_pipeline` | A modified model file is refused |
| `test_verify_frozen_refuses_a_changed_split` | A modified split file is refused |
| `test_test_split_can_only_be_evaluated_once` | A second test run is refused |
| `test_main_refuses_a_repeat_test_run_before_loading_any_rows` | The refusal comes before any data is read |
| `test_report_has_counts_for_each_band_and_no_email_text` | Sample counts are present, and no text leaks |
| `test_removal_rule_needs_a_small_cost_and_improvement_both_ways` | Each condition in the removal rule matters |
| `test_two_fits_learn_identical_values` | Fitting is repeatable |
| `test_fingerprint_does_not_depend_on_file_bytes` | Differently written files of one model share a fingerprint |
| `test_fingerprint_is_the_same_across_processes_with_different_hash_seeds` | Hash randomisation doesn't affect it |
| `test_fingerprint_detects_a_change` | Changed weights, intercept, vocabulary, removed words or settings all change it |
| `test_fingerprint_detects_changed_preprocessing_behaviour_under_the_same_name` | A changed preprocessor is caught, even with the same name |
| `test_record_fingerprint_changes_only_the_metadata` | The saved model file isn't touched |
| `test_record_fingerprint_refuses_a_file_that_does_not_match` | A fingerprint can't be attached to the wrong file |

## 5. Key implementation decisions

- **A separate process for the import test:** the test run itself has already imported `training`, so only a fresh process can show loading doesn't need it.
- **Safeguards are tested for failure:** files are deliberately altered, to show the refusal really triggers.

## 6. Dependencies

`pytest`, `pandas`, and the project's `predict`, `final_evaluation`, `source_leakage` and `train_final` modules.

## 7. How its output is used next

Passing tests are part of Milestone 3's acceptance check, and they protect the loading path the API will use.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 290 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing against the real saved model | It isn't in Git, so tests would fail on a fresh copy. The real file was checked separately, as the development log records. |
| Only checking success paths | Wouldn't show that the safeguards trigger |
