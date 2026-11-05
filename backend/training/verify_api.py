"""Check that API predictions match direct inference from the frozen pipeline.

Every validation message is sent through the API and also scored directly by the saved
pipeline, and the results are compared. The test split is never loaded. The saved model
is only read, and its hashes are checked before and after.

Run from the backend folder:
    python -m training.verify_api
"""

from __future__ import annotations

import collections
import json
import time

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import create_app
from app.ml.predict import DEFAULT_PIPELINE_PATH, file_sha256, load_pipeline, model_fingerprint
from training.config import REPORTS_DIR
from training.evaluate import score
from training.inspect_dataset import write_report
from training.prepare_data import load_split

RESULTS_PATH = REPORTS_DIR / "api_verification.json"

# Scores are rounded to 6 decimal places in responses, so this allows for that rounding.
SCORE_TOLERANCE = 2e-6
# An explanation adds several rounded values, so its total can differ a little more.
EXPLANATION_TOLERANCE = 1e-4


def explanation_total(explanation: dict) -> float:
    """Add up the parts of an explanation, which should equal the score."""
    listed = explanation["spam_terms"] + explanation["ham_terms"]
    return (
        explanation["intercept"]
        + explanation["other_terms_total"]
        + sum(item["contribution"] for item in listed)
    )


def compare_with_direct_inference(client: TestClient, pipeline, rows: pd.DataFrame) -> dict:
    """Send each row through the API, and compare with the pipeline's own results."""
    direct_labels = pipeline.predict(rows["text"])
    direct_scores = pipeline.decision_function(rows["text"])

    rejected: collections.Counter[str] = collections.Counter()
    failures: collections.Counter[str] = collections.Counter()
    accepted_positions: list[int] = []
    api_labels: list[str] = []
    label_mismatches = score_mismatches = explanation_mismatches = 0
    confidence_values = 0
    timings: list[float] = []

    for position, text in enumerate(rows["text"]):
        started = time.perf_counter()
        response = client.post("/api/classify", json={"text": text})
        timings.append((time.perf_counter() - started) * 1000)

        # 413 and 422 are the API correctly refusing input. Anything else unexpected is a failure.
        if response.status_code in {413, 422}:
            rejected[response.json()["error"]["code"]] += 1
            continue
        if response.status_code != 200:
            failures[str(response.status_code)] += 1
            continue

        body = response.json()
        accepted_positions.append(position)
        api_labels.append(body["label"].capitalize())
        label_mismatches += body["label"] != str(direct_labels[position]).lower()
        score_mismatches += abs(body["score"] - float(direct_scores[position])) > SCORE_TOLERANCE
        explanation_mismatches += abs(explanation_total(body["explanation"]) - body["score"]) > EXPLANATION_TOLERANCE
        confidence_values += body["confidence"] is not None

    accepted = rows.iloc[accepted_positions]
    return {
        "rows_sent": int(len(rows)),
        "rows_accepted": len(accepted_positions),
        "rows_rejected_by_reason": dict(sorted(rejected.items())),
        "other_failures": sum(failures.values()),
        "other_failures_by_status": dict(sorted(failures.items())),
        "label_mismatches": int(label_mismatches),
        "score_mismatches": int(score_mismatches),
        "explanation_total_mismatches": int(explanation_mismatches),
        "responses_with_a_confidence_value": int(confidence_values),
        "metrics_on_accepted_rows": score(accepted["label"], np.array(api_labels)) if api_labels else None,
        "in_process_request_latency": {
            "median_ms": round(float(np.median(timings)), 2),
            "p95_ms": round(float(np.percentile(timings, 95)), 2),
        },
    }


def main() -> int:
    file_before = file_sha256(DEFAULT_PIPELINE_PATH)
    pipeline = load_pipeline()
    fingerprint_before = model_fingerprint(pipeline)

    with TestClient(create_app()) as client:
        if client.get("/api/health").status_code != 200:
            print(f"The API has no model: {client.get('/api/health').json()['detail']}")
            return 1
        comparison = compare_with_direct_inference(client, pipeline, load_split("validation"))

    report = {
        "split_used": "validation",
        **comparison,
        "frozen_model": {
            "file_sha256": file_before,
            "model_content_sha256": fingerprint_before,
            "file_unchanged": file_sha256(DEFAULT_PIPELINE_PATH) == file_before,
            "content_unchanged": model_fingerprint(pipeline) == fingerprint_before,
        },
    }
    write_report(report, RESULTS_PATH)
    print(json.dumps(report, indent=2, sort_keys=True))

    failed = (
        comparison["label_mismatches"]
        or comparison["score_mismatches"]
        or comparison["explanation_total_mismatches"]
        or comparison["other_failures"]
        or comparison["responses_with_a_confidence_value"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
