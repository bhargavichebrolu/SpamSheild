# `backend/training/source_leakage.py`

Source: [`source_leakage.py`](../../backend/training/source_leakage.py).

## 1. Why the file exists

A random split can't show whether a model has learned where messages came from, because every split contains the same sources. This measures that dependence in two other ways.

## 2. Responsibility and design intention

It retrains the selected model under controlled changes, and scores on validation rows. **It doesn't prove generalisation to unseen sources**, and the report's `interpretation_note` says so.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Training and validation splits, `model_comparison.json`, and `source_markers.json` |
| **Output** | `backend/reports/source_leakage.json`: metrics, counts and list hashes, with no words |

Run it from `backend` with `python -m training.source_leakage`. It took about 14 minutes. Add `--decide` to reapply the rule to saved results without retraining.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `MARKER_REMOVALS` | The word-removal experiments |
| `CROSS_STYLE_RUNS` | The train-on-one-style experiments |
| `CANDIDATE_REMOVAL` | The removal considered for the final model |
| `run_marker_removal` | Retrains without some words, and scores on validation rows |
| `run_cross_style` | Trains on one style, and scores on each style's validation rows |
| `decide_removal` | Applies the rule fixed in advance |
| `INTERPRETATION_NOTE` | The limit on what these results show |

## 5. Key implementation decisions

- **Words are removed before forming features:** using TF-IDF's `stop_words`, so they can't contribute.
- **A matched-size run:** placeholder-style data is sampled down to the digit style's 20,196 rows, to separate the effect of style from the effect of size.
- **The rule was fixed before any result:** use the removal only if validation F1 stays within 0.002, and cross-style F1 improves in both directions.
- **The list knows both styles:** it was built from all training rows, which flatters the cross-style improvement, and the model card says so.

## 6. Dependencies

- **Packages:** `pandas`, `scikit-learn`.
- **Project files:** `compare_models.py`, `config.py`, `evaluate.py`, `feature_experiments.py`, `features.py`, `inspect_dataset.py`, `models.py`, `prepare_data.py`, `source_markers.py`.

## 7. How its output is used next

Its decision set the word removal in `FINAL_MODEL`, and its results are the main limitation in the [model card](../model-card.md#source-leakage).

## 8. Tests

Tests are in [`test_final_pipeline.py`](../../backend/tests/test_final_pipeline.py). They cover list combining, removal from the vocabulary, training on the named style, the decision rule, and that only train and validation are requested. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing on another email dataset | The most useful next step, but outside this milestone's agreed scope, and it would need its own licence check |
| Holding out a whole source | The sources aren't verified, so number style is the available stand-in |
| Only removing words | Scores barely changed, which would have hidden the much larger cross-style drop |
