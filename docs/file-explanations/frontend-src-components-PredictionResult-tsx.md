# `frontend/src/components/PredictionResult.tsx`

Source: [`PredictionResult.tsx`](../../frontend/src/components/PredictionResult.tsx).

## 1. Why the file exists

This is the main result, and must be honest about what the model's number means.

## 2. Responsibility and design intention

It displays the label, decision score, supporting details, and the short-message caution.

## 3. Inputs and outputs

Input: the API's response, and whether the text has changed since. Output: the result section.

## 4. Important functions and variables

`PredictionResult`, and `SHORT_MESSAGE_RECOGNISED_WORDS`, which is 5.

## 5. Key implementation decisions

**The score is labelled a decision score,** with a plain statement that it isn't a probability, and no percentage appears. **The caution below 5 recognised words is a display warning, not a measured reliability boundary,** as it says on screen. It only adds text: the label and score come from the API unchanged. A result is marked out of date if the text changes. `DecisionGauge` shows where the score falls on the model's own scale, and isn't a percentage.

## 6. Dependencies

`react`, `types/api.ts`, `utils/format.ts`, `StatusMessage`, `TermContributions`.

## 7. How its output is used next

`ClassifierPage` renders it.

## 8. Tests

[`PredictionResult.test.tsx`](../../frontend/src/components/PredictionResult.test.tsx), including both sides of the threshold.

## 9. Alternatives considered

Showing the score as a percentage or confidence bar was rejected: a Linear SVM provides no meaningful probability.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
