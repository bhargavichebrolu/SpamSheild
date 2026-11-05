/**
 * Runs with only the website started and no backend, so these failures are real, not simulated.
 * Run with: npm run test:e2e:api-down
 */

import { expect, test } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const reachable = await request
    .get("http://127.0.0.1:8000/api/health")
    .then(() => true)
    .catch(() => false);
  expect(reachable, "This run needs the backend to be stopped").toBe(false);
});

test("the classifier explains how to start the API, and shows no result", async ({ page }) => {
  await page.goto("/");
  const banner = page.getByRole("alert");
  await expect(banner).toContainText("The API can't be reached");
  await expect(banner).toContainText("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000");
  await expect(banner.getByRole("button", { name: "Try again" })).toBeVisible();

  await page.getByLabel("Email text").fill("free prize");
  await page.getByRole("button", { name: "Classify", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(2);
  await expect(page.getByTestId("prediction-label")).toHaveCount(0);
});

test("the Models page shows an error and no numbers", async ({ page }) => {
  await page.goto("/models");
  await expect(page.getByRole("alert")).toContainText("The API can't be reached");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Final test results" })).toHaveCount(0);
  await expect(page.locator("table")).toHaveCount(0);
});

test("the Dataset page shows an error and no numbers", async ({ page }) => {
  await page.goto("/dataset");
  await expect(page.getByRole("alert")).toContainText("The API can't be reached");
  await expect(page.getByRole("heading", { name: "Overview" })).toHaveCount(0);
  await expect(page.locator("table")).toHaveCount(0);
});

test("the layout still fits on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/");
  await expect(page.getByRole("alert")).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
