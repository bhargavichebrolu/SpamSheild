# `frontend/src/components/ResultsParts.tsx`

Source: [`ResultsParts.tsx`](../../frontend/src/components/ResultsParts.tsx).

## 1. Why the file exists

The Models and Dataset pages share several display pieces.

## 2. Responsibility and design intention

It provides section, stat, table and chart parts. It doesn't fetch data.

## 3. Inputs and outputs

Input: values from the page. Output: display elements.

## 4. Important functions and variables

`PageSection`, `StatTile`, `StatGrid`, `TableScroll`, `ConfusionMatrix`, `LabelBalanceBar`.

## 5. Key implementation decisions

**`TableScroll` keeps wide tables from widening the page,** can take keyboard focus, and shows a hint only when a table really overflows. Descriptions sit outside the scrolling area, because they were getting cut off inside it. `LabelBalanceBar` has a text legend and an accessible name, so no text sits on colour.

## 6. Dependencies

`react`, `types/api.ts`, `utils/format.ts`.

## 7. How its output is used next

`ModelsPage` and `DatasetPage` use it.

## 8. Tests

Covered through the page tests. A browser test checks every table's hint at 360, 768 and 1280 pixels.

## 9. Alternatives considered

Hiding columns on phones was rejected, because it would hide results. A pie chart was rejected, because a simple bar with numbers is clearer for two values.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 90 unit tests passed, 50 browser tests passed with the real model, and 4 passed with the backend stopped.
