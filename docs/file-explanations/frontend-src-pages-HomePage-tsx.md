# `frontend/src/pages/HomePage.tsx`

Source: [`HomePage.tsx`](../../frontend/src/pages/HomePage.tsx).

## 1. Why the file exists

The first page looked bare, and gave no sense of what the project found.

## 2. Responsibility and design intention

It's the landing page: a hero with headline results, the classifier, how it works, and charts.

## 3. Inputs and outputs

Input: `GET /api/results/models` and `GET /api/results/dataset`. Output: the page. The classifier inside it calls `POST /api/classify`.

## 4. Important functions and variables

`HomePage`, `Hero`, `HeroTile`, `HowItWorks`, `Overview`, `STEPS`.

## 5. Key implementation decisions

**The hero shows the weaker results beside the strongest,** and says they only describe this dataset, so colourful design doesn't overstate performance. **Results are optional here:** if they fail, numbers and charts disappear with no extra error, and the classifier still works, because its own status message explains any API problem. All numbers come from the API.

## 6. Dependencies

`react-router-dom`, `Charts`, `useApiResource`, `services/api.ts`, `utils/format.ts`, `utils/results.ts`, `ClassifierPage`.

## 7. How its output is used next

`App.tsx` routes `/` to it.

## 8. Tests

[`HomePage.test.tsx`](../../frontend/src/pages/HomePage.test.tsx), plus browser tests comparing headline numbers with the report files.

## 9. Alternatives considered

A separate landing page, with the classifier elsewhere, was rejected: it would add a click to the main thing people come to do.

From the `frontend` folder, run `npm test` for unit tests, and `npm run test:e2e` for browser tests with the real backend and model.

Result on 2026-11-05: 119 unit tests passed, 61 browser tests passed with the real model, and 4 passed with no API listening.
