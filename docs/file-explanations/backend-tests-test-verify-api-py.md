# `backend/tests/test_verify_api.py`

Source: [`test_verify_api.py`](../../backend/tests/test_verify_api.py).

## 1. Why the file exists

The comparison tool is only useful if it would actually catch a mismatch, and the API should also be checked against the real model when it's available.

## 2. Responsibility and design intention

It tests the tool with deliberate faults, and runs a few checks with the real model.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Made-up messages, the tiny model, and the real saved model if present |
| **Output** | Pass or fail results from `pytest`. Real-model tests are skipped if the file is missing |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_comparison_detects_a_wrong_label` | An injected wrong label is caught |
| `test_comparison_detects_a_wrong_score` | An injected wrong score is caught |
| `test_comparison_counts_server_failures` | `500` responses count as failures |
| `test_comparison_counts_an_oversized_body_as_a_refusal_not_a_failure` | A `413` counts as a refusal |
| `test_the_tool_only_loads_validation_data` | Only validation is requested, and the report has no text |
| `test_real_model_loads_and_matches_its_recorded_identity` | The real model's hashes match its metadata |
| `test_real_model_through_the_api_matches_direct_inference` | Labels and scores match for sample messages |
| `test_real_model_info_reports_the_saved_results` | `/api/model-info` matches the test report |

## 5. Key implementation decisions

- **Faults are injected on purpose:** a check that never fails looks the same as one that works.
- **Real-model tests can be skipped:** the model isn't in Git, so a fresh copy of the repository still passes.

## 6. Dependencies

`pytest`, `pandas`, `fastapi`, `app`, and `training.verify_api`.

## 7. How its output is used next

Passing tests are part of Milestone 4's acceptance check.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 290 tests passed, including the real-model tests.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Running the full comparison in the test suite | It takes about a minute and needs the dataset, so it's a separate command |
