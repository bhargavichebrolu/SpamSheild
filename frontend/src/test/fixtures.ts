/**
 * Made-up API responses, for automated tests only. The application never imports this file,
 * and a test confirms it. The numbers are deliberately unlike the real results.
 */

import type { ClassifyResponse, DatasetResults, HealthResponse, Metrics, ModelsResults } from "../types/api";

export const HEALTHY: HealthResponse = { status: "ok", model_loaded: true, model_version: "test-version", detail: null };

export const SPAM_RESULT: ClassifyResponse = {
  label: "spam",
  confidence: null,
  score: 1.5,
  model_version: "test-version",
  text_length: 25,
  terms_recognised: 8,
  explanation: {
    spam_terms: [
      { term: "prize", contribution: 0.75 },
      { term: "free", contribution: 0.25 },
    ],
    ham_terms: [{ term: "escapenumber", contribution: -0.5 }],
    other_terms_total: 0.25,
    intercept: 0.75,
    note: "Test note: these terms do not prove why.",
  },
};

export const HAM_RESULT: ClassifyResponse = {
  ...SPAM_RESULT,
  label: "ham",
  score: -2.25,
  explanation: {
    ...SPAM_RESULT.explanation,
    spam_terms: [],
    ham_terms: [{ term: "meeting", contribution: -3 }],
    other_terms_total: 0,
  },
};

const metrics = (f1: number, flagged: number, missed: number): Metrics => ({
  accuracy: 0.5,
  precision_spam: 0.25,
  recall_spam: 0.125,
  f1_spam: f1,
  ham_flagged_as_spam: flagged,
  spam_missed: missed,
  true_ham: 70,
  true_spam: 60,
});

const SELECTED_METRICS = metrics(0.6, 10, 30);
const OTHER_METRICS = metrics(0.6125, 12, 20);

export const MODELS_RESULTS: ModelsResults = {
  final_model: {
    model_version: "test-version",
    model: "linear_svm",
    setting: { C: 3 },
    features: "word_1",
    vocabulary_size: 4321,
    removed_word_count: 7,
    training_rows: 1234,
    file_sha256: "file-hash",
    model_content_sha256: "content-hash",
  },
  selection: {
    split_used: "validation",
    rule: { f1_tie_margin: 0.05, steps: ["Test step one", "Test step two"] },
    selected: { features: "word_1", model: "linear_svm", setting: { C: 3 }, metrics: SELECTED_METRICS, roc_auc: 0.7 },
  },
  feature_sets: [
    { features: "word_1", train_rows: 1234, validation_rows: 321, vocabulary_size: 4321, vectorizer_fit_seconds: 1, peak_memory_gb: 1 },
  ],
  comparison_runs: [
    {
      features: "word_1",
      model: "linear_svm",
      setting: { C: 3 },
      converged: true,
      metrics: SELECTED_METRICS,
      roc_auc: 0.7,
      classifier_fit_seconds: 1,
      single_message_latency: { rows: 2, median_ms: 1, p95_ms: 2 },
    },
    {
      features: "word_1_2",
      model: "linear_svm",
      setting: { C: 3 },
      converged: true,
      metrics: OTHER_METRICS,
      roc_auc: 0.71,
      classifier_fit_seconds: 1,
      single_message_latency: { rows: 2, median_ms: 1, p95_ms: 2 },
    },
  ],
  validation_evaluation: { split: "validation", rows: 321, overall_metrics: SELECTED_METRICS, roc_auc: 0.7 },
  test_evaluation: {
    split: "test",
    rows: 432,
    spam_share: 0.4,
    overall_metrics: metrics(0.6375, 11, 22),
    roc_auc: 0.72,
    class_results: {
      Ham: { rows: 81, precision: 0.5, recall: 0.5, share_wrongly_flagged_as_spam: 0.5 },
      Spam: { rows: 82, precision: 0.5, recall: 0.5, share_missed: 0.5 },
    },
    similarity_method: "test method",
    similarity_bands: [
      { band: "0.00_to_0.80", rows: 111, share_of_rows: 0.25, spam_share: 0.5, metrics: metrics(0.55, 5, 6) },
      { band: "0.95_and_above", rows: 222, share_of_rows: 0.5, spam_share: 0.5, metrics: null },
    ],
    single_message_latency: { rows: 2, median_ms: 1, p95_ms: 2 },
    report_matches_saved_model: true,
  },
  source_leakage: {
    split_used: "train to fit, validation to score",
    interpretation_note: "Test note: not proof of generalisation.",
    marker_removal: [
      { name: "baseline_no_removal", words_removed: 0, vocabulary_size: 10, metrics: metrics(0.61, 1, 2), roc_auc: 0.7 },
      { name: "remove_style_300_and_ham_300", words_removed: 7, vocabulary_size: 9, metrics: metrics(0.59, 3, 4), roc_auc: 0.7 },
    ],
    cross_style: [
      {
        name: "train_digits_only",
        training_style: "digits_only",
        training_rows: 55,
        words_removed: 0,
        scores: [{ scored_on: "placeholder_only", rows: 44, spam_share: 0.5, metrics: metrics(0.45, 9, 8), roc_auc: 0.6 }],
      },
      {
        name: "train_placeholder_only_matched_size",
        training_style: "placeholder_only",
        training_rows: 55,
        words_removed: 0,
        scores: [{ scored_on: "digits_only", rows: 33, spam_share: 0.5, metrics: metrics(0.46, 7, 6), roc_auc: 0.6 }],
      },
    ],
    removal_decision: {
      candidate: "remove_style_300_and_ham_300",
      validation_f1_drop: 0.02,
      f1_margin: 0.05,
      cross_style_f1_change: { digits_to_placeholder: 0.01, placeholder_to_digits: 0.01 },
      adopt: true,
    },
  },
  limitations: ["Test limitation one", "Test limitation two"],
};

