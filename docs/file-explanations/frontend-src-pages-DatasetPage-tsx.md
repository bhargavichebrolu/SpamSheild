# `frontend/src/pages/DatasetPage.tsx`

Source: [`DatasetPage.tsx`](../../frontend/src/pages/DatasetPage.tsx).

## 1. Why the file exists

Reviewers should be able to see what the model was trained on, and what's unverified.

## 2. Responsibility and design intention

It displays verified aggregate statistics, and shows no email text.

## 3. Inputs and outputs

Input: `GET /api/results/dataset`. Output: the page, or an error with no numbers.

## 4. Important functions and variables

`DatasetPage`, `Overview`, `Source`, `SourceRow`, `Duplicates`, `Lengths`, `TextFormat`, `Preparation`.

## 5. Key implementation decisions

**The licence is prominently "Not verified".** Charts show message length, number styles, source-word shares and the split, with the full tables below them. Source details use a wrapping list instead of a table, because a table cut them off on phones. The explanation of each cleaning rule is written here, while its count comes from the API.

## 6. Dependencies

`react`, `Charts`, `ResultsParts`, `StatusMessage`, `useApiResource`, `services/api.ts`, `utils/format.ts`, `utils/results.ts`.

## 7. How its output is used next

`App.tsx` routes `/dataset` to it.

## 8. Tests

[`DatasetPage.test.tsx`](../../frontend/src/pages/DatasetPage.test.tsx). Browser tests compare displayed values with the report files.

## 9. Alternatives considered

Showing example messages was rejected: the licence is unverified, and the API's schema has no field for them.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
