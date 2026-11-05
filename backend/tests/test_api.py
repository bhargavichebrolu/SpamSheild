"""Tests for the API endpoints, using a tiny model. All text is made up."""

from __future__ import annotations

import http.client
import json
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

from app.config import ALLOWED_ORIGINS, MAX_BODY_BYTES, MAX_INPUT_CHARS
from app.ml import model_info
from app.ml.predict import LoadedModel, ModelUnavailable, load_verified_model
from tests.conftest import REMOVED_WORD

CLASSIFY = "/api/classify"
SECRET_TEXT = "PrivateWordInsideTheEmail"


def unavailable_loader() -> LoadedModel:
    raise ModelUnavailable("The model file was not found. Test instructions.")


def assert_error(response, status: int, code: str, field: str | None = None) -> None:
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["field"] == field
    assert body["error"]["message"]


# --- Health ---------------------------------------------------------------------------


def test_health_reports_a_loaded_model(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
        "model_version": "test-version",
        "detail": None,
    }


def test_health_explains_an_unavailable_model(make_client: Callable[..., TestClient]) -> None:
    response = make_client(unavailable_loader).get("/api/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["model_loaded"] is False
    assert "not found" in body["detail"]


# --- Classify: valid input ------------------------------------------------------------


def test_valid_spam_text_gets_a_complete_response(client: TestClient) -> None:
    response = client.post(CLASSIFY, json={"text": "WIN a FREE prize today"})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "spam"
    assert body["score"] > 0
    assert body["model_version"] == "test-version"
    assert body["text_length"] == len("WIN a FREE prize today")
    assert body["terms_recognised"] > 0
    assert any(item["term"] == "free" for item in body["explanation"]["spam_terms"])
    assert "do not prove" in body["explanation"]["note"]


def test_valid_ham_text_is_labelled_ham(client: TestClient) -> None:
    body = client.post(CLASSIFY, json={"text": "Monday meeting notes attached"}).json()
    assert body["label"] == "ham"
    assert body["score"] < 0


def test_no_probability_or_confidence_is_ever_returned(client: TestClient) -> None:
    body = client.post(CLASSIFY, json={"text": "free prize"}).json()
    assert body["confidence"] is None
    assert "probability" not in body
    assert "%" not in json.dumps({key: value for key, value in body.items() if key != "explanation"})


def test_api_predictions_match_direct_inference_from_the_pipeline(
    client: TestClient, loaded_model: LoadedModel
) -> None:
    texts = ["free prize", "meeting notes", "free meeting", "Call 555 now for CASH", "project prize monday"]
    direct_labels = loaded_model.pipeline.predict(texts)
    direct_scores = loaded_model.pipeline.decision_function(texts)
    for text, label, score in zip(texts, direct_labels, direct_scores):
        body = client.post(CLASSIFY, json={"text": text}).json()
        assert body["label"] == label.lower()
        assert body["score"] == pytest.approx(float(score), abs=1e-5)


def test_response_does_not_repeat_the_email_text(client: TestClient) -> None:
    response = client.post(CLASSIFY, json={"text": f"free prize {SECRET_TEXT}"})
    assert response.status_code == 200
    assert SECRET_TEXT.lower() not in response.text.lower()


def test_removed_words_are_never_exposed(client: TestClient) -> None:
    classified = client.post(CLASSIFY, json={"text": f"{REMOVED_WORD} free prize"})
    assert REMOVED_WORD not in classified.text


# --- Classify: length limit -----------------------------------------------------------


def test_text_at_exactly_the_limit_is_accepted(client: TestClient) -> None:
    text = ("free prize " * MAX_INPUT_CHARS)[:MAX_INPUT_CHARS]
    response = client.post(CLASSIFY, json={"text": text})
    assert response.status_code == 200
    assert response.json()["text_length"] == MAX_INPUT_CHARS


def test_text_one_character_over_the_limit_is_rejected(client: TestClient) -> None:
    text = ("free prize " * MAX_INPUT_CHARS)[: MAX_INPUT_CHARS + 1]
    assert_error(client.post(CLASSIFY, json={"text": text}), 422, "text_too_long", "text")


def test_limit_is_20000_characters() -> None:
    assert MAX_INPUT_CHARS == 20_000


def test_limit_counts_characters_not_bytes(client: TestClient) -> None:
    text = "free prize " + "\U0001F600" * (MAX_INPUT_CHARS - 11)
    assert len(text) == MAX_INPUT_CHARS
    assert client.post(CLASSIFY, json={"text": text}).status_code == 200


def test_the_largest_valid_text_fits_within_the_body_limit(client: TestClient) -> None:
    text = "free prize " + "\U0001F600" * (MAX_INPUT_CHARS - 11)
    escaped = json.dumps({"text": text}, ensure_ascii=True)
    assert len(escaped) <= MAX_BODY_BYTES
    response = client.post(CLASSIFY, content=escaped, headers={"Content-Type": "application/json"})
    assert response.status_code == 200


# --- Classify: invalid input ----------------------------------------------------------


@pytest.mark.parametrize("text", ["", " ", "  \n\t  "])
def test_empty_or_whitespace_text_is_rejected(client: TestClient, text: str) -> None:
    assert_error(client.post(CLASSIFY, json={"text": text}), 422, "text_empty", "text")


def test_missing_text_field_is_rejected(client: TestClient) -> None:
    assert_error(client.post(CLASSIFY, json={}), 422, "text_missing", "text")


@pytest.mark.parametrize("value", [123, None, ["free prize"], {"nested": "free prize"}, True])
def test_non_string_text_is_rejected(client: TestClient, value: object) -> None:
    assert_error(client.post(CLASSIFY, json={"text": value}), 422, "text_not_a_string", "text")


def test_invalid_json_is_rejected(client: TestClient) -> None:
    response = client.post(CLASSIFY, content="{not json", headers={"Content-Type": "application/json"})
    assert_error(response, 422, "invalid_json")


def test_a_json_body_that_is_not_an_object_is_rejected(client: TestClient) -> None:
    assert_error(client.post(CLASSIFY, json=["free prize"]), 422, "invalid_body")


def test_invalid_utf8_gets_a_controlled_error(client: TestClient) -> None:
    response = client.post(CLASSIFY, content=b'{"text": "\xff\xfe"}', headers={"Content-Type": "application/json"})
    assert response.status_code in {400, 422}
    assert "error" in response.json()


def test_punctuation_only_text_is_rejected(client: TestClient) -> None:
    assert_error(client.post(CLASSIFY, json={"text": "... !!!"}), 422, "no_usable_words", "text")


def test_text_with_no_known_words_is_rejected(client: TestClient) -> None:
    response = client.post(CLASSIFY, json={"text": "unfamiliar vocabulary everywhere"})
    assert_error(response, 422, "no_recognised_terms", "text")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "\n",
        SECRET_TEXT * 2_000,
        f"... {SECRET_TEXT[:1]} !!!",
        f"{SECRET_TEXT} unfamiliar",
    ],
    ids=["empty", "newline", "too_long", "no_usable_words", "no_recognised_terms"],
)
def test_error_responses_never_repeat_the_submitted_text(client: TestClient, text: str) -> None:
    response = client.post(CLASSIFY, json={"text": text})
    assert response.status_code == 422
    assert SECRET_TEXT.lower() not in response.text.lower()
    assert "input" not in response.json()["error"]


