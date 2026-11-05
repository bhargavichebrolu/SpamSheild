# `frontend/src/components/ClassifierForm.tsx`

Source: [`ClassifierForm.tsx`](../../frontend/src/components/ClassifierForm.tsx).

## 1. Why the file exists

Users need somewhere to paste text, with clear limits and controls.

## 2. Responsibility and design intention

It holds the text box, character counter and buttons. The page keeps the state.

## 3. Inputs and outputs

Input: the current text and loading state. Output: change, submit and clear events.

## 4. Important functions and variables

`ClassifierForm`, and `MAX_INPUT_CHARACTERS`.

## 5. Key implementation decisions

**The server still enforces the limit.** The form only warns, and over-long text can still be submitted so that the server's clear refusal appears. Classify is disabled for blank text and during loading, which prevents double submission. A browser test confirms the limit matches the API's.

## 6. Dependencies

`react`, `utils/format.ts`.

## 7. How its output is used next

`ClassifierPage` renders it.

## 8. Tests

[`ClassifierForm.test.tsx`](../../frontend/src/components/ClassifierForm.test.tsx).

## 9. Alternatives considered

The text box's `maxLength` was rejected, because it would silently cut off pasted text, which is what the 20,000-character rule exists to avoid.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
