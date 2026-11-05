# `backend/training/compare_models.py`

Source: [`compare_models.py`](../../backend/training/compare_models.py).

## 1. Why the file exists

The final model must be chosen from measured results, using a fair comparison.

## 2. Responsibility and design intention

It trains every candidate and setting on each feature set, scores them on validation rows, and applies the selection rule. Within a feature set, every classifier uses the same matrix, so only the classifier differs.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Training and validation splits. The test split is never requested. |
| **Output** | `backend/reports/model_comparison.json`: exact settings, metrics, ROC-AUC, timing, memory and the selected result |

Run it from `backend` with `python -m training.compare_models`. It took about 7 minutes.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `FEATURES_COMPARED` | `word_1` and `word_1_2` |
| `fit_classifier` | Fits a classifier, and records convergence and time |
| `message_latency_ms` | Times one-message-at-a-time prediction over 200 rows |
| `compare_for_features` | Runs all candidates on one feature set |
| `write_results` | Adds results to the report, and reapplies the rule |

## 5. Key implementation decisions

- **One process per feature set:** this keeps memory measurements separate.
- **The matrix is built once per feature set:** this is what makes 18 runs affordable.
- **Convergence is recorded:** warnings are captured, so a failed fit can't win unnoticed.
- **Latency includes everything:** preprocessing, TF-IDF and prediction.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`, `scikit-learn`.
- **Project files:** `config.py`, `evaluate.py`, `feature_experiments.py`, `features.py`, `inspect_dataset.py`, `models.py`, `prepare_data.py`.

## 7. How its output is used next

Its selected result sets the model for `source_leakage.py` and informs `FINAL_MODEL`.

## 8. Tests

Tests are in [`test_models.py`](../../backend/tests/test_models.py), including one confirming it requests only train and validation. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Cross-validation | Takes several times as long, and one validation split of 19,082 rows gives a stable comparison |
| Refitting TF-IDF for each classifier | Wasteful, and would add time without changing results |
| Comparing on the test split | Would make its final result meaningless |
