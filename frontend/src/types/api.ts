/** Response shapes from the backend, matching backend/app/schemas. */

export type Label = "spam" | "ham";

export interface TermContribution {
  term: string;
  contribution: number;
}

export interface Explanation {
  spam_terms: TermContribution[];
  ham_terms: TermContribution[];
  other_terms_total: number;
  intercept: number;
  note: string;
}

export interface ClassifyResponse {
  label: Label;
  /** Always null: a Linear SVM doesn't provide a meaningful probability. */
  confidence: null;
  /** The raw SVM decision score. It isn't a probability. */
  score: number;
  model_version: string;
  text_length: number;
  terms_recognised: number;
  explanation: Explanation;
}

export interface HealthResponse {
  status: "ok" | "unavailable";
  model_loaded: boolean;
  model_version: string | null;
  detail: string | null;
}

export interface Metrics {
  accuracy: number;
  precision_spam: number;
  recall_spam: number;
  f1_spam: number;
  ham_flagged_as_spam: number;
  spam_missed: number;
  true_ham: number;
  true_spam: number;
}

export interface Latency {
  rows: number;
  median_ms: number;
  p95_ms: number;
}

export type Setting = Record<string, number>;

export interface FinalModel {
  model_version: string;
  model: string;
  setting: Setting;
  features: string;
  vocabulary_size: number;
  removed_word_count: number;
  training_rows: number;
  file_sha256: string;
  model_content_sha256: string;
}

export interface SelectedRun {
  features: string;
  model: string;
  setting: Setting;
  metrics: Metrics;
  roc_auc: number;
}

export interface Selection {
  split_used: string;
  rule: { f1_tie_margin: number; steps: string[] };
  selected: SelectedRun;
}

export interface ComparisonRun extends SelectedRun {
  converged: boolean;
  classifier_fit_seconds: number;
  single_message_latency: Latency;
}

export interface FeatureSetRun {
  features: string;
  train_rows: number;
  validation_rows: number;
  vocabulary_size: number;
  vectorizer_fit_seconds: number;
  peak_memory_gb: number | null;
}

export interface SimilarityBand {
  band: string;
  rows: number;
  share_of_rows: number;
  spam_share: number | null;
  metrics: Metrics | null;
}

export interface TestEvaluation {
  split: string;
  rows: number;
  spam_share: number;
  overall_metrics: Metrics;
  roc_auc: number;
  class_results: {
    Ham: { rows: number; precision: number | null; recall: number | null; share_wrongly_flagged_as_spam: number | null };
    Spam: { rows: number; precision: number | null; recall: number | null; share_missed: number | null };
  };
  similarity_method: string;
  similarity_bands: SimilarityBand[];
  single_message_latency: Latency;
  report_matches_saved_model: boolean;
}

export interface ValidationEvaluation {
  split: string;
  rows: number;
  overall_metrics: Metrics;
  roc_auc: number;
}

export interface MarkerRemovalRun {
  name: string;
  words_removed: number;
  vocabulary_size: number;
  metrics: Metrics;
  roc_auc: number;
}

export interface StyleScore {
  scored_on: string;
  rows: number;
  spam_share: number;
  metrics: Metrics;
  roc_auc: number;
}

export interface CrossStyleRun {
  name: string;
  training_style: string;
  training_rows: number;
  words_removed: number;
  scores: StyleScore[];
}

export interface SourceLeakage {
  split_used: string;
  interpretation_note: string;
  marker_removal: MarkerRemovalRun[];
  cross_style: CrossStyleRun[];
  removal_decision: {
    candidate: string;
    validation_f1_drop: number;
    f1_margin: number;
    cross_style_f1_change: { digits_to_placeholder: number; placeholder_to_digits: number };
    adopt: boolean;
  };
}

export interface ModelsResults {
  final_model: FinalModel;
  selection: Selection;
  feature_sets: FeatureSetRun[];
  comparison_runs: ComparisonRun[];
  validation_evaluation: ValidationEvaluation;
  test_evaluation: TestEvaluation;
  source_leakage: SourceLeakage;
  limitations: string[];
}

export interface LengthSummary {
  rows: number;
  min: number;
  median: number;
  p95: number;
  p99: number;
  max: number;
  mean: number;
}

export interface DatasetResults {
  source: {
    reported_source_url: string;
    licence: string;
    original_sources: string;
    label_accuracy: string;
    note: string;
  };
  file: { name: string; format: string; size_bytes: number; sha256: string };
  structure: { rows: number; columns: string[] };
  labels: { Ham: { rows: number; share: number }; Spam: { rows: number; share: number } };
  missing_values: Record<string, number>;
  blank_text: { empty_rows: Record<string, number>; whitespace_only_rows: number };
  duplicates: {
    identical_rows: number;
    exact_duplicate_text_rows: number;
    exact_conflicting_labels: { texts: number; rows: number };
    normalised_duplicate_rows: number;
    normalised_conflicting_labels: { texts: number; rows: number };
  };
  lengths: {
    by_label: { Ham: LengthSummary; Spam: LengthSummary };
    rows_under_20_chars: Record<string, number>;
    rows_over_chars: Record<string, number>;
  };
  word_shares: { word: string; shares: { Ham: number; Spam: number } }[];
  text_format: {
    rows_analysed: number;
    number_styles: { style: string; ham_rows: number; spam_rows: number; spaced_punctuation_share: number }[];
    flags: { name: string; ham_rows: number; ham_share: number; spam_rows: number; spam_share: number }[];
  };
  preparation: {
    cleaning: {
      rows_in: number;
      removed_blank: number;
      removed_no_word_tokens: number;
      removed_conflicting_labels: number;
      conflicting_label_texts: number;
      removed_duplicates: number;
      rows_kept: number;
    };
    random_seed: number;
    validation_share: number;
    test_share: number;
    stratified_by: string;
    splits: { split: string; total: number; ham: number; spam: number; spam_share: number }[];
    preprocessed_texts_shared_between_splits: number;
  };
}
