"""Tests for the API comparison tool, and for the API with the real model if it's present.

The real-model tests are skipped in a fresh copy of the repository, because the saved
model isn't in Git. All text is made up.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.ml.predict import (
    DEFAULT_METADATA_PATH,
    DEFAULT_PIPELINE_PATH,
    LoadedModel,
    file_sha256,
    load_verified_model,
    model_fingerprint,
)
from training import verify_api

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

needs_real_model = pytest.mark.skipif(
    not DEFAULT_PIPELINE_PATH.exists(),
    reason="The saved model isn't present. Create it with `python -m training.train_final`.",
)

ROWS = pd.DataFrame(
    {
        "label": ["Spam", "Ham", "Spam", "Ham", "Ham"],
        "text": ["free prize now", "monday meeting notes", "...", "unfamiliar vocabulary", "project notes attached"],
    }
)


def test_comparison_counts_matches_and_rejections(client: TestClient, loaded_model: LoadedModel) -> None:
    result = verify_api.compare_with_direct_inference(client, loaded_model.pipeline, ROWS)
    assert result["rows_sent"] == 5
    assert result["rows_accepted"] == 3
    assert result["rows_rejected_by_reason"] == {"no_recognised_terms": 1, "no_usable_words": 1}
    assert result["label_mismatches"] == 0
    assert result["score_mismatches"] == 0
    assert result["explanation_total_mismatches"] == 0
    assert result["responses_with_a_confidence_value"] == 0
    assert result["metrics_on_accepted_rows"]["true_spam"] == 1


def test_comparison_detects_a_wrong_label(
    client: TestClient, loaded_model: LoadedModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_classify = "app.api.routes.classify"

    def always_ham(model: LoadedModel, text: str) -> dict:
        from app.ml.predict import classify

        return {**classify(model, text), "label": "ham"}

    monkeypatch.setattr(real_classify, always_ham)
    result = verify_api.compare_with_direct_inference(client, loaded_model.pipeline, ROWS)
    assert result["label_mismatches"] == 1


def test_comparison_detects_a_wrong_score(
    client: TestClient, loaded_model: LoadedModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    def shifted(model: LoadedModel, text: str) -> dict:
        from app.ml.predict import classify

        result = classify(model, text)
        return {**result, "score": result["score"] + 0.5}

    monkeypatch.setattr("app.api.routes.classify", shifted)
    result = verify_api.compare_with_direct_inference(client, loaded_model.pipeline, ROWS)
    assert result["score_mismatches"] == 3
    assert result["explanation_total_mismatches"] == 3


def test_comparison_counts_server_failures(
    make_client: Callable[..., TestClient], loaded_model: LoadedModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(_: LoadedModel, __: str) -> dict:
        raise RuntimeError("broken")

    monkeypatch.setattr("app.api.routes.classify", broken)
    client = make_client(lambda: loaded_model, raise_server_exceptions=False)
    result = verify_api.compare_with_direct_inference(client, loaded_model.pipeline, ROWS)
    # All five fail, because the rejections happen inside the broken function too.
    assert result["other_failures"] == 5
    assert result["other_failures_by_status"] == {"500": 5}
    assert result["rows_accepted"] == 0
    assert result["metrics_on_accepted_rows"] is None


def test_comparison_counts_an_oversized_body_as_a_refusal_not_a_failure(
    client: TestClient, loaded_model: LoadedModel
) -> None:
    rows = pd.DataFrame({"label": ["Ham"], "text": ["free prize " * 30_000]})
    result = verify_api.compare_with_direct_inference(client, loaded_model.pipeline, rows)
    assert result["rows_rejected_by_reason"] == {"body_too_large": 1}
    assert result["other_failures"] == 0


def test_the_tool_only_loads_validation_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, model_files: tuple[Path, Path]
) -> None:
    requested: list[str] = []

    def fake_load(split: str, **_: object) -> pd.DataFrame:
        requested.append(split)
        return ROWS

    monkeypatch.setattr(verify_api, "load_split", fake_load)
    monkeypatch.setattr(verify_api, "RESULTS_PATH", tmp_path / "report.json")
    monkeypatch.setattr(verify_api, "DEFAULT_PIPELINE_PATH", model_files[0])
    monkeypatch.setattr(verify_api, "load_pipeline", lambda: load_verified_model(*model_files).pipeline)

    from app.main import create_app

    monkeypatch.setattr(
        verify_api, "create_app", lambda: create_app(model_loader=lambda: load_verified_model(*model_files))
    )
    assert verify_api.main() == 0
    assert requested == ["validation"]
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["frozen_model"]["file_unchanged"] is True
    assert report["frozen_model"]["content_unchanged"] is True
    assert "free prize" not in json.dumps(report)


@needs_real_model
def test_real_model_loads_and_matches_its_recorded_identity() -> None:
    model = load_verified_model()
    metadata = json.loads(DEFAULT_METADATA_PATH.read_text(encoding="utf-8"))
    assert file_sha256(DEFAULT_PIPELINE_PATH) == metadata["pipeline_sha256"]
    assert model_fingerprint(model.pipeline) == metadata["model_content_sha256"]


@needs_real_model
def test_real_model_through_the_api_matches_direct_inference() -> None:
    from app.main import create_app

    texts = [
        "Congratulations! You have won a free prize. Click here to claim 1000 dollars.",
        "Hi Sam, the project meeting has moved to Tuesday at 3pm. Notes attached.",
        "Buy cheap watches online today with free shipping",
        "Please review the budget report before the call on Monday.",
    ]
    model = load_verified_model()
    labels = model.pipeline.predict(texts)
    scores = model.pipeline.decision_function(texts)
    with TestClient(create_app()) as client:
        for text, label, score in zip(texts, labels, scores):
            body = client.post("/api/classify", json={"text": text}).json()
            assert body["label"] == label.lower()
            assert body["score"] == pytest.approx(float(score), abs=2e-6)
            assert body["confidence"] is None


@needs_real_model
def test_real_model_info_reports_the_saved_results() -> None:
    from app.main import create_app

    with TestClient(create_app()) as client:
        body = client.get("/api/model-info").json()
    report = json.loads((REPORTS_DIR / "final_test_evaluation.json").read_text(encoding="utf-8"))
    assert body["test_results"]["f1_spam"] == report["overall_metrics"]["f1_spam"]
    assert body["test_results"]["report_matches_loaded_file"] is True
    assert body["provides_probability"] is False
    assert body["removed_word_count"] == 575
