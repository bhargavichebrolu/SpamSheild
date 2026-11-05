# `frontend/src/pages/DatasetPage.test.tsx`

Source: [`DatasetPage.test.tsx`](../../frontend/src/pages/DatasetPage.test.tsx).

## 1. Why the file exists

This page must show verified statistics, and be clear about what isn't verified.

## 2. Responsibility and design intention

It tests each section, the licence notice and failures.

## 3. Inputs and outputs

Input: made-up statistics. Output: pass or fail.

## 4. Important functions and variables

Tests cover the licence, the source link, added-up totals, the balance bar, numeric ordering, and that long text stays outside tables.

## 5. Key implementation decisions

The last check guards against a layout bug found by looking at phone screenshots.

## 6. Dependencies

`vitest`, Testing Library, fixtures, helpers.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Comparing to real values here was rejected: browser tests do that.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
