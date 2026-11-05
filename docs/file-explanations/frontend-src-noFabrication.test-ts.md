# `frontend/src/noFabrication.test.ts`

Source: [`noFabrication.test.ts`](../../frontend/src/noFabrication.test.ts).

## 1. Why the file exists

The site must not contain mock predictions or made-up metrics, and a rule like that needs checking, not just promising.

## 2. Responsibility and design intention

It reads the application's own source files, and fails if it finds signs of fabricated results.

## 3. Inputs and outputs

Input: every non-test source file. Output: pass or fail.

## 4. Important functions and variables

Checks: no decimal metrics, no real result counts, no `Math.random`, no imports of test data, network calls only from `services/api.ts`, no browser storage, and no use of `confidence` or percentages in the prediction display.

## 5. Key implementation decisions

It caught `0.473`, in one of my own comments. **A source scan can't prove every number is real,** so browser tests also compare displayed values with the report files.

## 6. Dependencies

`vitest`, Node's `fs` and `path`.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

A code review alone was rejected, since a later change could reintroduce the problem unnoticed.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
