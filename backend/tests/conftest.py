"""Shared test helpers: a tiny fitted model, saved the same way as the real one.

All text is made up. Nothing here needs the dataset, the real model or any training code.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.main import create_app
from app.ml.predict import LoadedModel, file_sha256, load_verified_model, model_fingerprint
from app.ml.preprocess import preprocess_text

SPAM_TEXTS = [
    "win a free prize today call 555",
    "free money and a free prize now",
    "claim your free prize and cash",
    "cheap pills offer free delivery",
]
HAM_TEXTS = [
    "meeting moved to monday afternoon",
    "monday meeting notes are attached",
    "notes from the project meeting today",
    "please review the attached project notes",
]
REMOVED_WORD = "secretsurname"


def build_pipeline() -> Pipeline:
    """Fit a tiny pipeline with the same structure as the real one."""
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=preprocess_text,
                    lowercase=False,
                    sublinear_tf=True,
                    stop_words=[REMOVED_WORD],
                ),
            ),
            ("classifier", LinearSVC(C=10.0, random_state=42)),
        ]
    )
    texts = SPAM_TEXTS + HAM_TEXTS + [f"{REMOVED_WORD} free prize", f"{REMOVED_WORD} meeting notes"]
    labels = ["Spam"] * len(SPAM_TEXTS) + ["Ham"] * len(HAM_TEXTS) + ["Spam", "Ham"]
    return pipeline.fit(texts, labels)


def write_model_files(directory: Path, pipeline: Pipeline | None = None) -> tuple[Path, Path]:
    """Save a pipeline with matching metadata, and return both paths."""
    pipeline = pipeline or build_pipeline()
    pipeline_path = directory / "pipeline.joblib"
    metadata_path = directory / "metadata.json"
    joblib.dump(pipeline, pipeline_path, compress=3)
    metadata_path.write_text(
        json.dumps(
            {
                "model_version": "test-version",
                "model": "linear_svm",
                "setting": {"C": 10.0},
                "features": "word_1",
                "vocabulary_size": len(pipeline.named_steps["tfidf"].vocabulary_),
                "removed_words": {"count": 1, "rule": "test", "sha256": "abc"},
                "training_rows": 10,
                "pipeline_sha256": file_sha256(pipeline_path),
                "model_content_sha256": model_fingerprint(pipeline),
            }
        ),
        encoding="utf-8",
    )
    return pipeline_path, metadata_path


@pytest.fixture
def model_files(tmp_path: Path) -> tuple[Path, Path]:
    return write_model_files(tmp_path)


@pytest.fixture
def loaded_model(model_files: tuple[Path, Path]) -> LoadedModel:
    return load_verified_model(*model_files)


@pytest.fixture
def make_client() -> Iterator[Callable[..., TestClient]]:
    """Return a function that builds a running test client, and close each one afterwards."""
    clients: list[TestClient] = []

    def build(loader: Callable[[], LoadedModel], **options: object) -> TestClient:
        client = TestClient(create_app(model_loader=loader), **options)
        client.__enter__()
        clients.append(client)
        return client

    yield build
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client: Callable[..., TestClient], loaded_model: LoadedModel) -> TestClient:
    return make_client(lambda: loaded_model)
