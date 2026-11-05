# `backend/training/analyse_vocabulary.py`

Source: [`analyse_vocabulary.py`](../../backend/training/analyse_vocabulary.py).

## 1. Why the file exists

Before training, it helps to know which words most separate the labels. Some are real spam signals, and others may simply identify where a message came from.

## 2. Responsibility and design intention

It scores each word by how strongly it leans towards one label, using training rows only, so choices based on it can't be influenced by held-out data.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The training split, through `load_split("train")` |
| **Output** | `backend/reports/vocabulary_analysis.json`: the 40 strongest words each way, and a short watch list |

The report isn't in Git, because its words can include people's surnames. Run it from `backend/` with `python -m training.analyse_vocabulary`.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `log_odds_ratio` | Scores how much more likely a word is in spam than in ham. Positive means spam-leaning |
| `build_report` | Counts the rows containing each word, and ranks the words |
| `MIN_ROWS_PER_WORD` | Ignores words in fewer than 50 rows, whose scores would be unreliable |
| `WATCHED_WORDS` | Words reported regardless of rank, such as `enron` and `http` |

## 5. Key implementation decisions

- **It counts rows, not repetitions:** one message repeating a word 500 times shouldn't dominate.
- **It adds 0.5 to each count:** this avoids dividing by zero for words seen under only one label.
- **It uses `preprocess_text`:** the words scored are the ones a model would actually see.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`, `scikit-learn` (`CountVectorizer`).
- **Project files:** `preprocess.py`, `config.py`, `prepare_data.py`, and `write_report` from `inspect_dataset.py`.

## 7. How its output is used next

Milestone 3's source-leakage experiment can draw its word list from this report. The analysis also found the mismatch in my first number placeholder, because joined forms such as `shaescapenumber` appeared in its results.

## 8. Tests

Tests are in [`test_features.py`](../../backend/tests/test_features.py). Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Comparing raw frequency | The commonest words dominate, and they separate the labels poorly |
| Using a trained model's weights | Requires a model first, and depends on which model is used. This measure is simpler and independent of the model. |
| Committing the report | Its words can include people's surnames, and it can be regenerated in about 80 seconds |
