# `frontend/src/test/setup.ts`

Source: [`setup.ts`](../../frontend/src/test/setup.ts).

## 1. Why the file exists

Unit tests share some setup.

## 2. Responsibility and design intention

It adds page matchers such as `toBeInTheDocument`, and clears the page after each test.

## 3. Inputs and outputs

No inputs or outputs. Vitest runs it first.

## 4. Important functions and variables

`cleanup`, run after each test.

## 5. Key implementation decisions

Cleanup is needed here because Testing Library only does it automatically with global test functions, and this project imports them explicitly. Leaving it out made 55 tests fail, as pages carried over between tests.

## 6. Dependencies

`@testing-library/jest-dom`, `@testing-library/react`, `vitest`.

## 7. How its output is used next

Vitest loads it through `vite.config.ts`.

## 8. Tests

It supports all the unit tests.

## 9. Alternatives considered

Turning on Vitest's global functions was rejected, because explicit imports show where each function comes from.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
