/**
 * Pick values out of the API's saved results, for charts and headline numbers. These only
 * select and add up what the API returned. They don't estimate or create anything.
 */

import type { ComparisonRun, DatasetResults, ModelsResults, StyleScore } from "../types/api";
import { featureName, modelName, settingText, styleName } from "./format";

/** The F1 scores where a model was scored on the other number style, from every run. */
function crossStyleScores(results: ModelsResults): StyleScore[] {
  return results.source_leakage.cross_style.flatMap((run) =>
    run.scores.filter(({ scored_on: scoredOn }) => scoredOn !== "neither" && scoredOn !== run.training_style),
  );
}

export function lowestCrossStyleF1(results: ModelsResults): number | null {
  const scores = crossStyleScores(results).map(({ metrics }) => metrics.f1_spam);
  return scores.length > 0 ? Math.min(...scores) : null;
}

export function noCloseMatchF1(results: ModelsResults): number | null {
  return results.test_evaluation.similarity_bands[0]?.metrics?.f1_spam ?? null;
}

export function errorsByBand(results: ModelsResults) {
  return results.test_evaluation.similarity_bands.map((band) => ({
    band: band.band,
    rows: band.rows,
    flagged: band.metrics?.ham_flagged_as_spam ?? 0,
    missed: band.metrics?.spam_missed ?? 0,
  }));
}

/** Errors in the first band, which holds messages with no close match in training. */
export function errorShareOfFirstBand(results: ModelsResults): { first: number; total: number } {
  const errors = errorsByBand(results).map(({ flagged, missed }) => flagged + missed);
  return { first: errors[0] ?? 0, total: errors.reduce((sum, value) => sum + value, 0) };
}

/** Same-style and other-style scores for the two full-size runs, with no words removed. */
export function crossStyleBars(results: ModelsResults) {
  return results.source_leakage.cross_style
    .filter(({ name }) => name === "train_digits_only" || name === "train_placeholder_only")
    .flatMap((run) =>
      run.scores
        .filter(({ scored_on: scoredOn }) => scoredOn !== "neither")
        .map((score) => ({
          label: `Trained on ${styleName(run.training_style).toLowerCase()}, scored on ${styleName(score.scored_on).toLowerCase()}`,
          value: score.metrics.f1_spam,
          seriesKey: score.scored_on === run.training_style ? "same" : "other",
        })),
    )
    .sort((first, second) => second.value - first.value);
}

const isSelected = (run: ComparisonRun, results: ModelsResults): boolean => {
  const { selected } = results.selection;
  return (
    run.model === selected.model &&
    run.features === selected.features &&
    settingText(run.setting) === settingText(selected.setting)
  );
};

/**
 * One run for each combination of model and features: the selected run where it belongs, and
 * otherwise that combination's highest F1. Ordered by total errors, with the fewest first.
 */
export function bestRunPerCombination(results: ModelsResults) {
  const groups = new Map<string, ComparisonRun>();
  for (const run of results.comparison_runs) {
    const key = `${run.model}|${run.features}`;
    const current = groups.get(key);
    if (!current) {
      groups.set(key, run);
    } else if (!isSelected(current, results) && (isSelected(run, results) || run.metrics.f1_spam > current.metrics.f1_spam)) {
      groups.set(key, run);
    }
  }
  return [...groups.values()]
    .map((run) => ({
      label: modelName(run.model),
      detail: `${featureName(run.features).toLowerCase()}, ${settingText(run.setting)}`,
      flagged: run.metrics.ham_flagged_as_spam,
      missed: run.metrics.spam_missed,
      selected: isSelected(run, results),
    }))
    .sort((first, second) => first.flagged + first.missed - (second.flagged + second.missed));
}

export function numberStyleRows(dataset: DatasetResults) {
  return dataset.text_format.number_styles.map((style) => ({
    label: styleName(style.style),
    values: { ham: style.ham_rows, spam: style.spam_rows },
  }));
}

export function wordShareRows(dataset: DatasetResults) {
  return dataset.word_shares.map(({ word, shares }) => ({
    label: word,
    values: { ham: shares.Ham, spam: shares.Spam },
  }));
}
