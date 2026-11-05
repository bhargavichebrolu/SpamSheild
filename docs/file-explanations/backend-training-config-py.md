# `backend/training/config.py`

Source: [`config.py`](../../backend/training/config.py).

## 1. Why the file exists

Several scripts need the same seed, split shares and paths. One shared definition stops them disagreeing.

## 2. Responsibility and design intention

It only holds settings, with no logic, keeping configuration separate from implementation.

## 3. Inputs and outputs

It has no inputs or outputs. Other files import its constants.

## 4. Important functions and variables

| Name | Value and purpose |
|---|---|
| `BACKEND_DIR` | The `backend/` folder, worked out from this file's location |
| `REPORTS_DIR` | Where generated reports are written |
| `PROCESSED_DIR`, `SPLIT_ASSIGNMENTS` | Where the split file is written |
| `RANDOM_SEED` | `42`, used wherever randomness affects a result |
| `VALIDATION_SHARE`, `TEST_SHARE` | `0.10` each, leaving 80% for training |
| `FINAL_MODEL` | The chosen model, setting, features and word removal. It's set from validation results, and test results must never change it |

## 5. Key implementation decisions

- **Paths come from the file's location:** they work wherever the repository is, and no personal path is written down.
- **`42` has no special meaning:** what matters is that it's fixed and recorded. Trying other seeds and keeping the best result would be a form of cheating.

## 6. Dependencies

Only `pathlib` from the standard library.

## 7. How its output is used next

The training scripts import these values, and `train_final.py` builds the saved pipeline from `FINAL_MODEL`.

## 8. Tests

It contains no logic. Tests of `prepare_data.py` cover the split shares in practice, and `test_final_pipeline.py` checks that `FINAL_MODEL` names a known model, setting and removal.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| A YAML or JSON settings file | Needs extra loading code, and the settings are few |
| Environment variables | Nothing here varies between machines |
