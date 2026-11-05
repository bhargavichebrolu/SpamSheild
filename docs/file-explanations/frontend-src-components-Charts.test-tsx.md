# `frontend/src/components/Charts.test.tsx`

Source: [`Charts.test.tsx`](../../frontend/src/components/Charts.test.tsx).

## 1. Why the file exists

A chart that draws the wrong size misleads, even with the right numbers beside it.

## 2. Responsibility and design intention

It tests that values are written as text, and that bars use the right scale.

## 3. Inputs and outputs

Input: made-up chart data. Output: pass or fail.

## 4. Important functions and variables

Tests cover shared scales, proportional parts, empty data, series colours, accessible names, and the gauge's position and scale.

## 5. Key implementation decisions

One test confirms the gauge's description has no percentage or probability.

## 6. Dependencies

`vitest`, Testing Library.

## 7. How its output is used next

Part of the acceptance check for the redesign.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Visual snapshot tests were rejected: they fail on harmless changes.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
