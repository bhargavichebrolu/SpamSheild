# `frontend/src/components/TermContributions.test.tsx`

Source: [`TermContributions.test.tsx`](../../frontend/src/components/TermContributions.test.tsx).

## 1. Why the file exists

An explanation that's displayed wrongly would mislead.

## 2. Responsibility and design intention

It tests terms, values, the score breakdown and the bar scale.

## 3. Inputs and outputs

Input: made-up explanations. Output: pass or fail.

## 4. Important functions and variables

Tests cover direction, `escapenumber`, the sum table, one shared bar scale, and empty lists.

## 5. Key implementation decisions

Bar widths are compared approximately, because browsers round them.

## 6. Dependencies

`vitest`, Testing Library, fixtures.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Visual snapshot tests were rejected: they fail on harmless changes.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
