# `frontend/src/pages/ModelsPage.test.tsx`

Source: [`ModelsPage.test.tsx`](../../frontend/src/pages/ModelsPage.test.tsx).

## 1. Why the file exists

This page must show results exactly as saved.

## 2. Responsibility and design intention

It tests display, marking of the selected run, warnings and failures.

## 3. Inputs and outputs

Input: made-up results. Output: pass or fail.

## 4. Important functions and variables

Tests cover band counts, empty bands, the not-highest-F1 note, the mismatch warning, the interpretation note, and that errors show no numbers.

## 5. Key implementation decisions

Made-up values are used here, while browser tests cover real ones.

## 6. Dependencies

`vitest`, Testing Library, fixtures, helpers.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Using real report values here was rejected, because it would tie these tests to one set of results.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
