# `frontend/vite.config.ts`

Source: [`vite.config.ts`](../../frontend/vite.config.ts).

## 1. Why the file exists

The development server, build and unit tests need configuring.

## 2. Responsibility and design intention

It connects the React and Tailwind plugins, and sets up the unit tests.

## 3. Inputs and outputs

Input: none at runtime. Output: settings for Vite and Vitest.

## 4. Important functions and variables

`plugins` and `test`.

## 5. Key implementation decisions

Unit tests only match files in `src`, so browser tests run separately.

## 6. Dependencies

`vite`, `vitest`, `@vitejs/plugin-react`, `@tailwindcss/vite`.

## 7. How its output is used next

`npm run dev`, `npm run build` and `npm test` use it.

## 8. Tests

Exercised by every frontend command.

## 9. Alternatives considered

A separate Vitest config was rejected, because one file keeps settings together.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
