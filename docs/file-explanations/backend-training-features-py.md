# `backend/training/features.py`

Source: [`features.py`](../../backend/training/features.py).

## 1. Why the file exists

The approved plan allows this file only if it has a distinct responsibility. Its job is to define each TF-IDF configuration once, so experiments and Milestone 3's training use identical settings.

## 2. Responsibility and design intention

It maps a name such as `word_1_2` to its settings, and builds an unfitted vectoriser. It doesn't fit anything or read data.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | A configuration name and, optionally, a different preprocessing function |
| **Output** | An unfitted scikit-learn `TfidfVectorizer` |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `FEATURE_SETS` | The configurations: `word_1`, `word_1_2`, `word_1_2_stop`, `char_3_5` |
| `build_vectorizer` | Returns a vectoriser for a named configuration |

| Setting | Meaning |
|---|---|
| `ngram_range` | Term lengths, so `(1, 2)` means single words and pairs |
| `min_df` | Ignores terms in fewer than this many messages |
| `max_df=0.95` | Ignores terms in over 95% of messages |
| `max_features=300_000` | Keeps at most this many of the most frequent terms |
| `sublinear_tf=True` | Dampens repetition within a message |
| `char_wb` | Character n-grams built within word boundaries |

## 5. Key implementation decisions

- **It's in `training/`, not `app/ml/`:** a saved pipeline contains its fitted vectoriser, so the API doesn't need this file.
- **`dtype=float32`:** this uses half the memory of the default, with ample precision for these values.
- **`lowercase=False`:** `preprocess_text` already lowercases.
- **`preprocessor` is a parameter:** experiments can measure other preprocessing, while the default is the project's own function.

## 6. Dependencies

- **Packages:** `numpy`, `scikit-learn`.
- **Project files:** `preprocess.py`.

## 7. How its output is used next

`feature_experiments.py`, `compare_models.py`, `source_leakage.py`, `evaluate.py` and `train_final.py` all build vectorisers from it. The final model uses `word_1`.

## 8. Tests

Tests are in [`test_features.py`](../../backend/tests/test_features.py). They confirm that every configuration builds, that the vocabulary comes only from fitted text, that preprocessing runs at inference, and that a fitted vectoriser survives saving and reloading. Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| `app/ml/features.py`, as in the PRD's outline | The API doesn't need it, and this would add training-only code to the application |
| A custom wrapper class | `TfidfVectorizer` already does the work, so a wrapper would be redundant |
| Keeping settings in `feature_experiments.py` | Milestone 3's training would then have to import from an experiment script |
| `HashingVectorizer` | Saves memory, but can't map features back to words, which explanations need |
