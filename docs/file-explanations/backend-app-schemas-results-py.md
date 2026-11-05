# `backend/app/schemas/results.py`

Source: [`results.py`](../../backend/app/schemas/results.py).

## 1. Why the file exists

Results sent to the website must be limited to verified aggregate information.

## 2. Responsibility and design intention

It defines each results response. **Pydantic drops any field not named here, so these schemas are also an allowlist.**

## 3. Inputs and outputs

Input: dictionaries from `results.py`. Output: validated responses, and the API's documented schema.

## 4. Important functions and variables

`ModelsResults`, `DatasetResults`, and nested types such as `Metrics`, `SimilarityBand` and `CrossStyleRun`.

## 5. Key implementation decisions

There's no field that could hold email text, or the word lists. A test adds an unexpected field to a report, and confirms it doesn't reach the response.

## 6. Dependencies

`pydantic`.

## 7. How its output is used next

`routes.py` uses them, and they guided `frontend/src/types/api.ts`.

## 8. Tests

[`test_results_api.py`](../../backend/tests/test_results_api.py).

## 9. Alternatives considered

`dict[str, Any]` was rejected, because it would pass anything through.
