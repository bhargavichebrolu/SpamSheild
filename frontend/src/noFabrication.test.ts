/**
 * Application code must get every result from the API. These checks read the source files
 * themselves, to catch hard-coded metrics, invented values or test data used by the app.
 */

import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const SRC = dirname(fileURLToPath(import.meta.url));

function appFiles(directory: string = SRC): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      return entry.name === "test" ? [] : appFiles(path);
    }
    return /\.(ts|tsx)$/.test(entry.name) && !/\.test\.(ts|tsx)$/.test(entry.name) ? [path] : [];
  });
}

const files = appFiles().map((path) => ({
  path: relative(SRC, path),
  source: readFileSync(path, "utf-8"),
}));

describe("no fabricated results in application code", () => {
  it("finds the application's files", () => {
    expect(files.map(({ path }) => path.replaceAll("\\", "/"))).toEqual(
      expect.arrayContaining([
        "App.tsx",
        "services/api.ts",
        "pages/HomePage.tsx",
        "pages/ClassifierPage.tsx",
        "pages/ModelsPage.tsx",
        "pages/DatasetPage.tsx",
        "components/Charts.tsx",
        "utils/results.ts",
      ]),
    );
  });

  it("has no decimal metric written into the code", () => {
    for (const { path, source } of files) {
      expect(source.match(/\b0\.\d{2,}\b/g) ?? [], path).toEqual([]);
    }
  });

  it("has no real result counts written into the code", () => {
    const realCounts = ["193852", "193,852", "190817", "190,817", "19082", "19,082", "152653", "152,653", "242607", "242,607"];
    for (const { path, source } of files) {
      for (const value of realCounts) {
        expect(source.includes(value), `${value} in ${path}`).toBe(false);
      }
    }
  });

  it("creates no random values", () => {
    for (const { path, source } of files) {
      expect(source.includes("Math.random"), path).toBe(false);
    }
  });

  it("never imports test data or test helpers", () => {
    for (const { path, source } of files) {
      expect(source, path).not.toMatch(/from\s+["'][^"']*(test\/|fixtures|helpers)/);
    }
  });

  it("calls the network only from the API service", () => {
    for (const { path, source } of files) {
      if (path.replaceAll("\\", "/") !== "services/api.ts") {
        expect(source, path).not.toMatch(/\bfetch\(|XMLHttpRequest|axios/);
      }
    }
  });

  it("doesn't use browser storage for anything", () => {
    for (const { path, source } of files) {
      expect(source, path).not.toMatch(/localStorage|sessionStorage|indexedDB|document\.cookie/);
    }
  });

  it("doesn't use the API's confidence field, or show a percentage from a score", () => {
    const prediction = files.filter(({ path }) => /PredictionResult|TermContributions|ClassifierPage/.test(path));
    expect(prediction).toHaveLength(3);
    for (const { path, source } of prediction) {
      expect(source, path).not.toMatch(/\.confidence\b/);
      expect(source, path).not.toMatch(/share\(|\* 100}%`|toFixed\(\d\)}%/.source.replace("\\* 100}%`|", ""));
    }
  });
});
