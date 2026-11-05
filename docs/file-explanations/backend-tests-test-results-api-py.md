# `backend/tests/test_results_api.py`

Source: [`test_results_api.py`](../../backend/tests/test_results_api.py).

## 1. Why the file exists

The results endpoints must return real values, and only permitted ones.

## 2. Responsibility and design intention

It compares responses with the committed reports, and tests the failure paths.

## 3. Inputs and outputs

Input: committed reports, and altered copies in temporary folders. Output: pass or fail.

## 4. Important functions and variables

Tests cover matching values, all 18 runs, band counts, working without a model, the licence notice, the word lists, unexpected fields and missing reports.

## 5. Key implementation decisions

The word-list test skips on a fresh copy, because those lists aren't in Git. A few words reported in a committed report are allowed, and read from that report rather than written in.

## 6. Dependencies

`pytest`, `fastapi`, and `app`.

## 7. How its output is used next

Part of the acceptance check.

## 8. Tests

From the repository root, run `python -m pytest backend`.

## 9. Alternatives considered

Testing only made-up reports would miss a mismatch with the real ones.
