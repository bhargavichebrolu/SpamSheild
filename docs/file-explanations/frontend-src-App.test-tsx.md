# `frontend/src/App.test.tsx`

Source: [`App.test.tsx`](../../frontend/src/App.test.tsx).

## 1. Why the file exists

Navigation and the page frame need to work on every page.

## 2. Responsibility and design intention

It tests routing, titles and shared content.

## 3. Inputs and outputs

Input: a starting address. Output: pass or fail.

## 4. Important functions and variables

Tests cover moving between pages, page titles, unknown pages, the prototype notice and the skip link.

## 5. Key implementation decisions

`MemoryRouter` lets each test start at any address.

## 6. Dependencies

`vitest`, Testing Library, fixtures, helpers.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Testing only in a real browser would be slower for these simple checks.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
