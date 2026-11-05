# `frontend/src/App.tsx`

Source: [`App.tsx`](../../frontend/src/App.tsx).

## 1. Why the file exists

The website needs one shared layout, and a way to move between its pages.

## 2. Responsibility and design intention

It holds the header, navigation, footer and routes. Page content stays in `pages/`.

## 3. Inputs and outputs

Input: the current URL. Output: the matching page inside the shared layout.

## 4. Important functions and variables

`PAGES` lists the three pages. `App` sets the page title and routes. `ShieldLogo` draws the logo. `NotFoundPage` handles unknown addresses.

## 5. Key implementation decisions

The navigation bar is a sticky gradient with pill-shaped links, and the current page's link is white. The footer states on every page that this is a prototype, not a security product. A skip link helps keyboard users. Navigation wraps on narrow screens rather than hiding behind a menu, because there are only three items.

## 6. Dependencies

`react`, `react-router-dom`, and the three pages.

## 7. How its output is used next

`main.tsx` renders it.

## 8. Tests

[`App.test.tsx`](../../frontend/src/App.test.tsx), plus the browser tests.

## 9. Alternatives considered

A collapsing menu was rejected, because three links fit at 360 pixels, and hiding them would only add clicks.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
