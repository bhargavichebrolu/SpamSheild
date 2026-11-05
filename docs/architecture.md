# Architecture

This describes what exists now. The API and website don't exist yet, and are listed under [Planned](#planned).

## Current system

The project is a set of Python scripts that run in order and pass results through files. Nothing runs as a service yet.

```text
Raw CSV (local, not in Git)
   │
   ├─► inspect_dataset ──► dataset_inspection.json
   ├─► analyse_format ───► format_analysis.json
   │
   └─► prepare_data ─────► split_assignments.csv, data_preparation.json
          │  load_split(): the test split needs allow_test=True
          │
          ├─► analyse_vocabulary (train) ──► vocabulary_analysis.json (not in Git)
          ├─► feature_experiments (train, validation) ──► feature_experiments.json
          ├─► compare_models (train, validation) ──► model_comparison.json
          ├─► source_markers (train) ──► source_markers.json (not in Git)
          └─► source_leakage (train, validation) ──► source_leakage.json
                 │
                 ▼
            config.FINAL_MODEL (set by hand from validation results)
                 │
                 ▼
            train_final (train) ──► spamshield_pipeline.joblib (not in Git)
                 │                  pipeline_metadata.json
                 ▼
            final_evaluation ──► final_validation_evaluation.json
                                 final_test_evaluation.json (one run only)
```

## Components

| Component | Location | Responsibility | Depends on |
|---|---|---|---|
| Inference code | `backend/app/ml/` | Preprocessing, and loading the saved pipeline | `re`, `joblib`, `scikit-learn` |
| Training code | `backend/training/` | Inspection, cleaning, splitting, experiments, training, evaluation | `app.ml`, `pandas`, `numpy`, `scipy`, `scikit-learn` |
| Tests | `backend/tests/` | Automated checks on made-up data | `pytest` |
| Reports | `backend/reports/` | Generated results, aggregate only when committed | Training code |
| Saved model | `backend/models/` | The fitted pipeline and its metadata | Training code |

## Key boundary

`training` imports from `app`, and never the reverse. A test confirms a saved pipeline loads and predicts with no `training` modules imported.

The saved pipeline contains the fitted TF-IDF vectoriser, its reference to `app.ml.preprocess.preprocess_text`, and the classifier. So `preprocess_text` must stay at that import path, or saved models won't load.

## Inference data flow

```text
Raw message text
   ▼ preprocess_text: cap length, lowercase, unify numbers and http, collapse whitespace
   ▼ TF-IDF: word weights from the fitted vocabulary, excluding the 575 removed words
   ▼ LinearSVC: score from the weights
Label: Spam or Ham
```

## Safeguards built into the design

| Safeguard | Where |
|---|---|
| Dataset hash check | `verify_hash` in `inspect_dataset.py` |
| No preprocessed text in two splits | `verify_no_overlap` in `prepare_data.py` |
| Test split can't be loaded by accident | `load_split` in `prepare_data.py` |
| Selection uses validation results only | `select_best` in `models.py` |
| Evaluated file must match its frozen hash | `verify_frozen` in `final_evaluation.py` |
| Model content can be identified separately from file bytes | `model_fingerprint` in `app/ml/predict.py` |
| Test split evaluated only once | `refuse_repeat_test_run` in `final_evaluation.py` |

## Planned

These aren't built yet, and will be described here once they exist:

- **Milestone 4:** a FastAPI backend that loads the saved pipeline and provides classification and explanations.
- **Milestone 5:** a working React and TypeScript website connected to that backend, which can be opened locally and used end to end.
