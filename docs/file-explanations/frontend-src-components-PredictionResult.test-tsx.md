# `frontend/src/components/PredictionResult.test.tsx`

Source: [`PredictionResult.test.tsx`](../../frontend/src/components/PredictionResult.test.tsx).

## 1. Why the file exists

The result must never suggest a certainty the model can't support.

## 2. Responsibility and design intention

It tests labels, the decision score, the caution and the out-of-date notice.

## 3. Inputs and outputs

Input: made-up results. Output: pass or fail.

## 4. Important functions and variables

Tests include no percentage or confidence value, the caution at 4 words but not at 5, and that the caution doesn't change the label or score.

## 5. Key implementation decisions

Both sides of the threshold are tested, which catches an off-by-one error.

## 6. Dependencies

`vitest`, Testing Library, fixtures.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`. A browser test repeats the key checks with the real model.

## 9. Alternatives considered

Checking only for the word "percent" would miss a `%` sign, so the tests check both.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
