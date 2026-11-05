# `frontend/src/pages/ModelsPage.tsx`

Source: [`ModelsPage.tsx`](../../frontend/src/pages/ModelsPage.tsx).

## 1. Why the file exists

Reviewers should be able to see how the model was chosen and measured, using real results.

## 2. Responsibility and design intention

It displays final test results, the selected model, all comparison runs, the source-leakage experiment and limitations.

## 3. Inputs and outputs

Input: `GET /api/results/models`. Output: the page, or an error with no numbers.

## 4. Important functions and variables

`ModelsPage`, `TestResults`, `SelectedModel`, `ComparisonTable`, `SourceLeakageResults`, `crossStyleName`.

## 5. Key implementation decisions

**Every number comes from the API.** The note that the selected model isn't the highest F1 is worked out from the data, not written in. Sample counts appear for each similarity band. The source-leakage section keeps its warning that it doesn't prove generalisation. A warning appears if the test report doesn't describe the saved model.

## 6. Dependencies

`ResultsParts`, `StatusMessage`, `useApiResource`, `services/api.ts`, `utils/format.ts`.

## 7. How its output is used next

`App.tsx` routes `/models` to it.

## 8. Tests

[`ModelsPage.test.tsx`](../../frontend/src/pages/ModelsPage.test.tsx). Browser tests compare displayed values with the report files.

## 9. Alternatives considered

Showing only the best results was rejected, because the lower cross-style scores are the most important limitation.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
