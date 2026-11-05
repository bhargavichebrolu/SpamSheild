# `backend/app/api/routes.py`

Source: [`routes.py`](../../backend/app/api/routes.py). `backend/app/api/__init__.py` is an empty file that lets Python import this folder as a package.

## 1. Why the file exists

It defines what the API offers: three endpoints for the model, and two read-only endpoints for saved results.

## 2. Responsibility and design intention

It connects requests to `app/ml`, and shapes the responses. It holds no model logic, so each part can be tested alone.

## 3. Inputs and outputs

| Endpoint | Input | Output |
|---|---|---|
| `GET /api/health` | None | Status, and whether the model is loaded |
| `POST /api/classify` | `{"text": "..."}` | Label, `confidence: null`, score, version, text length, recognised terms and explanation |
| `GET /api/model-info` | None | Model details, both hashes, measured results and limitations |
| `GET /api/results/models` | None | Saved model comparison, final evaluation and source-leakage results |
| `GET /api/results/dataset` | None | Verified aggregate statistics about the dataset |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `health` | Returns `200`, or `503` with the reason |
| `classify_email` | Classifies one message |
| `model_info` | Describes the model |
| `models_results`, `dataset_results` | Return saved results, which don't need the model loaded |
| `_loaded_model` | Returns the model, or raises `ModelUnavailable` |
| `ClassificationFailed` | Replaces an unexpected error, and carries no details |

## 5. Key implementation decisions

- **Plain functions, not `async`:** FastAPI runs them in a worker thread, so model calculations can't hold up other requests.
- **Unexpected errors are replaced:** an error's message could include the email text, so only its type is logged, and the response is generic.
- **`from None` drops the original error:** so it can't appear in a traceback.
- **The text isn't stored or returned:** only its length is.

## 6. Dependencies

- **Packages:** `fastapi`.
- **Project files:** `app/ml/model_info.py`, `app/ml/predict.py`, `app/ml/results.py`, `app/schemas/prediction.py`, `app/schemas/results.py`.

## 7. How its output is used next

`main.py` includes this router, and the website calls these endpoints through `frontend/src/services/api.ts`.

## 8. Tests

Tests are in [`test_api.py`](../../backend/tests/test_api.py) and [`test_results_api.py`](../../backend/tests/test_results_api.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Putting model logic here | Harder to test, and it would mix concerns |
| `async` endpoints | Model calculations would block the server's event loop |
| Returning `200` with an error field | Status codes let clients detect failures in the standard way |
