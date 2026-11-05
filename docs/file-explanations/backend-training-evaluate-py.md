# `backend/training/evaluate.py`

Source: [`evaluate.py`](../../backend/training/evaluate.py).

## 1. Why the file exists

Experiments, model comparison and the final evaluation must measure results in exactly the same way. Sharing the code makes that automatic.

## 2. Responsibility and design intention

It calculates metrics and similarity, and it doesn't load data, fit models or write files.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | True labels, predictions, ranking scores, or TF-IDF matrices |
| **Output** | Dictionaries of metrics, or arrays of similarity values |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `score` | Accuracy, precision, recall and F1 with Spam as the positive class, plus confusion counts |
| `spam_scores` | A value ranking rows from least to most spam-like, for any candidate model |
| `roc_auc` | The chance a random spam row ranks above a random ham row |
| `closest_training_similarity` | Each row's cosine similarity to its most similar training row |
| `similarity_to_training` | Fits word TF-IDF on training text, then calls the function above |
| `shares_at_or_above` | The share of rows reaching each similarity |
| `score_by_similarity_band` | Metrics and sample counts for each similarity group |

## 5. Key implementation decisions

- **Spam is always the positive class:** so precision and recall mean the same thing everywhere.
- **`spam_scores` handles two model types:** Linear SVM and Logistic Regression use `decision_function`, while Naive Bayes uses `predict_proba`. These values rank rows within one model, but can't be compared across models.
- **Similarity runs in batches:** multiplying large sparse matrices can use a lot of memory.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`, `scipy`, `scikit-learn`.
- **Project files:** `features.py`.

## 7. How its output is used next

`feature_experiments.py`, `compare_models.py`, `source_leakage.py` and `final_evaluation.py` use it, and its results appear in the [model card](../model-card.md).

## 8. Tests

Tests are in [`test_models.py`](../../backend/tests/test_models.py) and [`test_features.py`](../../backend/tests/test_features.py). From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Keeping these in `feature_experiments.py` | The final evaluation would have to import from an experiment script |
| Reporting accuracy alone | It hides the two error types, which have different costs |