def test_error_for_non_string_text_does_not_repeat_it(client: TestClient) -> None:
    response = client.post(CLASSIFY, json={"text": [SECRET_TEXT]})
    assert SECRET_TEXT not in response.text


# --- Body size ------------------------------------------------------------------------


def test_an_oversized_body_is_rejected(client: TestClient) -> None:
    body = json.dumps({"text": "a" * (MAX_BODY_BYTES + 1)})
    response = client.post(CLASSIFY, content=body, headers={"Content-Type": "application/json"})
    assert_error(response, 413, "body_too_large")
    assert "a" * 100 not in response.text


def test_an_oversized_body_cannot_understate_its_size(loaded_model: LoadedModel) -> None:
    """Send the size limit's check a body larger than its Content-Length header says."""
    import asyncio

    from app.main import BodySizeLimitMiddleware

    forwarded: list[str] = []

    async def downstream(scope, receive, send) -> None:
        forwarded.append("reached the application")

    middleware = BodySizeLimitMiddleware(downstream, max_bytes=10)
    messages = [
        {"type": "http.request", "body": b"12345678", "more_body": True},
        {"type": "http.request", "body": b"12345678", "more_body": False},
    ]
    sent: list[dict] = []

    async def receive() -> dict:
        return messages.pop(0)

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {"type": "http", "method": "POST", "headers": [(b"content-length", b"1")]}
    asyncio.run(middleware(scope, receive, send))
    assert forwarded == []
    assert sent[0]["status"] == 413


