# `frontend/src/main.tsx`

Source: [`main.tsx`](../../frontend/src/main.tsx).

## 1. Why the file exists

The browser needs a starting point that puts the application on the page.

## 2. Responsibility and design intention

It starts React and the router, and loads the styles. It has no logic of its own.

## 3. Inputs and outputs

Input: the `root` element in `index.html`. Output: the running website.

## 4. Important functions and variables

`createRoot` renders `App`. `StrictMode` runs extra checks in development. `BrowserRouter` gives each page its own URL.

## 5. Key implementation decisions

It stops with a clear error if the root element is missing, rather than showing a blank page.

## 6. Dependencies

`react`, `react-dom`, `react-router-dom`, `App.tsx`, `index.css`.

## 7. How its output is used next

It renders [`App.tsx`](../../frontend/src/App.tsx).

## 8. Tests

Covered through the browser tests, which load the real page.

## 9. Alternatives considered

A hash-based router was rejected, because ordinary URLs are clearer and Vite's development server supports them.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
