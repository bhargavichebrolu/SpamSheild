# `frontend/tests/e2e/app.spec.ts`

Source: [`app.spec.ts`](../../frontend/tests/e2e/app.spec.ts).

## 1. Why the file exists

Only a real browser, backend and model can show that the whole application works.

## 2. Responsibility and design intention

**Nothing is stubbed.** It uses the real site, the real API and the frozen model, and compares displayed values with direct API calls and report files.

## 3. Inputs and outputs

Input: made-up messages, API responses and report files. Output: pass or fail, and screenshots in `docs/screenshots/`.

## 4. Important functions and variables

Tests cover the landing page's numbers and charts, classification, explanations, the decision score, the caution, errors, privacy, saved results, responsive layout at 360, 768 and 1280 pixels, accessibility in both colour modes, and keyboard use.

## 5. Key implementation decisions

It checks the frozen model's file hash after running. One test slows a real request only to see the loading state, and the response still comes from the real API. Messages are made up, so screenshots contain no real email.

## 6. Dependencies

`@playwright/test`, `@axe-core/playwright`, and the running applications.

## 7. How its output is used next

Part of the frontend's acceptance check, and it produces the screenshots.

## 8. Tests

From `frontend`, run `npm run test:e2e`. It starts both applications by itself, so make sure ports 8000 and 5173 are free.

## 9. Alternatives considered

A stubbed API was rejected: it couldn't catch a real mismatch, or the upload bug found in Milestone 4.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
