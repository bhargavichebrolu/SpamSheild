# `backend/app/ml/model_info.py`

Source: [`model_info.py`](../../backend/app/ml/model_info.py).

## 1. Why the file exists

Anyone using the API should be able to see what model they're using, how it measured, and what its limits are. The website will also need this.

## 2. Responsibility and design intention

It combines the model's metadata with the saved evaluation reports. Results are read from generated files, not written by hand, so they can't drift from what was measured.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | A `LoadedModel`, and the reports folder |
| **Output** | A dictionary with model details, both hashes, test results, cross-style results and limitations |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `SCORE_MEANING` | Explains the score, and that it isn't a probability |
| `LIMITATIONS` | The main limits on what the model can be used for |
| `_read_report` | Reads a report, returning `None` if it's missing or unreadable |
| `_test_results` | Selects the test figures, including the no-close-match group |
| `_cross_style_results` | Selects the cross-style figures and their interpretation note |
| `build_model_info` | Puts it all together |

## 5. Key implementation decisions

- **Removed words are never included:** only their count, because they can include surnames.
- **`report_matches_loaded_file`:** shows whether the test results describe the loaded file, which becomes false after a retrain, because the file's hash changes.
- **A missing report gives `None`:** the API still works, and doesn't invent a value.
- **The cross-style interpretation note is included:** so these figures aren't read as proof of generalisation.

## 6. Dependencies

- **Packages:** only the standard library.
- **Project files:** `app/config.py`, `app/ml/predict.py`.
- **Generated files:** `backend/reports/final_test_evaluation.json` and `source_leakage.json`.

## 7. How its output is used next

`routes.py` returns it from `/api/model-info`. The website can use it in Milestone 5.

## 8. Tests

Tests are in [`test_api.py`](../../backend/tests/test_api.py) and [`test_verify_api.py`](../../backend/tests/test_verify_api.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Writing results into the code | They could go out of date, and the PRD requires results from real outputs |
| Reading reports inside the endpoint | Would mix file handling with request handling |
| Importing from `training` | The API must not depend on training code |