def test_a_rejected_upload_is_read_before_responding() -> None:
    import asyncio

    from app.main import BodySizeLimitMiddleware

    async def downstream(scope, receive, send) -> None:
        raise AssertionError("A rejected body reached the application")

    messages = [
        {"type": "http.request", "body": b"1" * 8, "more_body": True},
        {"type": "http.request", "body": b"2" * 8, "more_body": True},
        {"type": "http.request", "body": b"3" * 8, "more_body": False},
    ]
    events: list[str] = []

    async def receive() -> dict:
        events.append("read")
        return messages.pop(0)

    async def send(message: dict) -> None:
        events.append(message["type"])

    scope = {"type": "http", "method": "POST", "headers": [(b"content-length", b"24")]}
    asyncio.run(BodySizeLimitMiddleware(downstream, max_bytes=10)(scope, receive, send))
    assert messages == []
    assert events.index("http.response.start") == events.count("read")


def test_discarding_a_rejected_upload_is_capped() -> None:
    import asyncio

    from app.main import BodySizeLimitMiddleware

    reads = 0

    async def endless_receive() -> dict:
        nonlocal reads
        reads += 1
        return {"type": "http.request", "body": b"x" * 10, "more_body": True}

    sent: list[dict] = []

    async def send(message: dict) -> None:
        sent.append(message)

    middleware = BodySizeLimitMiddleware(None, max_bytes=10, max_discard_bytes=50)
    scope = {"type": "http", "method": "POST", "headers": [(b"content-length", b"999999")]}
    asyncio.run(middleware(scope, endless_receive, send))
    assert reads == 6
    assert sent[0]["status"] == 413


