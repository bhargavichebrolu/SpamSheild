# `backend/training/train_final.py`

Source: [`train_final.py`](../../backend/training/train_final.py).

## 1. Why the file exists

It turns the chosen configuration into the one saved file that inference needs, along with a record of exactly how it was made.

## 2. Responsibility and design intention

It fits `FINAL_MODEL` on training rows only, so the test result describes exactly the saved file. It also checks reproducibility without replacing that file.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The training split, `FINAL_MODEL`, and `source_markers.json` |
| **Output** | `backend/models/spamshield_pipeline.joblib` (3.5 MB, not in Git) |
| **Output** | `backend/models/pipeline_metadata.json`: settings, the file hash, the content fingerprint, versions, and the removed words' count and hash |

Run from `backend`:

```powershell
python -m training.train_final
python -m training.train_final --verify-reproducible
python -m training.train_final --verify-fingerprint
python -m training.train_final --record-fingerprint
```

Only the first command **replaces the saved model and its metadata**, and training took about 80 seconds. The second and third change nothing. The fourth changes only the metadata's fingerprint.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `final_removed_words` | Returns the words to exclude, from the training-only lists |
| `build_final_pipeline` | Returns the unfitted pipeline |
| `save_pipeline` | Saves it, and returns the file's hash |
| `build_metadata` | Records how the file was made |
| `learned_values_differences` | Compares what two fitted pipelines learned |
| `verify_reproducible` | Refits without saving, and compares learned values, fingerprints and predictions with the saved pipeline |
| `record_fingerprint` | Adds the fingerprint to the metadata, refusing if the saved file doesn't match it |
| `verify_fingerprint` | Checks the saved file against its metadata, and prints a hash of its validation predictions |

## 5. Key implementation decisions

- **Training rows only:** refitting on more data would make the test result describe a different model.
- **Comparing learned values, not files:** two runs saved different bytes, while learning identical values. The likely cause, not yet proved, is a memory address scikit-learn stores on the vectoriser.
- **Removed words aren't in the metadata:** only their count and hash, because they can include surnames.
- **Two separate hashes:** `pipeline_sha256` identifies the file, and `model_content_sha256` identifies the model. The [model card](../model-card.md#two-hashes-identify-the-model) explains the difference.
- **The fingerprint was added without retraining:** `record_fingerprint` only reads the frozen file, and refuses if that file isn't the one the metadata describes.

## 6. Dependencies

- **Packages:** `joblib`, `numpy`, `scikit-learn`.
- **Project files:** `predict.py`, `config.py`, `feature_experiments.py`, `features.py`, `inspect_dataset.py`, `models.py`, `prepare_data.py`, `source_leakage.py`, `source_markers.py`.

## 7. How its output is used next

`final_evaluation.py` evaluates the saved file, and the API is expected to load it in Milestone 4.

## 8. Tests

Tests are in [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Refitting on train and validation together | Slightly more data, but the test result wouldn't describe a model that had been validated |
| Committing the model file | Contains words that can include surnames, comes from a dataset with an unverified licence, and can be regenerated |
| Requiring identical file bytes | Not currently achievable, and comparing learned values answers the real question |
