# `frontend/src/types/api.ts`

Source: [`api.ts`](../../frontend/src/types/api.ts).

## 1. Why the file exists

TypeScript needs to know the shape of each API response, to catch mistakes before the site runs.

## 2. Responsibility and design intention

It describes responses, and contains no logic. It mirrors `backend/app/schemas`.

## 3. Inputs and outputs

No runtime inputs or outputs. Other files import its types.

## 4. Important functions and variables

`ClassifyResponse`, `HealthResponse`, `ModelsResults` and `DatasetResults`. `confidence` has the type `null`, so code can't treat it as a number.

## 5. Key implementation decisions

It's written by hand to stay readable. Since nothing checks it against the backend automatically, browser tests against the real API catch any mismatch in practice.

## 6. Dependencies

None.

## 7. How its output is used next

`services/api.ts`, pages and components import it.

## 8. Tests

Checked by `npm run typecheck`, and through the browser tests.

## 9. Alternatives considered

Generating types from the API's schema would remove the hand-written copy, but adds a tool and a build step, so it could be future work.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
