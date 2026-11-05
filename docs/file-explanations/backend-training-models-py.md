# `backend/training/models.py`

Source: [`models.py`](../../backend/training/models.py).

## 1. Why the file exists

It holds the candidate models and the rule for choosing between them, in one place that was written before any comparison ran.

## 2. Responsibility and design intention

It defines what's compared, and how the winner is chosen. It doesn't load data or run anything.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | A model name and setting, or a list of validation results |
| **Output** | An unfitted classifier, or the selected result |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `PARAMETER_GRID` | Three values of each model's main setting |
| `F1_TIE_MARGIN` | `0.002`: smaller F1 gaps count as ties |
| `SIMPLICITY_ORDER` | Naive Bayes, then Logistic Regression, then Linear SVM, for breaking final ties |
| `build_classifier` | Returns an unfitted classifier |
| `select_best` | Applies the selection rule |

## 5. Key implementation decisions

- **The rule came first:** this stops it being adjusted to suit a particular result.
- **Ties favour fewer false alarms:** flagging a legitimate email is the costlier mistake for a spam filter.
- **The margin reflects noise:** with 19,082 validation rows, F1 gaps below about 0.002 are about the size of random variation. It's a judgement call rather than a calculated threshold.
- **A run that didn't converge can't win:** its weights may not be reliable. In practice, all 18 runs converged.
- **Only three values:** the project owner asked to avoid broad searches. The best Logistic Regression and SVM values were at the top of the range, so higher ones weren't explored.

## 6. Dependencies

- **Packages:** `scikit-learn`.
- **Project files:** `config.py`.

## 7. How its output is used next

`compare_models.py` uses it to run and choose candidates, and `source_leakage.py` and `train_final.py` use `build_classifier`.

## 8. Tests

Tests are in [`test_models.py`](../../backend/tests/test_models.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Choosing the highest F1 outright | Would treat random variation as a real difference, and ignore the cost of false alarms |
| A broad grid search | Costly, and the project owner asked to avoid it |
| Choosing by hand after seeing results | Open to bias |
