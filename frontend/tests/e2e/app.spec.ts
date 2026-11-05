/**
 * End-to-end tests in a real browser, against the real backend and frozen model. Nothing is
 * stubbed. Displayed values are compared with direct API calls and the saved report files.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const API = "http://127.0.0.1:8000";
const HERE = dirname(fileURLToPath(import.meta.url));
const BACKEND = join(HERE, "../../../backend");
const SCREENSHOTS = join(HERE, "../../../docs/screenshots");

const FROZEN_FILE_SHA256 = "ed9f16df062afe7bb4ba3dd1acb6473d5119aa643ae1bcdf9d042279de788b2c";

const SPAM_EMAIL =
  "Congratulations! You have WON a free prize. Click here to claim your 1000 dollars today. Limited offer, buy now.";
const HAM_EMAIL =
  "Hi Sam, the project meeting has moved to Tuesday at 3pm. I have attached the notes and the budget report. Please review them before the call.";

const report = (name: string) => JSON.parse(readFileSync(join(BACKEND, "reports", name), "utf-8"));
const frozenFileHash = () =>
  createHash("sha256").update(readFileSync(join(BACKEND, "models/spamshield_pipeline.joblib"))).digest("hex");

const signed = (value: number, decimals = 3) => `${value > 0 ? "+" : ""}${value.toFixed(decimals)}`;
const count = (value: number) => value.toLocaleString("en-GB");

async function classify(page: Page, text: string) {
  await page.goto("/");
  await page.getByLabel("Email text").fill(text);
  await page.getByRole("button", { name: "Classify", exact: true }).click();
}

async function apiClassify(request: APIRequestContext, text: string) {
  const response = await request.post(`${API}/api/classify`, { data: { text } });
  expect(response.status()).toBe(200);
  return response.json();
}

test.beforeAll(() => {
  mkdirSync(SCREENSHOTS, { recursive: true });
});

test.afterAll(() => {
  expect(frozenFileHash()).toBe(FROZEN_FILE_SHA256);
});

test.describe("Email classifier, with the real model", () => {
  for (const [name, email] of [
    ["spam-like", SPAM_EMAIL],
    ["ham-like", HAM_EMAIL],
  ] as const) {
    test(`shows the same label and decision score as the API for a ${name} message`, async ({ page, request }) => {
      const expected = await apiClassify(request, email);
      await classify(page, email);

      await expect(page.getByTestId("prediction-label")).toHaveText(expected.label === "spam" ? "Spam" : "Ham");
      await expect(page.getByTestId("decision-score")).toHaveText(signed(expected.score));
      await expect(page.getByTestId("terms-recognised")).toHaveText(String(expected.terms_recognised));
    });
  }

  test("really sends the text to the backend, and shows its response", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Email text").fill(SPAM_EMAIL);
    const [response] = await Promise.all([
      page.waitForResponse(`${API}/api/classify`),
      page.getByRole("button", { name: "Classify", exact: true }).click(),
    ]);
    expect(response.status()).toBe(200);
    expect(response.request().postDataJSON()).toEqual({ text: SPAM_EMAIL });
    const body = await response.json();
    expect(body.confidence).toBeNull();
    await expect(page.getByTestId("decision-score")).toHaveText(signed(body.score));
  });

  test("shows the influential words and contributions from the API", async ({ page, request }) => {
    const { explanation } = await apiClassify(request, SPAM_EMAIL);
    await classify(page, SPAM_EMAIL);

    const spamList = page.getByRole("region", { name: "Pushed towards spam" });
    const hamList = page.getByRole("region", { name: "Pushed towards ham" });
    await expect(spamList.getByRole("listitem")).toHaveCount(explanation.spam_terms.length);
    await expect(hamList.getByRole("listitem")).toHaveCount(explanation.ham_terms.length);

    const first = explanation.spam_terms[0];
    await expect(spamList.getByRole("listitem").first()).toContainText(first.term);
    await expect(spamList.getByRole("listitem").first()).toContainText(signed(first.contribution));
    await expect(page.getByText(explanation.note)).toBeVisible();
  });

  test("shows the parts of the score, which add up to the decision score", async ({ page, request }) => {
    const { score, explanation } = await apiClassify(request, HAM_EMAIL);
    const total =
      explanation.intercept +
      explanation.other_terms_total +
      [...explanation.spam_terms, ...explanation.ham_terms].reduce((sum: number, term: { contribution: number }) => sum + term.contribution, 0);
    expect(total).toBeCloseTo(score, 3);

    await classify(page, HAM_EMAIL);
    const table = page.getByRole("table", { name: "How the decision score adds up" });
    await expect(table.getByRole("row", { name: /starting score/ })).toContainText(signed(explanation.intercept));
    await expect(table.getByRole("row", { name: /Decision score/ })).toContainText(signed(score));
  });

  test("shows no percentage or confidence value, and labels the decision score", async ({ page }) => {
    await classify(page, SPAM_EMAIL);
    const result = page.getByRole("region", { name: "Result" });
    await expect(page.getByTestId("decision-score").locator("..")).toContainText("Decision score");
    await expect(result.getByText(/It isn't a probability/)).toBeVisible();
    const text = await result.innerText();
    expect(text).not.toContain("%");
    expect(text).not.toMatch(/\bconfidence\b/i);
  });

  test("shows the caution below five recognised words, without changing the prediction", async ({ page, request }) => {
    const shortText = "free prize";
    const expected = await apiClassify(request, shortText);
    expect(expected.terms_recognised).toBeLessThan(5);

    await classify(page, shortText);
    await expect(page.getByText(`Only ${expected.terms_recognised} recognised words`)).toBeVisible();
    await expect(page.getByText(/a display warning, not a measured reliability boundary/)).toBeVisible();
    await expect(page.getByTestId("prediction-label")).toHaveText(expected.label === "spam" ? "Spam" : "Ham");
    await expect(page.getByTestId("decision-score")).toHaveText(signed(expected.score));
  });

  test("shows no caution for a message with enough recognised words", async ({ page, request }) => {
    const expected = await apiClassify(request, SPAM_EMAIL);
    expect(expected.terms_recognised).toBeGreaterThanOrEqual(5);
    await classify(page, SPAM_EMAIL);
    await expect(page.getByTestId("prediction-label")).toBeVisible();
    await expect(page.getByTestId("terms-recognised")).toHaveText(String(expected.terms_recognised));
    await expect(page.getByText(/a display warning/)).toHaveCount(0);
  });
});

test.describe("Validation and errors, from the real backend", () => {
  test("Classify is disabled for empty and whitespace-only text", async ({ page }) => {
    await page.goto("/");
    const button = page.getByRole("button", { name: "Classify", exact: true });
    await expect(button).toBeDisabled();
    await page.getByLabel("Email text").fill("   \n  ");
    await expect(button).toBeDisabled();
    await page.getByLabel("Email text").fill("hello");
    await expect(button).toBeEnabled();
  });

  test("text at exactly the limit is accepted", async ({ page }) => {
    await classify(page, "free prize ".repeat(2000).slice(0, 20_000));
    await expect(page.getByTestId("prediction-label")).toBeVisible();
    await expect(page.getByText("20,000 of 20,000 characters")).toBeVisible();
  });

  test("one character over the limit shows a warning, and the server's refusal", async ({ page }) => {
    await classify(page, "free prize ".repeat(2000).slice(0, 20_001));
    await expect(page.getByText(/1 over the limit/)).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("longer than the 20,000 character limit");
    await expect(page.getByTestId("prediction-label")).toHaveCount(0);
  });

  test("a body over the size limit shows the server's error, not a network failure", async ({ page }) => {
    await classify(page, "a".repeat(300_000));
    await expect(page.getByRole("alert")).toContainText("The request is too large");
    await expect(page.getByRole("alert")).not.toContainText("can't be reached");
  });

  test("text with no usable words shows the server's explanation", async ({ page }) => {
    await classify(page, "... !!! ???");
    await expect(page.getByRole("alert")).toContainText("no words of two or more characters");
    await expect(page.getByTestId("prediction-label")).toHaveCount(0);
  });

  test("text with no recognised words shows the server's explanation", async ({ page }) => {
    await classify(page, "zzqxv qwxzz vvqzx");
    await expect(page.getByRole("alert")).toContainText("in the model's vocabulary");
    await expect(page.getByTestId("prediction-label")).toHaveCount(0);
  });

  test("shows a loading state during a slow request", async ({ page }) => {
    await page.route(`${API}/api/classify`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.continue();
    });
    await classify(page, SPAM_EMAIL);
    await expect(page.getByText("Classifying your text…")).toBeVisible();
    await expect(page.getByRole("button", { name: "Classifying…" })).toBeDisabled();
    await expect(page.getByTestId("prediction-label")).toBeVisible();
    await expect(page.getByText("Classifying your text…")).toHaveCount(0);
  });

  test("marks a result as out of date when the text changes, and Clear resets the page", async ({ page }) => {
    await classify(page, SPAM_EMAIL);
    await expect(page.getByTestId("prediction-label")).toBeVisible();
    await page.getByLabel("Email text").fill(`${SPAM_EMAIL} more`);
    await expect(page.getByText("The text has changed since this result")).toBeVisible();

    await page.getByRole("button", { name: "Clear" }).click();
    await expect(page.getByLabel("Email text")).toHaveValue("");
    await expect(page.getByTestId("prediction-label")).toHaveCount(0);
  });

  test("keeps the text out of the URL and browser storage", async ({ page }) => {
    const marker = "PrivateMarkerWordInEmail";
    await classify(page, `${SPAM_EMAIL} ${marker}`);
    await expect(page.getByTestId("prediction-label")).toBeVisible();

    expect(page.url()).not.toContain(marker);
    const stored = await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }));
    expect(stored).not.toContain(marker);
    await expect(page.getByRole("region", { name: "Result" })).not.toContainText(marker);
  });
});

test.describe("Saved results match the report files", () => {
  test("the limit shown matches the API's", async ({ page, request }) => {
    const info = await (await request.get(`${API}/api/model-info`)).json();
    await page.goto("/");
    await expect(page.getByText(`0 of ${count(info.max_input_characters)} characters`)).toBeVisible();
  });

  test("the Models page shows the final test results", async ({ page }) => {
    const test_ = report("final_test_evaluation.json");
    await page.goto("/models");

    const metrics = test_.overall_metrics;
    await expect(page.getByText(metrics.f1_spam.toFixed(4), { exact: true }).first()).toBeVisible();
    await expect(page.getByText(metrics.precision_spam.toFixed(4), { exact: true }).first()).toBeVisible();
    await expect(page.getByText(metrics.recall_spam.toFixed(4), { exact: true }).first()).toBeVisible();
    await expect(page.getByText(test_.roc_auc.toFixed(4), { exact: true }).first()).toBeVisible();

    const matrix = page.getByRole("table", { name: /Test split/ });
    await expect(matrix.getByRole("row", { name: /^Ham/ })).toContainText(count(metrics.true_ham));
    await expect(matrix.getByRole("row", { name: /^Ham/ })).toContainText(count(metrics.ham_flagged_as_spam));
    await expect(matrix.getByRole("row", { name: /^Spam/ })).toContainText(count(metrics.spam_missed));
  });

  test("the Models page shows every similarity band, with sample counts", async ({ page }) => {
    const bands = report("final_test_evaluation.json").metrics_by_similarity_band;
    await page.goto("/models");
    const region = page.getByRole("region", { name: "Test results by similarity to training data" });
    const rows = region.locator("tbody tr");
    await expect(rows).toHaveCount(Object.keys(bands).length);
    let position = 0;
    for (const band of Object.values(bands) as { rows: number; metrics: { f1_spam: number } }[]) {
      await expect(rows.nth(position)).toContainText(count(band.rows));
      await expect(rows.nth(position)).toContainText(band.metrics.f1_spam.toFixed(4));
      position += 1;
    }
  });

  test("the Models page shows all 18 comparison runs, and marks the selected one", async ({ page }) => {
    const comparison = report("model_comparison.json");
    const runs = Object.values(comparison.runs).flatMap((run) => (run as { results: { metrics: { f1_spam: number } }[] }).results);
    expect(runs).toHaveLength(18);

    await page.goto("/models");
    const rows = page.getByRole("region", { name: "All model comparison runs" }).locator("tbody tr");
    await expect(rows).toHaveCount(18);
    for (const [position, run] of runs.entries()) {
      await expect(rows.nth(position)).toContainText(run.metrics.f1_spam.toFixed(4));
    }
    const selected = page.getByRole("region", { name: "All model comparison runs" }).locator('tr[data-highlight="true"]');
    await expect(selected).toHaveCount(1);
    await expect(selected).toContainText("Linear SVM");
    await expect(selected).toContainText(comparison.selected.metrics.f1_spam.toFixed(4));
  });

  test("the Models page shows the cross-style results and the warning about them", async ({ page }) => {
    const leakage = report("source_leakage.json");
    await page.goto("/models");
    await expect(page.getByText(leakage.interpretation_note)).toBeVisible();
    const f1 = leakage.cross_style.train_digits_only.validation_by_style.placeholder_only.metrics.f1_spam;
    await expect(page.getByRole("region", { name: "Cross-style results" })).toContainText(f1.toFixed(4));
  });

  test("the Dataset page shows the verified statistics", async ({ page }) => {
    const inspection = report("dataset_inspection.json");
    const preparation = report("data_preparation.json");
    await page.goto("/dataset");

    await expect(page.getByText(count(inspection.structure.rows), { exact: true }).first()).toBeVisible();
    await expect(page.getByText(`Ham: ${count(inspection.labels.Ham.rows)} rows`)).toBeVisible();
    await expect(page.getByText(`Spam: ${count(inspection.labels.Spam.rows)} rows`)).toBeVisible();
    await expect(page.getByText(inspection.file.sha256)).toBeVisible();

    const duplicates = page.getByRole("region", { name: "Duplicate checks" });
    await expect(duplicates).toContainText(count(inspection.duplicates.normalised_duplicate_rows));

    const cleaning = page.getByRole("region", { name: "Cleaning rules" });
    await expect(cleaning).toContainText(count(preparation.cleaning.removed_duplicates));
    await expect(page.getByText(`${count(preparation.cleaning.rows_kept)} kept`)).toBeVisible();

    const splits = page.getByRole("region", { name: "Data splits" });
    await expect(splits).toContainText(count(preparation.split.rows.test.total));
  });

  test("the Dataset page says the licence isn't verified", async ({ page }) => {
    await page.goto("/dataset");
    await expect(page.getByText("Licence: Not verified")).toBeVisible();
    await expect(page.getByTestId("licence")).toHaveText("Not verified");
  });

  test("the pages call the real results endpoints", async ({ page }) => {
    const models = page.waitForResponse(`${API}/api/results/models`);
    await page.goto("/models");
    expect((await models).status()).toBe(200);

    const dataset = page.waitForResponse(`${API}/api/results/dataset`);
    await page.getByRole("link", { name: "Dataset" }).click();
    expect((await dataset).status()).toBe(200);
  });
});

test.describe("Responsive layout", () => {
  for (const width of [360, 768, 1280]) {
    test.describe(`at ${width} pixels wide`, () => {
      test.use({ viewport: { width, height: 800 } });

      async function expectNoPageScroll(page: Page) {
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        expect(overflow).toBeLessThanOrEqual(0);
      }

      test("the classifier and its result fit", async ({ page }) => {
        await classify(page, SPAM_EMAIL);
        await expect(page.getByTestId("prediction-label")).toBeVisible();
        await expectNoPageScroll(page);
        for (const name of ["Classify", "Models", "Dataset"]) {
          await expect(page.getByRole("link", { name, exact: true })).toBeVisible();
        }
        await expect(page.getByLabel("Email text")).toBeVisible();
        await page.screenshot({ path: join(SCREENSHOTS, `classifier-${width}.png`), fullPage: true });
      });

      test("the Models page fits, with wide tables scrolling on their own", async ({ page }) => {
        await page.goto("/models");
        await expect(page.getByRole("heading", { name: "Final test results" })).toBeVisible();
        await expectNoPageScroll(page);
        await page.screenshot({ path: join(SCREENSHOTS, `models-${width}.png`), fullPage: true });
      });

      test("the Dataset page fits", async ({ page }) => {
        await page.goto("/dataset");
        await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
        await expectNoPageScroll(page);
        await page.screenshot({ path: join(SCREENSHOTS, `dataset-${width}.png`), fullPage: true });
      });

      test("no text is cut off, and wide tables say they scroll", async ({ page }) => {
        for (const path of ["/models", "/dataset"]) {
          await page.goto(path);
          await expect(page.locator("main section").first()).toBeVisible();

          // Text outside a table must fit within the page's width, not just avoid scrolling it.
          const clipped = await page.evaluate(() =>
            [...document.querySelectorAll("main p, main li, main dt, main dd, main h1, main h2, main h3")]
              .filter((element) => !element.closest("table"))
              .filter((element) => {
                const { left, right } = element.getBoundingClientRect();
                return left < 0 || right > window.innerWidth;
              })
              .map((element) => element.textContent?.slice(0, 40)),
          );
          expect(clipped).toEqual([]);

          // Every region that overflows must say so, and every hint must be true.
          const regions = page.locator('main [role="region"]');
          for (let position = 0; position < (await regions.count()); position += 1) {
            const region = regions.nth(position);
            const overflows = await region.evaluate((element) => element.scrollWidth > element.clientWidth);
            const hint = region.locator("xpath=..").getByTestId("scroll-hint");
            await expect(hint).toHaveCount(overflows ? 1 : 0);
          }
        }
      });

      test("error messages fit", async ({ page }) => {
        await classify(page, "... !!! ???");
        await expect(page.getByRole("alert")).toBeVisible();
        await expectNoPageScroll(page);
      });
    });
  }
});

test.describe("Accessibility", () => {
  // AxeBuilder has its own copy of Playwright's types, so the same Page needs a cast here.
  const axe = (page: Page) =>
    new AxeBuilder({ page: page as unknown as ConstructorParameters<typeof AxeBuilder>[0]["page"] }).withTags([
      "wcag2a",
      "wcag2aa",
      "wcag21a",
      "wcag21aa",
    ]);

  for (const colorScheme of ["light", "dark"] as const) {
    test.describe(`in ${colorScheme} mode`, () => {
      test.use({ colorScheme });

      test("the classifier with a result has no automatically detectable problems", async ({ page }) => {
        await classify(page, "free prize");
        await expect(page.getByTestId("prediction-label")).toBeVisible();
        expect((await axe(page).analyze()).violations).toEqual([]);
        await page.screenshot({ path: join(SCREENSHOTS, `classifier-short-message-${colorScheme}.png`), fullPage: true });
      });

      test("the Models page has no automatically detectable problems", async ({ page }) => {
        await page.goto("/models");
        await expect(page.getByRole("heading", { name: "Final test results" })).toBeVisible();
        expect((await axe(page).analyze()).violations).toEqual([]);
      });

      test("the Dataset page has no automatically detectable problems", async ({ page }) => {
        await page.goto("/dataset");
        await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
        expect((await axe(page).analyze()).violations).toEqual([]);
      });

      test("an error message has no automatically detectable problems", async ({ page }) => {
        await classify(page, "... !!! ???");
        await expect(page.getByRole("alert")).toBeVisible();
        expect((await axe(page).analyze()).violations).toEqual([]);
      });
    });
  }

  test("the classifier can be used with only a keyboard", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Email text").focus();
    await page.keyboard.type("Free prize, click here to claim your money today");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("button", { name: "Classify", exact: true })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("prediction-label")).toBeVisible();
  });

  test("wide tables can be reached and scrolled with a keyboard", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto("/models");
    const region = page.getByRole("region", { name: "All model comparison runs" });
    await expect(region).toBeVisible();
    await expect(region).toHaveAttribute("tabindex", "0");
    const scrollable = await region.evaluate((element) => element.scrollWidth > element.clientWidth);
    expect(scrollable).toBe(true);
  });
});
