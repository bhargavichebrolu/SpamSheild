# `frontend/src/utils/results.ts`

Source: [`results.ts`](../../frontend/src/utils/results.ts).

## 1. Why the file exists

Charts and headline numbers need specific values picked out of the API's larger results.

## 2. Responsibility and design intention

It selects and adds up values from API responses. It doesn't estimate or create anything.

## 3. Inputs and outputs

Input: `ModelsResults` or `DatasetResults`. Output: values and rows for charts.

## 4. Important functions and variables

`lowestCrossStyleF1`, `noCloseMatchF1`, `errorsByBand`, `errorShareOfFirstBand`, `crossStyleBars`, `bestRunPerCombination`, `numberStyleRows`, `wordShareRows`.

## 5. Key implementation decisions

`lowestCrossStyleF1` only counts scores on the other number style, and ignores the "neither" group, so it's a fair comparison. `bestRunPerCombination` keeps the selected run where it belongs, and otherwise picks that combination's highest F1, so the chart can't hide what was chosen.

## 6. Dependencies

`types/api.ts`, `utils/format.ts`.

## 7. How its output is used next

`HomePage`, `ModelsPage` and `DatasetPage` use it.

## 8. Tests

[`results.test.ts`](../../frontend/src/utils/results.test.ts).

## 9. Alternatives considered

Working these out inside each page was rejected, because the same logic would appear twice.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