def test_a_real_server_returns_the_size_error_to_the_client(loaded_model: LoadedModel) -> None:
    """Over real HTTP, replying too early resets the connection, which a test client can't show."""
    from app.main import create_app

    server = uvicorn.Server(
        uvicorn.Config(create_app(model_loader=lambda: loaded_model), host="127.0.0.1", port=0, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        port = server.servers[0].sockets[0].getsockname()[1]

        for _ in range(5):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            connection.request(
                "POST",
                CLASSIFY,
                body=json.dumps({"text": "a" * (2 * MAX_BODY_BYTES)}),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            body = json.loads(response.read())
            connection.close()
            assert response.status == 413
            assert body["error"]["code"] == "body_too_large"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def test_a_small_chunked_body_reaches_the_application_intact() -> None:
    import asyncio

    from app.main import BodySizeLimitMiddleware

    received: list[bytes] = []

    async def downstream(scope, receive, send) -> None:
        message = await receive()
        received.append(message["body"])

    middleware = BodySizeLimitMiddleware(downstream, max_bytes=100)
    messages = [
        {"type": "http.request", "body": b"part one ", "more_body": True},
        {"type": "http.request", "body": b"part two", "more_body": False},
    ]

    async def receive() -> dict:
        return messages.pop(0)

    async def send(_: dict) -> None:
        raise AssertionError("Nothing should be sent")

    asyncio.run(middleware({"type": "http", "method": "POST", "headers": []}, receive, send))
    assert received == [b"part one part two"]


# --- Errors from the server -----------------------------------------------------------


def test_classify_returns_503_when_the_model_is_unavailable(make_client: Callable[..., TestClient]) -> None:
    response = make_client(unavailable_loader).post(CLASSIFY, json={"text": "free prize"})
    assert_error(response, 503, "model_unavailable")
    assert "not found" in response.json()["error"]["message"]


def test_model_info_returns_503_when_the_model_is_unavailable(make_client: Callable[..., TestClient]) -> None:
    assert_error(make_client(unavailable_loader).get("/api/model-info"), 503, "model_unavailable")


def test_validation_still_runs_when_the_model_is_unavailable(make_client: Callable[..., TestClient]) -> None:
    assert_error(make_client(unavailable_loader).post(CLASSIFY, json={"text": ""}), 422, "text_empty", "text")


def test_a_tampered_model_file_leaves_the_api_running_with_a_503(
    make_client: Callable[..., TestClient], model_files: tuple[Path, Path]
) -> None:
    with open(model_files[0], "ab") as file:
        file.write(b"changed")
    client = make_client(lambda: load_verified_model(*model_files))
    assert client.get("/api/health").status_code == 503
    assert_error(client.post(CLASSIFY, json={"text": "free prize"}), 503, "model_unavailable")


def test_an_unexpected_failure_is_controlled_and_keeps_text_out_of_the_logs(
    make_client: Callable[..., TestClient],
    loaded_model: LoadedModel,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(_: LoadedModel, text: str) -> dict:
        raise RuntimeError(f"Something broke while reading: {text}")

    monkeypatch.setattr("app.api.routes.classify", fail)
    client = make_client(lambda: loaded_model, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="spamshield.api"):
        response = client.post(CLASSIFY, json={"text": f"free prize {SECRET_TEXT}"})
    assert_error(response, 500, "internal_error")
    assert SECRET_TEXT not in response.text
    assert "RuntimeError" in caplog.text
    assert SECRET_TEXT not in caplog.text


def test_normal_requests_do_not_log_the_text(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        client.post(CLASSIFY, json={"text": f"free prize {SECRET_TEXT}"})
    assert SECRET_TEXT not in caplog.text


def test_an_unknown_path_gets_the_standard_error_shape(client: TestClient) -> None:
    assert_error(client.get("/api/nothing-here"), 404, "not_found")


def test_a_wrong_method_gets_the_standard_error_shape(client: TestClient) -> None:
    assert_error(client.get(CLASSIFY), 405, "method_not_allowed")


# --- Model info -----------------------------------------------------------------------


def test_model_info_describes_the_model(client: TestClient, model_files: tuple[Path, Path]) -> None:
    response = client.get("/api/model-info")
    assert response.status_code == 200
    body = response.json()
    metadata = json.loads(model_files[1].read_text(encoding="utf-8"))
    assert body["model_version"] == "test-version"
    assert body["model_type"] == "linear_svm"
    assert body["provides_probability"] is False
    assert body["max_input_characters"] == MAX_INPUT_CHARS
    assert body["file_sha256"] == metadata["pipeline_sha256"]
    assert body["model_content_sha256"] == metadata["model_content_sha256"]
    assert body["file_sha256"] != body["model_content_sha256"]
    assert "isn't a probability" in body["score_meaning"]
    assert any("not an email security product" in item for item in body["limitations"])


def test_model_info_gives_the_count_of_removed_words_but_never_the_words(client: TestClient) -> None:
    response = client.get("/api/model-info")
    assert response.json()["removed_word_count"] == 1
    assert REMOVED_WORD not in response.text


def _evaluation_reports(directory: Path, pipeline_hash: str) -> None:
    (directory / "final_test_evaluation.json").write_text(
        json.dumps(
            {
                "split": "test",
                "rows": 100,
                "roc_auc": 0.9,
                "pipeline_sha256": pipeline_hash,
                "overall_metrics": {
                    "accuracy": 0.8,
                    "precision_spam": 0.7,
                    "recall_spam": 0.6,
                    "f1_spam": 0.5,
                    "ham_flagged_as_spam": 4,
                    "spam_missed": 3,
                },
                "metrics_by_similarity_band": {
                    "0.00_to_0.80": {"rows": 40, "metrics": {"f1_spam": 0.4}},
                },
            }
        ),
        encoding="utf-8",
    )
    style = lambda run: {  # noqa: E731
        "validation_by_style": {
            "digits_only": {"metrics": {"f1_spam": run}},
            "placeholder_only": {"metrics": {"f1_spam": run}},
        }
    }
    (directory / "source_leakage.json").write_text(
        json.dumps(
            {
                "interpretation_note": "Not proof of generalisation.",
                "removal_decision": {"candidate": "removal"},
                "cross_style": {
                    "train_digits_only": style(0.1),
                    "train_digits_only_removal": style(0.2),
                    "train_placeholder_only": style(0.3),
                    "train_placeholder_only_removal": style(0.4),
                },
            }
        ),
        encoding="utf-8",
    )


def test_model_info_reads_results_from_the_saved_reports(loaded_model: LoadedModel, tmp_path: Path) -> None:
    _evaluation_reports(tmp_path, loaded_model.metadata["pipeline_sha256"])
    info = model_info.build_model_info(loaded_model, tmp_path)
    assert info["test_results"]["f1_spam"] == 0.5
    assert info["test_results"]["no_close_training_match"] == {"rows": 40, "f1_spam": 0.4}
    assert info["test_results"]["report_matches_loaded_file"] is True
    shift = info["cross_style_results"]["digit_style_to_placeholder_style"]
    assert shift == {"f1_without_word_removal": 0.1, "f1_with_word_removal": 0.2}
    assert "Not proof" in info["cross_style_results"]["note"]


def test_model_info_says_when_results_describe_a_different_file(loaded_model: LoadedModel, tmp_path: Path) -> None:
    _evaluation_reports(tmp_path, "a-different-file-hash")
    assert model_info.build_model_info(loaded_model, tmp_path)["test_results"]["report_matches_loaded_file"] is False


def test_model_info_reports_none_when_results_are_missing(loaded_model: LoadedModel, tmp_path: Path) -> None:
    info = model_info.build_model_info(loaded_model, tmp_path)
    assert info["test_results"] is None
    assert info["cross_style_results"] is None


# --- Browser access and documentation -------------------------------------------------


@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
def test_the_local_website_may_call_the_api(client: TestClient, origin: str) -> None:
    response = client.options(
        CLASSIFY,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_other_websites_may_not_call_the_api(client: TestClient) -> None:
    response = client.post(CLASSIFY, json={"text": "free prize"}, headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_a_size_rejection_reaches_the_website_with_browser_headers(client: TestClient) -> None:
    body = json.dumps({"text": "a" * (MAX_BODY_BYTES + 1)})
    response = client.post(
        CLASSIFY,
        content=body,
        headers={"Content-Type": "application/json", "Origin": ALLOWED_ORIGINS[0]},
    )
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGINS[0]


def test_generated_documentation_is_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) >= {"/api/health", "/api/classify", "/api/model-info"}
    request = schema["components"]["schemas"]["ClassifyRequest"]["properties"]["text"]
    assert request["maxLength"] == MAX_INPUT_CHARS
