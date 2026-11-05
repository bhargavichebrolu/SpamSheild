# `frontend/src/pages/HomePage.test.tsx`

Source: [`HomePage.test.tsx`](../../frontend/src/pages/HomePage.test.tsx).

## 1. Why the file exists

The landing page's headline numbers must come from the API, and must include the weaker results.

## 2. Responsibility and design intention

It tests the hero, charts and failure behaviour.

## 3. Inputs and outputs

Input: made-up API responses. Output: pass or fail.

## 4. Important functions and variables

Tests cover one main heading, headline numbers, the dataset-only note, charts, and that failed results remove numbers without adding an extra alert or blocking the classifier.

## 5. Key implementation decisions

Made-up values are used here, and browser tests cover the real ones.

## 6. Dependencies

`vitest`, Testing Library, `react-router-dom`, fixtures, helpers.

## 7. How its output is used next

Part of the acceptance check for the redesign.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Testing only in a browser would make failure cases harder to arrange.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
