# `frontend/playwright.config.ts`

Source: [`playwright.config.ts`](../../frontend/playwright.config.ts).

## 1. Why the file exists

Browser tests need both applications running, and a browser to use.

## 2. Responsibility and design intention

It starts the applications, chooses the browser, and selects which suite to run.

## 3. Inputs and outputs

Input: optional `E2E_API_DOWN`, `E2E_PYTHON` and `E2E_BROWSER_CHANNEL` settings. Output: test settings.

## 4. Important functions and variables

`apiDown`, `python`, `webServer`, `channel`.

## 5. Key implementation decisions

It uses the Edge browser already installed, so nothing extra is downloaded. Tests run one at a time, for steady results. It never reuses a running server, so tests can't silently run against something else. The Python path is resolved and quoted, because Windows' command shell can't run the forward-slash form.

## 6. Dependencies

`@playwright/test`, Node's `path`.

## 7. How its output is used next

`npm run test:e2e` and `npm run test:e2e:api-down` use it.

## 8. Tests

Exercised by the browser tests.

## 9. Alternatives considered

Downloading Playwright's own browsers was rejected as unnecessary here. Other computers may need `E2E_BROWSER_CHANNEL`, or Playwright's browsers, if they don't have Edge.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
