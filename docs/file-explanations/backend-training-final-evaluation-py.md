# `backend/training/final_evaluation.py`

Source: [`final_evaluation.py`](../../backend/training/final_evaluation.py).

## 1. Why the file exists

A test set only means something if it's used once, on a model that's already fixed. This script enforces that in code.

## 2. Responsibility and design intention

It evaluates the saved, frozen pipeline, and it never fits or changes a model.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The saved pipeline, its metadata, and the chosen split |
| **Output** | `backend/reports/final_validation_evaluation.json`, or `final_test_evaluation.json` |
| **Exit code** | `0` on success, `1` if a safeguard refuses |

Run from `backend`:

```powershell
python -m training.final_evaluation --split validation
```

The test run has already been used, so `--split test` now stops with an error.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `verify_frozen` | Refuses if the pipeline or split file differs from what was recorded at freezing |
| `refuse_repeat_test_run` | Refuses if a test report already exists |
| `class_results` | Precision, recall and error rates for each class |
| `single_message_latency` | Times one-message-at-a-time prediction |
| `build_report` | Metrics, similarity bands with sample counts, and latency, with no email text |

## 5. Key implementation decisions

- **Checks run first:** a repeat test run is refused before any rows load, and a test confirms it.
- **The same code runs on validation first:** the rehearsal found no bugs, and matched the experiment's numbers exactly, so the one test run couldn't be wasted.
- **It loads the saved file:** the result describes the actual file, not an in-memory model.
- **The report is written last:** a crash can't leave a report without a completed evaluation.

**Limit of the guard:** it stops accidental reruns. Someone could still delete the report and run again, so the discipline also relies on not doing that. The report's presence in Git makes that visible.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`.
- **Project files:** `predict.py`, `config.py`, `evaluate.py`, `feature_experiments.py`, `inspect_dataset.py`, `prepare_data.py`, `train_final.py`.

## 7. How its output is used next

Its results are in the [model card](../model-card.md), and the website can display the report in Milestone 5.

## 8. Tests

Tests are in [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py). From the repository root:

```powershell
python -m pytest backend
```

**Real results:** the validation rehearsal gave F1 0.9886, matching the experiment. The single test run gave F1 0.9894. A second test attempt was refused, as designed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Relying on a rule in the documentation | Easy to break by accident |
| Evaluating inside the training script | Would blur the line between fixing a model and judging it |
