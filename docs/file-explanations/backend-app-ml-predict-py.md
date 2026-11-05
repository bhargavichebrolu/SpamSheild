# `backend/app/ml/predict.py`

Source: [`predict.py`](../../backend/app/ml/predict.py).

## 1. Why the file exists

The API will need to load the saved model without any training code. This gives it one small, clear way to do that.

## 2. Responsibility and design intention

It finds, verifies and loads the saved pipeline, calculates a fingerprint of what the pipeline contains, and classifies messages.

## 3. Inputs and outputs

| | Details |
|---|---|
| **`load_pipeline`** | Takes a file path, by default `backend/models/spamshield_pipeline.joblib`. Returns a fitted `Pipeline`, or raises `FileNotFoundError` with the command to create the file |
| **`load_verified_model`** | Takes the pipeline and metadata paths. Returns a `LoadedModel`, or raises `ModelUnavailable` with a message safe to show |
| **`model_fingerprint`** | Takes a fitted `Pipeline`. Returns a SHA-256 string |
| **`classify`** | Takes a `LoadedModel` and text. Returns the label, score, recognised term count and explanation, or raises `ClassificationRejected` |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `MODELS_DIR`, `DEFAULT_PIPELINE_PATH` | Where the model is saved, worked out from this file's location |
| `PREPROCESSING_PROBES` | Fixed strings used to include preprocessing behaviour in the fingerprint |
| `load_pipeline` | Loads the file, or explains how to create it |
| `model_fingerprint` | Hashes what the pipeline learned and how it's configured |
| `_pipeline_configuration` | Collects the settings that affect predictions |
| `_callable_name` | Gives a function's import path, because its `repr` includes a memory address |
| `LoadedModel` | A verified pipeline, with the weights, intercept and term names explanations need |
| `ModelUnavailable`, `ClassificationRejected` | The two expected failures, which the API turns into clear responses |
| `load_verified_model` | Checks the file, loads it, then checks its contents |
| `classify` | Produces a label, score and explanation for one message |

## 5. Key implementation decisions

- **It's in `app/`:** so the API can use it without importing `training`.
- **The hash is checked before loading:** because loading a tampered file could run code. A test confirms a tampered file is never loaded.
- **Text with no recognised words is rejected:** the score would just be the intercept, which leans towards spam, so a label would say nothing about the message.
- **Package version differences are logged:** not refused, because the fingerprint already catches any change in the stored values.
- **A helpful error:** the model isn't in Git, so a missing file is a normal situation in a fresh copy of the repository.
- **A warning about trust:** the `joblib` format can run code when loaded, so only a file this project created should be loaded.

**How the fingerprint stays stable:**
- **It reads values, not the file:** so it doesn't depend on how the file was written.
- **Everything has a fixed order and encoding:** the vocabulary and removed words are sorted, JSON keys are sorted, and arrays are written as little-endian 64-bit floats.
- **Settings are chosen explicitly:** a vectoriser's full settings include a function whose `repr` has a memory address, which would change each run.
- **Each section's length is included:** so content from one section can't be mistaken for another's.
- **Preprocessing is checked by its results:** editing a comment doesn't change the fingerprint, while a change in behaviour on the sample strings does.

The [model card](../model-card.md#two-hashes-identify-the-model) explains the difference between this and the file hash.

## 6. Dependencies

- **Packages:** `joblib`, `numpy`, `scikit-learn`.
- **Project files:** `app/config.py`, `app/ml/explain.py`, `app/ml/preprocess.py`.
- **At load time:** `app.ml.preprocess`, because the saved pipeline refers to `preprocess_text` by its import path.

## 7. How its output is used next

`main.py` loads the model at startup, and `routes.py` calls `classify`. `final_evaluation.py` and `train_final.py` also use it.

## 8. Tests

Tests are in [`test_predict.py`](../../backend/tests/test_predict.py) and [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py). One starts a fresh Python process, and confirms a saved pipeline loads and predicts with no `training` modules imported. From the repository root:

```powershell
python -m pytest backend
```

To load the real model, from `backend`:

```powershell
python -c "from app.ml.predict import load_pipeline; print(load_pipeline().predict(['Example message text']))"
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Saving each part in a separate file | They could get out of step. One `Pipeline` guarantees inference matches training. |
| ONNX or another portable format | Adds complexity, and `preprocess_text` is custom Python |
| Loading the model at import time | Would make importing slow, and fail in tests. Loading on request is simpler to control. |
| Hashing the pickled model again | Would still depend on bytes such as the stored memory address |
| Hashing the preprocessing source code | Editing a comment would change the fingerprint, with no change in behaviour |
