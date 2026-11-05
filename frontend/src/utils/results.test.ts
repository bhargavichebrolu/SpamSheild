import { describe, expect, it } from "vitest";

import { DATASET_RESULTS, MODELS_RESULTS } from "../test/fixtures";
import {
  bestRunPerCombination,
  crossStyleBars,
  errorsByBand,
  errorShareOfFirstBand,
  lowestCrossStyleF1,
  noCloseMatchF1,
  numberStyleRows,
  wordShareRows,
} from "./results";

describe("results helpers", () => {
  it("finds the lowest score across different text styles only", () => {
    expect(lowestCrossStyleF1(MODELS_RESULTS)).toBe(0.45);
  });

  it("ignores same-style and neither-style scores", () => {
    const score = MODELS_RESULTS.source_leakage.cross_style[0]!.scores[0]!;
    const results = {
      ...MODELS_RESULTS,
      source_leakage: {
        ...MODELS_RESULTS.source_leakage,
        cross_style: [
          {
            ...MODELS_RESULTS.source_leakage.cross_style[0]!,
            scores: [
              { ...score, scored_on: "digits_only" },
              { ...score, scored_on: "neither" },
            ],
          },
        ],
      },
    };
    expect(lowestCrossStyleF1(results)).toBeNull();
  });

  it("reads the no-close-match score from the first band", () => {
    expect(noCloseMatchF1(MODELS_RESULTS)).toBe(0.55);
  });

  it("adds up errors by band, treating an empty band as zero", () => {
    expect(errorsByBand(MODELS_RESULTS)).toEqual([
      { band: "0.00_to_0.80", rows: 111, flagged: 5, missed: 6 },
      { band: "0.95_and_above", rows: 222, flagged: 0, missed: 0 },
    ]);
    expect(errorShareOfFirstBand(MODELS_RESULTS)).toEqual({ first: 11, total: 11 });
  });

  it("orders style bars from highest to lowest, using only the full-size runs", () => {
    expect(crossStyleBars(MODELS_RESULTS)).toEqual([
      { label: "Trained on digit style, scored on placeholder style", value: 0.45, seriesKey: "other" },
    ]);
  });

  it("gives one run per model and features, with the selected one marked", () => {
    const rows = bestRunPerCombination(MODELS_RESULTS);
    expect(rows).toHaveLength(2);
    expect(rows.filter(({ selected }) => selected)).toHaveLength(1);
    expect(rows.find(({ selected }) => selected)).toMatchObject({ flagged: 10, missed: 30 });
  });

  it("orders those runs by total errors, with the fewest first", () => {
    const totals = bestRunPerCombination(MODELS_RESULTS).map(({ flagged, missed }) => flagged + missed);
    expect(totals).toEqual([...totals].sort((first, second) => first - second));
  });

  it("keeps the selected run even if another setting has a higher F1", () => {
    const [selected, other] = MODELS_RESULTS.comparison_runs;
    const sameCombination = { ...other!, features: selected!.features, setting: { C: 9 } };
    const rows = bestRunPerCombination({ ...MODELS_RESULTS, comparison_runs: [sameCombination, selected!] });
    expect(rows).toHaveLength(1);
    expect(rows[0]?.selected).toBe(true);
  });

  it("uses the highest F1 for a combination without the selected run", () => {
    const other = MODELS_RESULTS.comparison_runs[1]!;
    const better = { ...other, setting: { C: 9 }, metrics: { ...other.metrics, f1_spam: 0.9, spam_missed: 1 } };
    const rows = bestRunPerCombination({ ...MODELS_RESULTS, comparison_runs: [other, better] });
    expect(rows[0]?.missed).toBe(1);
  });

  it("builds dataset chart rows from the API's values", () => {
    expect(numberStyleRows(DATASET_RESULTS)).toEqual([{ label: "Digit style", values: { ham: 51, spam: 52 } }]);
    expect(wordShareRows(DATASET_RESULTS)).toEqual([{ label: "testword", values: { ham: 0.125, spam: 0.25 } }]);
  });
});
