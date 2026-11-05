# `backend/app/main.py`

Source: [`main.py`](../../backend/app/main.py).

## 1. Why the file exists

It's the API's entry point: Uvicorn runs the `app` object it creates.

## 2. Responsibility and design intention

It connects the pieces: startup, middleware and error responses. The endpoints themselves are in `routes.py`, and model logic is in `app/ml`.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | HTTP requests, and a function that loads the model |
| **Output** | HTTP responses, including every error response |

Run from `backend`:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `create_app` | Builds the application. Tests pass a different loader, to use a small model |
| `lifespan` | Loads the model once at startup, and records any failure |
| `BodySizeLimitMiddleware` | Rejects bodies over 256 KB, before they're parsed |
| `_VALIDATION_ERRORS` | Maps Pydantic's error types to this API's codes and fixed messages |
| `_error_response` | Gives every error the same shape |
| `app` | The application object Uvicorn runs |

## 5. Key implementation decisions

- **The API starts without a model:** `/api/health` can then explain the problem, rather than the server failing to start.
- **Validation errors are rewritten:** FastAPI's defaults repeat the rejected input, which could be someone's email. A test confirms the text never appears.
- **Body size is counted as it arrives:** so a request can't avoid the limit by understating its `Content-Length`.
- **A rejected upload is read before replying:** replying early resets the connection, so the client sees a network failure instead of the error. Real-server testing found this, and the test client can't show it. Reading stops at 16 MB.
- **CORS is added last, so it runs first:** a `413` still has the headers the website's browser needs to read it.

## 6. Dependencies

- **Packages:** `fastapi`, `starlette`.
- **Project files:** `app/api/routes.py`, `app/config.py`, `app/ml/predict.py`, `app/ml/results.py`.

## 7. How its output is used next

Uvicorn runs it, and the website calls it. Its CORS rules are what allow the website's address, `http://localhost:5173`, to read responses.

## 8. Tests

Tests are in [`test_api.py`](../../backend/tests/test_api.py), including one using a real server. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Stopping the server if the model is missing | Gives a less helpful failure |
| Using FastAPI's default validation errors | They repeat the rejected input |
| Relying only on the `Content-Length` header | A client can understate it or leave it out |
| Loading the model at import time | Slow, and it would fail tests that use a small model |
