# `frontend/src/pages/ClassifierPage.tsx`

Source: [`ClassifierPage.tsx`](../../frontend/src/pages/ClassifierPage.tsx).

## 1. Why the file exists

This is the main page, where a user classifies an email.

## 2. Responsibility and design intention

It holds the page's state and connects the form, the API and the result.

## 3. Inputs and outputs

Input: the user's text. Output: a real result from the API, or an error.

## 4. Important functions and variables

`ClassifierPage`, `BackendStatus`, `handleSubmit`, `handleClear`, `currentRequest`.

## 5. Key implementation decisions

**Only the newest request can update the page,** so a slow earlier response can't replace a newer one. **The text stays in memory only,** and isn't placed in the URL or browser storage. `BackendStatus` warns when the page opens if the API is down or its model is unavailable.

## 6. Dependencies

`react`, `ClassifierForm`, `PredictionResult`, `StatusMessage`, `useApiResource`, `services/api.ts`.

## 7. How its output is used next

`App.tsx` routes `/` to it.

## 8. Tests

[`ClassifierPage.test.tsx`](../../frontend/src/pages/ClassifierPage.test.tsx), plus the browser tests.

## 9. Alternatives considered

Saving recent results was deferred: prediction history is optional in the PRD, and adds storage and privacy work.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
