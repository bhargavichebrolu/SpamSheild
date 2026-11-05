# `frontend/src/utils/format.test.ts`

Source: [`format.test.ts`](../../frontend/src/utils/format.test.ts).

## 1. Why the file exists

Wrong formatting could misstate a result.

## 2. Responsibility and design intention

It tests each formatter with known values.

## 3. Inputs and outputs

Input: fixed values. Output: pass or fail.

## 4. Important functions and variables

Tests cover band names, unknown names, number formats and score signs.

## 5. Key implementation decisions

Unknown names are tested, so a new value appears as received and doesn't vanish.

## 6. Dependencies

`vitest`.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Checking formats only through pages would need far more setup.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
