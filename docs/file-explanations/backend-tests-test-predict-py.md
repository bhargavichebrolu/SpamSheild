# `backend/tests/test_predict.py`

Source: [`test_predict.py`](../../backend/tests/test_predict.py).

## 1. Why the file exists

The API's trust in its model depends on verified loading, so it must be shown to refuse bad files, as well as to accept good ones.

## 2. Responsibility and design intention

It tests loading and classification without any HTTP, so a failure points directly at this logic.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The tiny saved model from `conftest.py`, including deliberately damaged copies |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_a_tampered_file_is_refused_before_it_is_loaded` | The hash check comes first, and the file is never loaded |
| `test_a_wrong_fingerprint_is_refused` | The content check works |
| `test_loading_refuses_invalid_metadata` | Bad metadata gives a clear failure |
| `test_a_model_with_unexpected_labels_is_refused` | The model's structure is checked |
| `test_classify_matches_direct_inference_from_the_pipeline` | Labels and scores match the pipeline |
| `test_label_always_agrees_with_the_sign_of_the_score` | The label and score can't contradict each other |
| `test_text_with_no_known_words_is_rejected` | Unclassifiable text is refused |
| `test_importing_the_application_imports_no_training_code` | In a fresh process, no training module is imported |
| `test_application_code_never_imports_training` | No file in `app/` has such an import |
| `test_classification_does_not_change_the_model` | Predicting leaves the model unchanged |

## 5. Key implementation decisions

- **Imports are checked by parsing:** my first version searched the text, and failed on a docstring mentioning training. Parsing checks real import statements.
- **A stand-in replaces the loader in the tamper test:** if the file were ever loaded, the test would fail.

## 6. Dependencies

`pytest`, `numpy`, and `app`.

## 7. How its output is used next

Passing tests are part of Milestone 4's acceptance check.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 260 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing only through the API | A failure wouldn't show which layer broke |
