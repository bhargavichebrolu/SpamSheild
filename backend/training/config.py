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
