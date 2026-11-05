# `frontend/src/index.css`

Source: [`index.css`](../../frontend/src/index.css).

## 1. Why the file exists

Colours and table styles must stay consistent across pages and colour modes.

## 2. Responsibility and design intention

It defines colours by role, swaps them in dark mode, and styles data tables.

## 3. Inputs and outputs

Input: the browser's colour preference. Output: styles used across the site.

## 4. Important functions and variables

The `--ham` and `--spam` roles colour marks. Ink roles colour text. `.data-table` styles every table.

## 5. Key implementation decisions

**Text uses ink colours, never Ham or Spam colours,** so it stays readable. The Ham and Spam pair passed a colour-vision validator in both modes. Numbers use aligned figures only in tables. Row names wrap, so they don't push numbers off a narrow screen. No fonts are downloaded.

## 6. Dependencies

Tailwind CSS.

## 7. How its output is used next

All components use these roles.

## 8. Tests

Automated accessibility checks in the browser tests cover contrast in both modes.

## 9. Alternatives considered

White text on coloured bars was rejected, because it failed contrast checks. A separate dark theme file was rejected, because one set of roles keeps the modes in step.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
