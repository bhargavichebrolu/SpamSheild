# `frontend/src/test/helpers.ts`

Source: [`helpers.ts`](../../frontend/src/test/helpers.ts).

## 1. Why the file exists

Unit tests need to replace network calls in a controlled way.

## 2. Responsibility and design intention

It provides a stand-in for `fetch`, **for automated tests only.**

## 3. Inputs and outputs

Input: replies chosen by path. Output: a stubbed `fetch`.

## 4. Important functions and variables

`stubApi`, `jsonResponse`.

## 5. Key implementation decisions

A request to an unexpected path fails the test, so a page can't quietly call something unplanned.

## 6. Dependencies

`vitest`.

## 7. How its output is used next

Unit tests use it.

## 8. Tests

Used by the unit tests.

## 9. Alternatives considered

A request-mocking library was rejected, because this small helper is enough.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
