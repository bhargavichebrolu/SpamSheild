# Architecture

This describes what exists now. The website doesn't exist yet, and is listed under [Planned](#planned).

## System overview

The project has two parts that share one preprocessing module and connect through saved files. Training scripts run in order to produce a saved model, and the API loads that model and serves predictions.

```text
TRAINING (runs ahead of time)                 API (runs on request)

Raw CSV (local, not in Git)                   HTTP client
   │                                             │  POST /api/classify
   ▼                                             ▼
backend/training/  ──── imports ───►  backend/app/
   │                                             │
   ▼                                             ▼
spamshield_pipeline.joblib ──── loaded at startup ──► verified model in memory
pipeline_metadata.json
backend/reports/*.json ──── read by ──► /api/model-info
```

## Training flow

Scripts run in order, and pass results through files.

```text
Raw CSV
   ├─► inspect_dataset ──► dataset_inspection.json
   ├─► analyse_format ───► format_analysis.json
   └─► prepare_data ─────► split_assignments.csv, data_preparation.json
          │  load_split(): the test split needs allow_test=True
          ├─► analyse_vocabulary (train) ──► vocabulary_analysis.json (not in Git)
          ├─► feature_experiments (train, validation) ──► feature_experiments.json
          ├─► compare_models (train, validation) ──► model_comparison.json
          ├─► source_markers (train) ──► source_markers.json (not in Git)
          └─► source_leakage (train, validation) ──► source_leakage.json
                 ▼
            config.FINAL_MODEL (set by hand from validation results)
                 ▼
            train_final (train) ──► spamshield_pipeline.joblib (not in Git)
                 │                  pipeline_metadata.json
                 ▼
            final_evaluation ──► final_validation_evaluation.json
                 │               final_test_evaluation.json (one run only)
                 ▼
            verify_api (validation) ──► api_verification.json
```

## API request flow

```text
POST /api/classify  {"text": "..."}
   │
   ▼  CORSMiddleware: allows only the website's local addresses
   ▼  BodySizeLimitMiddleware: over 256 KB gets a 413
   ▼  ClassifyRequest (Pydantic): missing, not a string, empty or over 20,000 characters gets a 422
   ▼  routes.classify_email: a model that isn't loaded gets a 503
   ▼  predict.classify
   │     preprocess_text: no usable words gets a 422
   │     TF-IDF transform: no recognised words gets a 422
   │     LinearSVC: label and score
   │     explain: each term's contribution to the score
   ▼
200  {"label", "confidence": null, "score", "model_version", "text_length",
      "terms_recognised", "explanation"}
```

The message isn't stored, logged or repeated in any response. All errors use one shape:

```json
{ "error": { "code": "text_too_long", "message": "...", "field": "text" } }
```

## Endpoints

| Endpoint | Purpose | Responses |
|---|---|---|
| `GET /api/health` | Is the API up, and is the model loaded? | `200`, or `503` with the reason |
| `POST /api/classify` | Classify one message, and explain the score | `200`, `400`, `413`, `422`, `500`, `503` |
| `GET /api/model-info` | Model details, measured results and limitations | `200`, `503` |
| `GET /docs` | Generated API documentation | `200` |

## Startup

1. `create_app` builds the application, without loading the model.
2. On startup, `load_verified_model` checks the file exists, then compares its hash with the metadata **before loading it**, because loading a tampered file could run code.
3. It loads the file, and compares the content fingerprint with the metadata.
4. It checks the model is a two-class linear model with Ham and Spam labels.
5. If anything fails, the API still starts. `/api/health` explains the problem, and model endpoints return `503`.

The model is loaded once, so requests don't reload it.

## Components

| Component | Location | Responsibility | Depends on |
|---|---|---|---|
| Application | `backend/app/main.py` | Startup, middleware and error responses | FastAPI, `app.api`, `app.ml` |
| Endpoints | `backend/app/api/routes.py` | The three endpoints, without model logic | `app.ml`, `app.schemas` |
| Schemas | `backend/app/schemas/prediction.py` | Request and response shapes | Pydantic |
| Settings | `backend/app/config.py` | Limits and allowed origins | `app.ml.preprocess` |
| Preprocessing | `backend/app/ml/preprocess.py` | Text handling for training and inference | `re` |
| Prediction | `backend/app/ml/predict.py` | Verified loading, fingerprint and classification | `joblib`, `numpy`, `scikit-learn` |
| Explanations | `backend/app/ml/explain.py` | Term contributions from the model's weights | `numpy`, `scipy` |
| Model information | `backend/app/ml/model_info.py` | Describes the model from metadata and reports | Saved reports |
| Training code | `backend/training/` | Inspection, cleaning, splitting, experiments, training, evaluation | `app.ml`, `pandas`, `numpy`, `scipy`, `scikit-learn` |
| Tests | `backend/tests/` | Automated checks, mostly on made-up data | `pytest`, `httpx2`, `uvicorn` |
| Reports | `backend/reports/` | Generated results, aggregate only when committed | Training code |
| Saved model | `backend/models/` | The fitted pipeline and its metadata | Training code |

## Key boundary

`training` imports from `app`, and never the reverse. Tests parse every file in `app/` to confirm it has no such import, and confirm that importing the application, and loading a model, imports no `training` modules.

The saved pipeline contains the fitted TF-IDF vectoriser, its reference to `app.ml.preprocess.preprocess_text`, and the classifier. So `preprocess_text` must stay at that import path, or saved models won't load.

## Safeguards built into the design

| Safeguard | Where |
|---|---|
| Dataset hash check | `verify_hash` in `inspect_dataset.py` |
| No preprocessed text in two splits | `verify_no_overlap` in `prepare_data.py` |
| Test split can't be loaded by accident | `load_split` in `prepare_data.py` |
| Selection uses validation results only | `select_best` in `models.py` |
| Evaluated file must match its frozen hash | `verify_frozen` in `final_evaluation.py` |
| Test split evaluated only once | `refuse_repeat_test_run` in `final_evaluation.py` |
| Model content can be identified separately from file bytes | `model_fingerprint` in `app/ml/predict.py` |
| API refuses a file that doesn't match its metadata | `load_verified_model` in `app/ml/predict.py` |
| Errors never repeat submitted text | `handle_validation_error` in `app/main.py` |
| Failures log only the error's type | `classify_email` in `app/api/routes.py` |
| Removed words are never exposed | `build_model_info` in `app/ml/model_info.py` |

## Planned

**Milestone 5:** a working React and TypeScript website connected to this API, which can be opened locally and used end to end. It isn't built yet.
