# `frontend/src/components/TermContributions.tsx`

Source: [`TermContributions.tsx`](../../frontend/src/components/TermContributions.tsx).

## 1. Why the file exists

Users should see which words moved the score, and that the numbers add up.

## 2. Responsibility and design intention

It displays the API's explanation as two lists with bars, plus a table showing how the parts add up to the decision score.

## 3. Inputs and outputs

Input: the API's explanation and score. Output: lists, bars and a table.

## 4. Important functions and variables

`TermContributions`, `TermList`, `displayTerm`.

## 5. Key implementation decisions

**Every value is written as text,** so the bars only add a quick visual comparison and are hidden from screen readers. Bars share one scale across both lists, so sizes can be compared. Direction appears in the heading as well as colour. `escapenumber` is explained as a number. All values come from the API, and only totals are summed here.

## 6. Dependencies

`react`, `types/api.ts`, `utils/format.ts`.

## 7. How its output is used next

`PredictionResult` renders it.

## 8. Tests

[`TermContributions.test.tsx`](../../frontend/src/components/TermContributions.test.tsx). A browser test confirms the parts add up, using the real model.

## 9. Alternatives considered

A chart library was rejected, because simple bars don't need one. A single chart with a centre line was rejected, because two lists read better at 360 pixels.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