export const DATASET_RESULTS: DatasetResults = {
  source: {
    reported_source_url: "https://example.com/test-dataset",
    licence: "Not verified",
    original_sources: "Not verified",
    label_accuracy: "Not verified",
    note: "Test note: the raw dataset isn't included.",
  },
  file: { name: "test.csv", format: "CSV, UTF-8", size_bytes: 2097152, sha256: "test-sha" },
  structure: { rows: 7777, columns: ["label", "text"] },
  labels: { Ham: { rows: 5000, share: 0.625 }, Spam: { rows: 3000, share: 0.375 } },
  missing_values: { label: 1, text: 2 },
  blank_text: { empty_rows: { Ham: 3, Spam: 4 }, whitespace_only_rows: 0 },
  duplicates: {
    identical_rows: 11,
    exact_duplicate_text_rows: 12,
    exact_conflicting_labels: { texts: 13, rows: 14 },
    normalised_duplicate_rows: 15,
    normalised_conflicting_labels: { texts: 16, rows: 17 },
  },
  lengths: {
    by_label: {
      Ham: { rows: 21, min: 1, median: 22, p95: 23, p99: 24, max: 25, mean: 26.5 },
      Spam: { rows: 31, min: 1, median: 32, p95: 33, p99: 34, max: 35, mean: 36.5 },
    },
    rows_under_20_chars: { Ham: 41, Spam: 42 },
    rows_over_chars: { "100000": 43, "20000": 44 },
  },
  word_shares: [{ word: "testword", shares: { Ham: 0.125, Spam: 0.25 } }],
  text_format: {
    rows_analysed: 7000,
    number_styles: [{ style: "digits_only", ham_rows: 51, spam_rows: 52, spaced_punctuation_share: 0.75 }],
    flags: [{ name: "has_digit", ham_rows: 61, ham_share: 0.125, spam_rows: 62, spam_share: 0.25 }],
  },
  preparation: {
    cleaning: {
      rows_in: 7777,
      removed_blank: 71,
      removed_no_word_tokens: 72,
      removed_conflicting_labels: 73,
      conflicting_label_texts: 74,
      removed_duplicates: 75,
      rows_kept: 7000,
    },
    random_seed: 99,
    validation_share: 0.1,
    test_share: 0.1,
    stratified_by: "label",
    splits: [{ split: "train", total: 81, ham: 82, spam: 83, spam_share: 0.5 }],
    preprocessed_texts_shared_between_splits: 0,
  },
};
