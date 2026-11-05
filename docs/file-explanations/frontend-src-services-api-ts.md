# `frontend/src/services/api.ts`

Source: [`api.ts`](../../frontend/src/services/api.ts).

## 1. Why the file exists

Every page needs to reach the backend, and to tell apart the ways that can fail.

## 2. Responsibility and design intention

**This is the only file that calls the network.** It sends requests, and turns failures into a clear `ApiError`. There are no sample or fallback results: if the backend can't answer, pages show an error.

## 3. Inputs and outputs

Input: message text or a page's request. Output: the backend's parsed response, or an `ApiError`.

## 4. Important functions and variables

`classifyEmail`, `getHealth`, `getModelsResults`, `getDatasetResults`. `ApiError.kind` is `network`, `timeout`, `server` or `invalid_response`. `API_BASE_URL` defaults to `http://127.0.0.1:8000`.

## 5. Key implementation decisions

**Failures stay distinct,** so a page can say "start the API" only when that's the problem. A 503 from health is a normal answer, because it explains why the model isn't loaded. Cancelled requests pass through without becoming error messages. Requests time out after 30 seconds.

## 6. Dependencies

The browser's `fetch`, and `types/api.ts`.

## 7. How its output is used next

Pages call these functions directly.

## 8. Tests

[`api.test.ts`](../../frontend/src/services/api.test.ts). A source scan also confirms nothing else calls the network.

## 9. Alternatives considered

Vite's proxy was rejected, because calling the API directly exercises the real CORS rules. A library such as axios was rejected, because `fetch` is enough.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
