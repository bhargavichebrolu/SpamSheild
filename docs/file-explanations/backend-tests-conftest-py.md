# `backend/tests/conftest.py`

Source: [`conftest.py`](../../backend/tests/conftest.py). `pytest` loads this file automatically. `backend/tests/__init__.py` is an empty file that lets tests import from it.

## 1. Why the file exists

API tests need a fitted model, but the real one isn't in Git. This builds a tiny one, saved the same way.

## 2. Responsibility and design intention

It provides shared test setup, using made-up text. It doesn't need the dataset, the real model or any training code.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | None, beyond a temporary folder from `pytest` |
| **Output** | A fitted pipeline, matching metadata, and test clients |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `build_pipeline` | Fits a tiny pipeline with the same structure as the real one |
| `write_model_files` | Saves it with matching hashes |
| `REMOVED_WORD` | An invented word, for testing that removed words never appear |
| `model_files`, `loaded_model`, `client` | Fixtures: reusable setup for tests |
| `make_client` | Builds test clients with a chosen loader, and closes them afterwards |

## 5. Key implementation decisions

- **Real preprocessing and the real classifier type:** so tests exercise the same code paths as production.
- **The model goes through the real loading path:** files are saved and verified, not created in memory.
- **The test client is started properly:** so the startup code runs, as in a real server.

## 6. Dependencies

`pytest`, `joblib`, `fastapi`, `scikit-learn`, and `app`.

## 7. How its output is used next

[`test_api.py`](../../backend/tests/test_api.py), [`test_explain.py`](../../backend/tests/test_explain.py), [`test_predict.py`](../../backend/tests/test_predict.py) and [`test_verify_api.py`](../../backend/tests/test_verify_api.py) use it.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 260 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Using the real model in every test | It isn't in Git, so tests would fail on a fresh copy |
| Faking the model entirely | Wouldn't test loading, hashing or real predictions |
