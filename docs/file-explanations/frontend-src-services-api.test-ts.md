# `frontend/src/services/api.test.ts`

Source: [`api.test.ts`](../../frontend/src/services/api.test.ts).

## 1. Why the file exists

The API client decides what kind of failure each page reports, so that must be right.

## 2. Responsibility and design intention

It tests requests and every failure type, with `fetch` replaced.

## 3. Inputs and outputs

Input: stubbed responses. Output: pass or fail.

## 4. Important functions and variables

Tests cover the request sent, server refusals, network failure, unreadable responses, timeouts, cancellation and a 503 from health.

## 5. Key implementation decisions

Timeouts use fake timers, so the test doesn't wait 30 seconds.

## 6. Dependencies

`vitest`, test helpers and fixtures.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Testing only through pages would make it harder to see which layer failed.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
