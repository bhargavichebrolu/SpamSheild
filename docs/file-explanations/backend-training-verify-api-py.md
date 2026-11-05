# `backend/training/verify_api.py`

Source: [`verify_api.py`](../../backend/training/verify_api.py).

## 1. Why the file exists

The project owner required API predictions to match direct inference from the frozen pipeline. This checks that on real data, at a scale tests can't.

## 2. Responsibility and design intention

It sends every validation message through the API, scores each one directly with the saved pipeline, and compares the results. It only reads the model. The test split is never loaded, because it has had its one evaluation.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The validation split, and the saved pipeline |
| **Output** | `backend/reports/api_verification.json`, with aggregate counts only |
| **Exit code** | `0` if everything matches, `1` if anything doesn't |

Run it from `backend` with `python -m training.verify_api`. It takes about a minute.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `compare_with_direct_inference` | Sends each row, and counts matches, refusals and failures |
| `explanation_total` | Adds up an explanation's parts |
| `SCORE_TOLERANCE`, `EXPLANATION_TOLERANCE` | Allow for rounding in responses |

## 5. Key implementation decisions

- **`413` and `422` count as refusals, not failures:** those are the API correctly declining input. My first version counted a `413` as a failure, and recording each status and code revealed what it was.
- **Refused rows aren't compared:** they get no prediction. Their counts are reported, so nothing disappears silently.
- **The model's identity is checked before and after:** confirming the run changed nothing.

**Actual result:** 19,082 sent, 18,929 accepted, and 153 refused (119 too long, 33 with no recognised words, 1 body too large). There were 0 label mismatches, 0 score mismatches, 0 explanation mismatches and 0 unexpected failures.

## 6. Dependencies

- **Packages:** `fastapi`, `numpy`, `pandas`.
- **Project files:** `app/main.py`, `app/ml/predict.py`, `config.py`, `evaluate.py`, `inspect_dataset.py`, `prepare_data.py`.

It's in `training/` because it needs the dataset, and `app/` must not depend on training code.

## 7. How its output is used next

It's part of Milestone 4's acceptance check, and can be rerun after any API change.

## 8. Tests

Tests are in [`test_verify_api.py`](../../backend/tests/test_verify_api.py). They confirm it detects wrong labels and scores, and only loads validation data. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing only a few made-up messages | Wouldn't cover the variety in real text |
| Using the test split | It has had its one evaluation |
| Sending requests over real HTTP | Slower, and the comparison concerns the results. A real server was tested separately. |
