# `frontend/src/utils/format.ts`

Source: [`format.ts`](../../frontend/src/utils/format.ts).

## 1. Why the file exists

API values need turning into readable text, in one consistent way.

## 2. Responsibility and design intention

It formats values for display, and never creates or changes a result.

## 3. Inputs and outputs

Input: values from the API. Output: display text.

## 4. Important functions and variables

`modelName`, `featureName`, `styleName`, `removalName`, `flagName`, `bandName`, `settingText`, `count`, `metric`, `share`, `signed`, `fileSize`.

## 5. Key implementation decisions

An unknown name is shown as received, rather than hidden. `signed` always shows direction. `share` is for rows in a dataset and is never used for a prediction, which a source scan checks.

## 6. Dependencies

None.

## 7. How its output is used next

Pages and components use it.

## 8. Tests

[`format.test.ts`](../../frontend/src/utils/format.test.ts).

## 9. Alternatives considered

Formatting inside each page was rejected, because numbers could then appear differently from page to page.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
