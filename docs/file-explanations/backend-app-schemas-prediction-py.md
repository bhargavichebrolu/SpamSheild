# `backend/app/schemas/prediction.py`

Source: [`prediction.py`](../../backend/app/schemas/prediction.py). `backend/app/schemas/__init__.py` is an empty file that lets Python import this folder as a package.

## 1. Why the file exists

It defines the shape of each request and response in one place, so they're validated automatically and appear in the generated documentation.

## 2. Responsibility and design intention

It describes data, and validates the request. It doesn't classify anything.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Request JSON, and the results from `app/ml` |
| **Output** | Validated objects, and the API's documented schema |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `ClassifyRequest` | Requires `text`: a string of up to 20,000 characters, and not blank |
| `ClassifyResponse` | The classification result |
| `Explanation`, `TermContribution` | The explanation's shape |
| `HealthResponse` | The health result |
| `ModelInfoResponse` | The model information, with nested result types |
| `ErrorResponse`, `ErrorDetail` | The one shape used by every error |

## 5. Key implementation decisions

- **`confidence` has the type `None`:** the schema itself makes a probability impossible to return, not just a convention.
- **`max_length` is in the schema:** so the limit appears in the generated documentation.
- **Blank text uses a custom error type:** so `main.py` can return a clear `text_empty` code.
- **Characters, not bytes:** an emoji counts as one character. A test confirms this.

## 6. Dependencies

- **Packages:** `pydantic`, `pydantic_core`.
- **Project files:** `app/config.py`.

## 7. How its output is used next

`routes.py` uses these for requests and responses, and they guided the website's types in `frontend/src/types/api.ts`.

## 8. Tests

Tests are in [`test_api.py`](../../backend/tests/test_api.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Checking input by hand in the endpoint | More code, and it wouldn't appear in the documentation |
| Leaving out `confidence` | The PRD's example includes it, and an explicit `null` makes clear it's deliberately absent |
| Returning `score` as a percentage | It isn't a probability, so that would be misleading |
