# `frontend/src/hooks/useApiResource.ts`

Source: [`useApiResource.ts`](../../frontend/src/hooks/useApiResource.ts).

## 1. Why the file exists

The Models and Dataset pages both load data on opening, and need the same loading, error and retry behaviour.

## 2. Responsibility and design intention

It loads something from the API when a page opens, and provides a way to try again.

## 3. Inputs and outputs

Input: a loading function. Output: `data`, `error`, `loading` and `retry`.

## 4. Important functions and variables

`useApiResource`, and the `ApiResource` type.

## 5. Key implementation decisions

A request is cancelled if the page closes, so a late response can't update a page that's gone. The loading function must stay the same between renders, which is why pages pass named functions.

## 6. Dependencies

`react`.

## 7. How its output is used next

`ClassifierPage`, `ModelsPage` and `DatasetPage` use it.

## 8. Tests

Covered through the page tests.

## 9. Alternatives considered

A data-fetching library was rejected, because two simple page loads don't need caching or background refetching. It could be reconsidered if the site grows.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
