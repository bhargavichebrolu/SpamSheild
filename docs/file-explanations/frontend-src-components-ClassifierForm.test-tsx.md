# `frontend/src/components/ClassifierForm.test.tsx`

Source: [`ClassifierForm.test.tsx`](../../frontend/src/components/ClassifierForm.test.tsx).

## 1. Why the file exists

The form controls what can be submitted.

## 2. Responsibility and design intention

It tests blank text, the limit, loading and clearing.

## 3. Inputs and outputs

Input: props and simulated user actions. Output: pass or fail.

## 4. Important functions and variables

Tests cover blank input, double submission, both sides of the limit, and that over-long text stays submittable.

## 5. Key implementation decisions

User actions are simulated in the way a person would act.

## 6. Dependencies

`vitest`, Testing Library.

## 7. How its output is used next

Part of the frontend's acceptance check.

## 8. Tests

Run with `npm test`.

## 9. Alternatives considered

Testing only through the page would hide which part failed.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
