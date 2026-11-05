# `frontend/tests/e2e/api-down.spec.ts`

Source: [`api-down.spec.ts`](../../frontend/tests/e2e/api-down.spec.ts).

## 1. Why the file exists

A stopped backend is the likeliest failure when running locally.

## 2. Responsibility and design intention

It runs with only the website started, so the failure is real, not simulated.

## 3. Inputs and outputs

Input: the running website, with no backend. Output: pass or fail.

## 4. Important functions and variables

Tests cover the start instructions, no results or tables without data, and phone layout. It first confirms the backend really is stopped.

## 5. Key implementation decisions

It's a separate run because the other suite needs the backend running.

## 6. Dependencies

`@playwright/test`.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

From `frontend`, run `npm run test:e2e:api-down`, with nothing running on port 8000.

## 9. Alternatives considered

Blocking requests inside the normal suite was rejected, because this is closer to what a user would see.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
