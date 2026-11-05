# `backend/app/ml/results.py`

Source: [`results.py`](../../backend/app/ml/results.py).

## 1. Why the file exists

The website needs saved results, and they should come from one controlled place.

## 2. Responsibility and design intention

It reads committed reports and arranges them for the website. It only reads, and doesn't need the model loaded.

## 3. Inputs and outputs

Input: reports in `backend/reports/`, and the model metadata. Output: dictionaries for the results endpoints, or `ResultsUnavailable`.

## 4. Important functions and variables

`build_models_results`, `build_dataset_results`, `ResultsUnavailable`.

## 5. Key implementation decisions

**The word lists and vocabulary report are never read,** because their words can include surnames. A missing or malformed report gives a clear failure rather than partial results. The licence is stated here as "Not verified". `report_matches_saved_model` shows if the test report describes a different file.

## 6. Dependencies

`app/config.py`, `app/ml/model_info.py`, `app/ml/predict.py`.

## 7. How its output is used next

`routes.py` returns its results.

## 8. Tests

[`test_results_api.py`](../../backend/tests/test_results_api.py). From the repository root, run `python -m pytest backend`.

## 9. Alternatives considered

Serving report files directly was rejected: this way, each response passes through an allowlist.
