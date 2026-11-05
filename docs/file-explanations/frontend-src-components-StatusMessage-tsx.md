# `frontend/src/components/StatusMessage.tsx`

Source: [`StatusMessage.tsx`](../../frontend/src/components/StatusMessage.tsx).

## 1. Why the file exists

Loading, errors and cautions should look and behave the same everywhere.

## 2. Responsibility and design intention

It displays messages, and chooses the right text for each kind of API failure.

## 3. Inputs and outputs

Input: a tone and text, or an error. Output: an announced message.

## 4. Important functions and variables

`StatusMessage`, `LoadingMessage`, `RetryButton`, `StartBackendHelp`, `ApiErrorMessage`.

## 5. Key implementation decisions

**Colour is never the only signal:** each message has text, and errors and cautions have an icon. Errors use `role="alert"` so screen readers announce them. A refused request shows the server's own message and no retry, since retrying wouldn't help. Failures that might be temporary offer a retry.

## 6. Dependencies

`react`, `services/api.ts`.

## 7. How its output is used next

All pages use it.

## 8. Tests

Covered through the page tests, and the browser tests with the backend stopped.

## 9. Alternatives considered

A pop-up notification was rejected, because errors should stay visible beside the action that caused them.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
