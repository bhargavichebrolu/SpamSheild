# `backend/training/source_markers.py`

Source: [`source_markers.py`](../../backend/training/source_markers.py).

## 1. Why the file exists

The source-leakage experiment needs a list of words that may reveal a message's source. The sources aren't verified, so there's no true list, and this builds a documented estimate.

## 2. Responsibility and design intention

It ranks words from **training rows only**, so held-out data can't influence the list.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | The training split |
| **Output** | `backend/reports/source_markers.json`: three ranked lists of up to 1,000 words, with their hashes (not in Git) |

Run it from `backend` with `python -m training.source_markers`.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `styles_of` | Finds each raw message's number style. It needs raw text, because preprocessing hides the difference |
| `rank_words` | Orders words by score, with alphabetical ties, so the result is repeatable |
| `derive_markers` | Builds the three lists |
| `list_hash` | Identifies a list without revealing its words |
| `load_markers` | Reads the saved lists |

## 5. How each list is created

Only words in at least 50 training rows are scored.

| List | Rule |
|---|---|
| `style_leaning` | Calculate the log-odds of each word between digit-style and placeholder-style rows, separately for Ham and Spam. Keep the larger absolute value, and rank by it |
| `ham_leaning` | Rank by log-odds between labels, leaning towards Ham |
| `spam_leaning` | Rank by log-odds between labels, leaning towards Spam |

**Key decisions:**
- **Measuring style within each label:** this stops a word scoring highly just because one style has more spam.
- **Reports hold hashes, not words:** the lists can include people's surnames, so they're excluded from Git.

**These are estimates.** Style-leaning words include list and organisation terms, but also disguised spellings such as `technoiogy`, which may be real spam signals.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`, `scikit-learn`.
- **Project files:** `preprocess.py`, `analyse_format.py`, `analyse_vocabulary.py`, `config.py`, `inspect_dataset.py`, `prepare_data.py`.

## 7. How its output is used next

`source_leakage.py` retrains without these words, and `train_final.py` excludes the 575 words chosen for the final model.

## 8. Tests

Tests are in [`test_source_markers.py`](../../backend/tests/test_source_markers.py), including one confirming it requests only the training split. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| A hand-written list | Open to bias, and would reflect what I noticed in the data, including from earlier checks |
| Using a model's weights | Depends on the model, and can't separate source from topic any better |
| Using validation data too | Would let held-out data shape the experiment |
