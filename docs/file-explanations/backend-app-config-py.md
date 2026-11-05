# `backend/app/config.py`

Source: [`config.py`](../../backend/app/config.py).

## 1. Why the file exists

The API's limits are used in several places, and defining them once stops them disagreeing.

## 2. Responsibility and design intention

It only holds settings, with no logic. It's separate from `training/config.py`, so the API doesn't depend on training code.

## 3. Inputs and outputs

It has no inputs or outputs. Other files import its constants.

## 4. Important functions and variables

| Name | Value and purpose |
|---|---|
| `MAX_INPUT_CHARS` | 20,000, taken from preprocessing's own limit |
| `MAX_BODY_BYTES` | 256 KB, enough for 20,000 characters in the most verbose JSON escaping |
| `MAX_DISCARD_BYTES` | 16 MB, how much of a rejected upload to read |
| `TOP_TERMS` | 10, how many terms to list for each label |
| `ALLOWED_ORIGINS` | The website's local addresses, on port 5173 |
| `BACKEND_DIR`, `REPORTS_DIR` | Worked out from this file's location |

## 5. Key implementation decisions

- **The limit comes from preprocessing:** the API's limit and the model's reading limit can't drift apart.
- **The body limit was checked by a test:** the largest valid text, fully escaped, fits within it.
- **Origins are listed exactly:** other websites can't call the API from a visitor's browser.

## 6. Dependencies

- **Packages:** only the standard library.
- **Project files:** `app/ml/preprocess.py`.

## 7. How its output is used next

`main.py`, `predict.py`, `model_info.py` and `schemas/prediction.py` import it.

## 8. Tests

It contains no logic. [`test_api.py`](../../backend/tests/test_api.py) checks each limit's behaviour. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Environment variables | Nothing here varies between machines yet |
| Sharing `training/config.py` | The API must not depend on training code |
