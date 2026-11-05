# `frontend/src/pages/ClassifierPage.test.tsx`

Source: [`ClassifierPage.test.tsx`](../../frontend/src/pages/ClassifierPage.test.tsx).

## 1. Why the file exists

This page has the most ways to go wrong.

## 2. Responsibility and design intention

It tests the page's whole flow, with the API replaced.

## 3. Inputs and outputs

Input: stubbed API replies and simulated typing. Output: pass or fail.

## 4. Important functions and variables

Tests cover success, loading, refusals, an unreachable API, an unavailable model, retry, out-of-date results, slow earlier responses, clearing and privacy.

## 5. Key implementation decisions

The slow-response test releases replies out of order, to prove a late answer can't overwrite a newer one.

## 6. Dependencies

`vitest`, Testing Library, fixtures, helpers.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Relying only on browser tests was rejected: out-of-order replies are hard to arrange against a real server.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
