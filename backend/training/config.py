"""Settings shared by the training scripts."""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BACKEND_DIR / "reports"
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
SPLIT_ASSIGNMENTS = PROCESSED_DIR / "split_assignments.csv"

RANDOM_SEED = 42
VALIDATION_SHARE = 0.10
TEST_SHARE = 0.10

# Set from validation results only: model_comparison.json chose the model and features,
# and source_leakage.json's removal_decision chose the word removal. Test results must
# never change this.
FINAL_MODEL: dict = {
    "model_version": "1.0.0",
    "model": "linear_svm",
    "setting_name": "C",
    "setting_value": 10.0,
    "features": "word_1",
    "removed_words": "remove_style_300_and_ham_300",
}
