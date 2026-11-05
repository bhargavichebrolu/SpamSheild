"""Tests for the saved-results endpoints, using the committed reports and made-up reports."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ml import results
from app.ml.predict import DEFAULT_METADATA_PATH, LoadedModel, ModelUnavailable
from app.schemas.results import DatasetResults, ModelsResults

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"
SECRET_FIELD = "PrivateWordInsideTheReport"

MODELS_REPORTS = (
    "model_comparison.json",
    "final_test_evaluation.json",
    "final_validation_evaluation.json",
    "source_leakage.json",
)
DATASET_REPORTS = ("dataset_inspection.json", "format_analysis.json", "data_preparation.json")


def read_report(name: str) -> dict:
    return json.loads((REPORTS_DIR / name).read_text(encoding="utf-8"))


def copy_reports(directory: Path, names: tuple[str, ...]) -> None:
    for name in names:
        (directory / name).write_text((REPORTS_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")


def unavailable_loader() -> LoadedModel:
    raise ModelUnavailable("No model in this test.")


# --- Model results --------------------------------------------------------------------


def test_models_results_match_the_saved_reports(client: TestClient) -> None:
    response = client.get("/api/results/models")
    assert response.status_code == 200
    body = response.json()
    comparison = read_report("model_comparison.json")
    test_report = read_report("final_test_evaluation.json")

    assert body["selection"]["selected"] == comparison["selected"]
    assert body["selection"]["split_used"] == "validation"
    assert body["test_evaluation"]["overall_metrics"] == test_report["overall_metrics"]
    assert body["test_evaluation"]["roc_auc"] == test_report["roc_auc"]
    assert body["test_evaluation"]["report_matches_saved_model"] is True


def test_every_comparison_run_is_returned(client: TestClient) -> None:
    body = client.get("/api/results/models").json()
    comparison = read_report("model_comparison.json")
    expected = [run for group in comparison["runs"].values() for run in group["results"]]
    assert len(body["comparison_runs"]) == len(expected) == 18
    for returned, saved in zip(body["comparison_runs"], expected):
        assert returned["metrics"] == saved["metrics"]
        assert returned["setting"] == saved["setting"]


def test_similarity_bands_keep_their_sample_counts(client: TestClient) -> None:
    bands = client.get("/api/results/models").json()["test_evaluation"]["similarity_bands"]
    saved = read_report("final_test_evaluation.json")["metrics_by_similarity_band"]
    assert [band["band"] for band in bands] == list(saved)
    for band in bands:
        assert band["rows"] == saved[band["band"]]["rows"]
        assert band["metrics"] == saved[band["band"]]["metrics"]
    assert sum(band["rows"] for band in bands) == read_report("final_test_evaluation.json")["rows"]


def test_source_leakage_results_keep_the_interpretation_note(client: TestClient) -> None:
    leakage = client.get("/api/results/models").json()["source_leakage"]
    assert "not proof of generalisation" in leakage["interpretation_note"]
    assert len(leakage["marker_removal"]) == 6
    assert len(leakage["cross_style"]) == 5
    assert leakage["removal_decision"]["adopt"] is True


def test_final_model_identity_matches_the_metadata(client: TestClient) -> None:
    final_model = client.get("/api/results/models").json()["final_model"]
    metadata = json.loads(DEFAULT_METADATA_PATH.read_text(encoding="utf-8"))
    assert final_model["file_sha256"] == metadata["pipeline_sha256"]
    assert final_model["model_content_sha256"] == metadata["model_content_sha256"]
    assert final_model["removed_word_count"] == 575


def test_models_results_report_a_different_saved_model(tmp_path: Path) -> None:
    copy_reports(tmp_path, MODELS_REPORTS)
    metadata = json.loads(DEFAULT_METADATA_PATH.read_text(encoding="utf-8"))
    metadata["pipeline_sha256"] = "a-different-file"
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    built = results.build_models_results(tmp_path, metadata_path)
    assert built["test_evaluation"]["report_matches_saved_model"] is False


def test_results_work_without_the_model_being_loaded(make_client: Callable[..., TestClient]) -> None:
    client = make_client(unavailable_loader)
    assert client.get("/api/health").status_code == 503
    assert client.get("/api/results/models").status_code == 200
    assert client.get("/api/results/dataset").status_code == 200


# --- Dataset results ------------------------------------------------------------------


def test_dataset_results_match_the_saved_reports(client: TestClient) -> None:
    response = client.get("/api/results/dataset")
    assert response.status_code == 200
    body = response.json()
    inspection = read_report("dataset_inspection.json")
    preparation = read_report("data_preparation.json")

    assert body["structure"]["rows"] == inspection["structure"]["rows"]
    assert body["labels"] == inspection["labels"]
    assert body["duplicates"] == inspection["duplicates"]
    assert body["file"]["sha256"] == inspection["file"]["sha256"]
    assert body["preparation"]["cleaning"] == preparation["cleaning"]
    assert [split["split"] for split in body["preparation"]["splits"]] == ["train", "validation", "test"]


def test_licence_is_reported_as_not_verified(client: TestClient) -> None:
    source = client.get("/api/results/dataset").json()["source"]
    assert source["licence"] == "Not verified"
    assert source["original_sources"] == "Not verified"
    assert source["reported_source_url"].startswith("https://www.kaggle.com/datasets/")


def test_number_styles_add_up_to_the_rows_analysed(client: TestClient) -> None:
    text_format = client.get("/api/results/dataset").json()["text_format"]
    total = sum(style["ham_rows"] + style["spam_rows"] for style in text_format["number_styles"])
    assert total == text_format["rows_analysed"]


# --- Restricted to aggregates ---------------------------------------------------------


@pytest.mark.parametrize("path", ["/api/results/models", "/api/results/dataset"])
def test_results_have_no_word_list_fields(client: TestClient, path: str) -> None:
    text = client.get(path).text.lower()
    assert "removed_words_sha256" not in text
    assert "most_ham_leaning" not in text
    assert "style_leaning" not in text


@pytest.mark.skipif(
    not (REPORTS_DIR / "source_markers.json").exists(),
    reason="The generated word lists aren't present.",
)
@pytest.mark.parametrize("path", ["/api/results/models", "/api/results/dataset"])
def test_results_contain_no_words_from_the_generated_lists(client: TestClient, path: str) -> None:
    text = client.get(path).text.lower()
    markers = json.loads((REPORTS_DIR / "source_markers.json").read_text(encoding="utf-8"))
    # These few words are deliberately reported, with their shares, in a committed report.
    published = set(read_report("dataset_inspection.json")["marker_document_frequency"])
    for words in markers["lists"].values():
        for word in words[:300]:
            if word not in published:
                assert f'"{word}"' not in text


def test_the_generated_word_lists_are_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    read: list[str] = []
    original = results._read_json

    def recording(path: Path) -> dict:
        read.append(path.name)
        return original(path)

    monkeypatch.setattr(results, "_read_json", recording)
    results.build_models_results()
    results.build_dataset_results()
    assert "source_markers.json" not in read
    assert "vocabulary_analysis.json" not in read


def test_an_unexpected_field_in_a_report_cannot_reach_the_website(
    tmp_path: Path, make_client: Callable[..., TestClient], loaded_model: LoadedModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy_reports(tmp_path, DATASET_REPORTS)
    inspection_path = tmp_path / "dataset_inspection.json"
    inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
    inspection["file"]["example_email"] = SECRET_FIELD
    inspection["labels"]["Ham"]["example_email"] = SECRET_FIELD
    inspection["structure"]["example_email"] = SECRET_FIELD
    inspection_path.write_text(json.dumps(inspection), encoding="utf-8")

    monkeypatch.setattr("app.api.routes.build_dataset_results", lambda: results.build_dataset_results(tmp_path))
    response = make_client(lambda: loaded_model).get("/api/results/dataset")
    assert response.status_code == 200
    assert SECRET_FIELD not in response.text


# --- Error handling -------------------------------------------------------------------


@pytest.mark.parametrize("name", MODELS_REPORTS)
def test_a_missing_models_report_is_a_clear_failure(tmp_path: Path, name: str) -> None:
    copy_reports(tmp_path, MODELS_REPORTS)
    (tmp_path / name).unlink()
    with pytest.raises(results.ResultsUnavailable, match=name):
        results.build_models_results(tmp_path)


@pytest.mark.parametrize("name", DATASET_REPORTS)
def test_a_missing_dataset_report_is_a_clear_failure(tmp_path: Path, name: str) -> None:
    copy_reports(tmp_path, DATASET_REPORTS)
    (tmp_path / name).unlink()
    with pytest.raises(results.ResultsUnavailable, match=name):
        results.build_dataset_results(tmp_path)


def test_an_unreadable_report_is_a_clear_failure(tmp_path: Path) -> None:
    copy_reports(tmp_path, DATASET_REPORTS)
    (tmp_path / "data_preparation.json").write_text("not json", encoding="utf-8")
    with pytest.raises(results.ResultsUnavailable, match="data_preparation.json"):
        results.build_dataset_results(tmp_path)


@pytest.mark.parametrize(
    "builder, names, name",
    [
        (results.build_dataset_results, DATASET_REPORTS, "dataset_inspection.json"),
        (results.build_models_results, MODELS_REPORTS, "model_comparison.json"),
    ],
)
def test_a_report_with_missing_contents_is_a_clear_failure(
    tmp_path: Path, builder: Callable, names: tuple[str, ...], name: str
) -> None:
    copy_reports(tmp_path, names)
    (tmp_path / name).write_text("{}", encoding="utf-8")
    with pytest.raises(results.ResultsUnavailable, match="expected contents"):
        builder(tmp_path)


@pytest.mark.parametrize(
    "path, target",
    [
        ("/api/results/models", "app.api.routes.build_models_results"),
        ("/api/results/dataset", "app.api.routes.build_dataset_results"),
    ],
)
def test_the_api_returns_a_503_for_unavailable_results(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, path: str, target: str
) -> None:
    def fail() -> dict:
        raise results.ResultsUnavailable("The saved report is missing.")

    monkeypatch.setattr(target, fail)
    response = client.get(path)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "results_unavailable"


def test_the_schemas_accept_the_real_reports() -> None:
    ModelsResults.model_validate(results.build_models_results())
    DatasetResults.model_validate(results.build_dataset_results())


def test_reading_results_does_not_change_any_report(client: TestClient) -> None:
    before = {path.name: path.read_bytes() for path in REPORTS_DIR.glob("*.json")}
    client.get("/api/results/models")
    client.get("/api/results/dataset")
    assert {path.name: path.read_bytes() for path in REPORTS_DIR.glob("*.json")} == before
