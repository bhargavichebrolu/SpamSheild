# `frontend/src/utils/results.test.ts`

Source: [`results.test.ts`](../../frontend/src/utils/results.test.ts).

## 1. Why the file exists

These helpers decide which numbers appear in headlines and charts.

## 2. Responsibility and design intention

It tests each selection against known values.

## 3. Inputs and outputs

Input: made-up results. Output: pass or fail.

## 4. Important functions and variables

Tests cover ignoring same-style and neither-style scores, empty bands, ordering, and keeping the selected run.

## 5. Key implementation decisions

One test confirms the selected run stays, even if another setting has a higher F1.

## 6. Dependencies

`vitest`, fixtures.

## 7. How its output is used next

Part of the acceptance check for the redesign.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Testing only through pages would hide which part failed.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
