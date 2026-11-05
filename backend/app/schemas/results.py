"""Response shapes for the saved results.

Pydantic drops any field not named here, so these schemas are also an allowlist: if a
report ever gained something else, such as message text, it wouldn't reach the website.
"""

from __future__ import annotations

from pydantic import BaseModel


class Metrics(BaseModel):
    accuracy: float
    precision_spam: float
    recall_spam: float
    f1_spam: float
    ham_flagged_as_spam: int
    spam_missed: int
    true_ham: int
    true_spam: int


class Latency(BaseModel):
    rows: int
    median_ms: float
    p95_ms: float


class FinalModel(BaseModel):
    model_version: str
    model: str
    setting: dict[str, float]
    features: str
    vocabulary_size: int
    removed_word_count: int
    training_rows: int
    file_sha256: str
    model_content_sha256: str


class SelectionRule(BaseModel):
    f1_tie_margin: float
    steps: list[str]


class SelectedRun(BaseModel):
    features: str
    model: str
    setting: dict[str, float]
    metrics: Metrics
    roc_auc: float


class Selection(BaseModel):
    split_used: str
    rule: SelectionRule
    selected: SelectedRun


class ComparisonRun(BaseModel):
    features: str
    model: str
    setting: dict[str, float]
    converged: bool
    metrics: Metrics
    roc_auc: float
    classifier_fit_seconds: float
    single_message_latency: Latency


class FeatureSetRun(BaseModel):
    features: str
    train_rows: int
    validation_rows: int
    vocabulary_size: int
    vectorizer_fit_seconds: float
    peak_memory_gb: float | None


class HamClassResult(BaseModel):
    rows: int
    precision: float | None
    recall: float | None
    share_wrongly_flagged_as_spam: float | None


class SpamClassResult(BaseModel):
    rows: int
    precision: float | None
    recall: float | None
    share_missed: float | None


class ClassResults(BaseModel):
    Ham: HamClassResult
    Spam: SpamClassResult


class SimilarityBand(BaseModel):
    band: str
    rows: int
    share_of_rows: float
    spam_share: float | None
    metrics: Metrics | None


class TestEvaluation(BaseModel):
    split: str
    rows: int
    spam_share: float
    overall_metrics: Metrics
    roc_auc: float
    class_results: ClassResults
    similarity_method: str
    similarity_bands: list[SimilarityBand]
    single_message_latency: Latency
    report_matches_saved_model: bool


class ValidationEvaluation(BaseModel):
    split: str
    rows: int
    overall_metrics: Metrics
    roc_auc: float


class MarkerRemovalRun(BaseModel):
    name: str
    words_removed: int
    vocabulary_size: int
    metrics: Metrics
    roc_auc: float


class StyleScore(BaseModel):
    scored_on: str
    rows: int
    spam_share: float
    metrics: Metrics
    roc_auc: float


class CrossStyleRun(BaseModel):
    name: str
    training_style: str
    training_rows: int
    words_removed: int
    scores: list[StyleScore]


class CrossStyleF1Change(BaseModel):
    digits_to_placeholder: float
    placeholder_to_digits: float


class RemovalDecision(BaseModel):
    candidate: str
    validation_f1_drop: float
    f1_margin: float
    cross_style_f1_change: CrossStyleF1Change
    adopt: bool


class SourceLeakage(BaseModel):
    split_used: str
    interpretation_note: str
    marker_removal: list[MarkerRemovalRun]
    cross_style: list[CrossStyleRun]
    removal_decision: RemovalDecision


class ModelsResults(BaseModel):
    final_model: FinalModel
    selection: Selection
    feature_sets: list[FeatureSetRun]
    comparison_runs: list[ComparisonRun]
    validation_evaluation: ValidationEvaluation
    test_evaluation: TestEvaluation
    source_leakage: SourceLeakage
    limitations: list[str]


class DatasetSource(BaseModel):
    reported_source_url: str
    licence: str
    original_sources: str
    label_accuracy: str
    note: str


class DatasetFile(BaseModel):
    name: str
    format: str
    size_bytes: int
    sha256: str


class DatasetStructure(BaseModel):
    rows: int
    columns: list[str]


class LabelCount(BaseModel):
    rows: int
    share: float


class Labels(BaseModel):
    Ham: LabelCount
    Spam: LabelCount


class BlankText(BaseModel):
    empty_rows: dict[str, int]
    whitespace_only_rows: int


class LabelConflicts(BaseModel):
    texts: int
    rows: int


class Duplicates(BaseModel):
    identical_rows: int
    exact_duplicate_text_rows: int
    exact_conflicting_labels: LabelConflicts
    normalised_duplicate_rows: int
    normalised_conflicting_labels: LabelConflicts


class LengthSummary(BaseModel):
    rows: int
    min: int
    median: int
    p95: int
    p99: int
    max: int
    mean: float


class LengthsByLabel(BaseModel):
    Ham: LengthSummary
    Spam: LengthSummary


class Lengths(BaseModel):
    by_label: LengthsByLabel
    rows_under_20_chars: dict[str, int]
    rows_over_chars: dict[str, int]


class LabelShares(BaseModel):
    Ham: float
    Spam: float


class WordShare(BaseModel):
    word: str
    shares: LabelShares


class NumberStyle(BaseModel):
    style: str
    ham_rows: int
    spam_rows: int
    spaced_punctuation_share: float


class FormatFlag(BaseModel):
    name: str
    ham_rows: int
    ham_share: float
    spam_rows: int
    spam_share: float


class TextFormat(BaseModel):
    rows_analysed: int
    number_styles: list[NumberStyle]
    flags: list[FormatFlag]


class Cleaning(BaseModel):
    rows_in: int
    removed_blank: int
    removed_no_word_tokens: int
    removed_conflicting_labels: int
    conflicting_label_texts: int
    removed_duplicates: int
    rows_kept: int


class SplitRows(BaseModel):
    split: str
    total: int
    ham: int
    spam: int
    spam_share: float


class Preparation(BaseModel):
    cleaning: Cleaning
    random_seed: int
    validation_share: float
    test_share: float
    stratified_by: str
    splits: list[SplitRows]
    preprocessed_texts_shared_between_splits: int


class DatasetResults(BaseModel):
    source: DatasetSource
    file: DatasetFile
    structure: DatasetStructure
    labels: Labels
    missing_values: dict[str, int]
    blank_text: BlankText
    duplicates: Duplicates
    lengths: Lengths
    word_shares: list[WordShare]
    text_format: TextFormat
    preparation: Preparation
