# `frontend/src/components/Charts.tsx`

Source: [`Charts.tsx`](../../frontend/src/components/Charts.tsx).

## 1. Why the file exists

The site needed charts to make results easier to take in at a glance.

## 2. Responsibility and design intention

It draws the values it's given, and creates none. Charts are plain HTML, so they resize with the page without a chart library.

## 3. Inputs and outputs

Input: series, rows and values from the page. Output: charts, each with its values written as text.

## 4. Important functions and variables

`StackedBars`, `RatioBars`, `GroupedBars`, `ShareBar`, `ChartLegend`, `DecisionGauge`, `gaugeLimit`.

## 5. Key implementation decisions

**Bars start at zero and share one scale,** so differences appear at their true size. Error counts are charted rather than F1, because F1 values from 0.97 to 0.99 would look the same from zero. **Every value is also written as text,** so nothing depends on colour or hover. **`DecisionGauge` shows a position on the model's own scale, not a percentage.** It uses a scale of at least -2 to +2, widening only to keep a large score on the track. The colours passed a colour-vision validator, and two low-contrast split colours rely on their text labels.

## 6. Dependencies

`react`, `utils/format.ts`, `index.css`.

## 7. How its output is used next

`HomePage`, `ModelsPage`, `DatasetPage` and `PredictionResult` use it.

## 8. Tests

[`Charts.test.tsx`](../../frontend/src/components/Charts.test.tsx), plus browser tests comparing chart values with the reports.

## 9. Alternatives considered

A chart library was rejected: these simple bars don't need one. A pie or donut for two values was rejected: a bar with numbers is clearer. A speedometer-style gauge was rejected, because it could read as a percentage.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
