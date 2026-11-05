# `frontend/src/test/fixtures.ts`

Source: [`fixtures.ts`](../../frontend/src/test/fixtures.ts).

## 1. Why the file exists

Unit tests need predictable API responses, without running a backend.

## 2. Responsibility and design intention

It holds made-up responses, **for automated tests only.**

## 3. Inputs and outputs

No runtime inputs. Tests import its values.

## 4. Important functions and variables

`HEALTHY`, `SPAM_RESULT`, `HAM_RESULT`, `MODELS_RESULTS`, `DATASET_RESULTS`.

## 5. Key implementation decisions

The numbers are deliberately unlike real results, so they can't be mistaken for them. A source scan confirms application code never imports this file, and a check confirms its text isn't in the production bundle.

## 6. Dependencies

`types/api.ts`, so a change in response shape fails type checking here.

## 7. How its output is used next

Unit tests use it.

## 8. Tests

Used by the unit tests. It's excluded from the application by the scan in [`noFabrication.test.ts`](../../frontend/src/noFabrication.test.ts).

## 9. Alternatives considered

Browser tests deliberately don't use it: they run against the real backend.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
