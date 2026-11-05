# `backend/tests/test_api.py`

Source: [`test_api.py`](../../backend/tests/test_api.py).

## 1. Why the file exists

This is how the API's behaviour is checked: what it returns for good input, bad input and failures.

## 2. Responsibility and design intention

It sends requests to the application, using the tiny model from `conftest.py`, and checks the responses.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Made-up requests, including deliberately invalid ones |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Area | What's checked |
|---|---|
| Valid input | Complete responses, and `confidence` is always `null` |
| Direct inference | API labels and scores match the pipeline's |
| Empty input | Empty and whitespace-only text are rejected |
| Oversized input | Exactly 20,000 characters is accepted, 20,001 is rejected, and emoji count as one character each |
| Body size | Over 256 KB is rejected, including when the size is understated |
| Invalid input | Missing fields, wrong types, invalid JSON and invalid UTF-8 |
| Model loading | Missing or tampered models give `503`, and validation still works |
| Error handling | Unknown paths and wrong methods use the standard error shape |
| Privacy | Text never appears in errors or logs, and removed words never appear |
| Browser access | The local website is allowed, and other origins aren't |
| Documentation | `/docs` and the schema are available, with the limit shown |

## 5. Key implementation decisions

- **Both sides of the limit are tested:** 20,000 passes and 20,001 fails, which catches an off-by-one error.
- **Privacy tests use a marker word:** it's easy to search for in responses and logs.
- **One test starts a real server:** replying too early resets the connection, which only real HTTP shows. It runs five times, because that bug depended on timing.
- **Failures are injected:** a replaced `classify` raises an error containing the text, to show it doesn't leak.

## 6. Dependencies

`pytest`, `fastapi`, `httpx2` (through the test client), `uvicorn`, and `app`.

## 7. How its output is used next

Passing tests are part of Milestone 4's acceptance check. They also protect the API the website depends on.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 290 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Starting a real server for every test | Much slower, and only one behaviour needs it |
| Using the real model | It isn't in Git. [`test_verify_api.py`](../../backend/tests/test_verify_api.py) covers it when present. |
