"""Tests for verified model loading and classification. All text is made up."""

from __future__ import annotations

import ast
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from app.ml import predict
from app.ml.predict import (
    ClassificationRejected,
    LoadedModel,
    ModelUnavailable,
    classify,
    load_verified_model,
)
from tests.conftest import build_pipeline, write_model_files

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_verified_loading_returns_the_saved_pipeline(model_files: tuple[Path, Path]) -> None:
    model = load_verified_model(*model_files)
    assert model.metadata["model_version"] == "test-version"
    assert model.intercept == float(model.pipeline.named_steps["classifier"].intercept_[0])
    assert len(model.feature_names) == len(model.weights)


def test_loading_refuses_a_missing_model_file(tmp_path: Path) -> None:
    with pytest.raises(ModelUnavailable, match="model file was not found.*training.train_final"):
        load_verified_model(tmp_path / "missing.joblib", tmp_path / "missing.json")


def test_loading_refuses_missing_metadata(model_files: tuple[Path, Path], tmp_path: Path) -> None:
    with pytest.raises(ModelUnavailable, match="metadata was not found"):
        load_verified_model(model_files[0], tmp_path / "missing.json")


@pytest.mark.parametrize("content", ["not json", "{}", '{"pipeline_sha256": "abc"}'])
def test_loading_refuses_invalid_metadata(model_files: tuple[Path, Path], content: str) -> None:
    model_files[1].write_text(content, encoding="utf-8")
    with pytest.raises(ModelUnavailable, match="invalid or incomplete"):
        load_verified_model(*model_files)


def test_a_tampered_file_is_refused_before_it_is_loaded(
    model_files: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    with open(model_files[0], "ab") as file:
        file.write(b"changed")

    def must_not_load(_: Path) -> None:
        raise AssertionError("A tampered file was loaded")

    monkeypatch.setattr(predict, "load_pipeline", must_not_load)
    with pytest.raises(ModelUnavailable, match="doesn't match the hash"):
        load_verified_model(*model_files)


def test_a_wrong_fingerprint_is_refused(model_files: tuple[Path, Path]) -> None:
    metadata = json.loads(model_files[1].read_text(encoding="utf-8"))
    metadata["model_content_sha256"] = "0" * 64
    model_files[1].write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ModelUnavailable, match="fingerprint"):
        load_verified_model(*model_files)


def test_a_model_with_unexpected_labels_is_refused(tmp_path: Path) -> None:
    pipeline = build_pipeline()
    pipeline.fit(["free prize now", "meeting notes today"], ["junk", "ok"])
    with pytest.raises(ModelUnavailable, match="Ham and Spam"):
        load_verified_model(*write_model_files(tmp_path, pipeline))


def test_loading_logs_package_version_differences(
    model_files: tuple[Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    metadata = json.loads(model_files[1].read_text(encoding="utf-8"))
    metadata["versions"] = {"python": "1.0", "numpy": "0.0.1", "not-installed-package": "1.0"}
    model_files[1].write_text(json.dumps(metadata), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="spamshield.model"):
        load_verified_model(*model_files)
    assert "numpy" in caplog.text
    assert "python" not in caplog.text


def test_classify_labels_clear_examples(loaded_model: LoadedModel) -> None:
    assert classify(loaded_model, "WIN a FREE prize today")["label"] == "spam"
    assert classify(loaded_model, "Monday meeting notes attached")["label"] == "ham"


def test_classify_matches_direct_inference_from_the_pipeline(loaded_model: LoadedModel) -> None:
    texts = ["free prize", "meeting notes", "free meeting", "Call 555 now for CASH", "project prize monday"]
    direct_labels = loaded_model.pipeline.predict(texts)
    direct_scores = loaded_model.pipeline.decision_function(texts)
    for text, label, score in zip(texts, direct_labels, direct_scores):
        result = classify(loaded_model, text)
        assert result["label"] == label.lower()
        assert result["score"] == pytest.approx(float(score), abs=1e-5)


def test_label_always_agrees_with_the_sign_of_the_score(loaded_model: LoadedModel) -> None:
    for text in ["free prize", "meeting notes", "free meeting monday prize"]:
        result = classify(loaded_model, text)
        assert (result["score"] > 0) == (result["label"] == "spam")


def test_classify_counts_recognised_terms(loaded_model: LoadedModel) -> None:
    assert classify(loaded_model, "free prize unknownword")["terms_recognised"] == 2


def test_classify_applies_preprocessing(loaded_model: LoadedModel) -> None:
    assert classify(loaded_model, "FREE   PRIZE") == classify(loaded_model, "free prize")


@pytest.mark.parametrize("text", [".", "! ? ...", "a", "a b c"])
def test_text_without_usable_words_is_rejected(loaded_model: LoadedModel, text: str) -> None:
    with pytest.raises(ClassificationRejected) as rejected:
        classify(loaded_model, text)
    assert rejected.value.code == "no_usable_words"


def test_text_with_no_known_words_is_rejected(loaded_model: LoadedModel) -> None:
    with pytest.raises(ClassificationRejected) as rejected:
        classify(loaded_model, "completely unfamiliar vocabulary everywhere")
    assert rejected.value.code == "no_recognised_terms"


def test_importing_the_application_imports_no_training_code() -> None:
    script = (
        "import sys; import app.main; "
        "print(any(name == 'training' or name.startswith('training.') for name in sys.modules))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND_DIR, capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == "False"


def test_application_code_never_imports_training() -> None:
    for path in (BACKEND_DIR / "app").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            assert not any(module.split(".")[0] == "training" for module in modules), path


def test_classification_does_not_change_the_model(loaded_model: LoadedModel) -> None:
    before = predict.model_fingerprint(loaded_model.pipeline)
    weights = np.array(loaded_model.weights)
    classify(loaded_model, "brand new words and a free prize")
    assert predict.model_fingerprint(loaded_model.pipeline) == before
    assert np.array_equal(loaded_model.weights, weights)
