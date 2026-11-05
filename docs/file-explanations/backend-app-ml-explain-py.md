# `backend/app/ml/explain.py`

Source: [`explain.py`](../../backend/app/ml/explain.py).

## 1. Why the file exists

A label alone doesn't help anyone judge a prediction. This shows which terms moved the score, using the model's own calculation.

## 2. Responsibility and design intention

It turns one message's TF-IDF values and the model's weights into a list of term contributions. It doesn't decide the label.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | One message's sparse TF-IDF row, the weights, intercept and term names, and how many terms to list |
| **Output** | `spam_terms`, `ham_terms`, `other_terms_total`, `intercept` and `note` |

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `explain` | Calculates and ranks contributions |
| `NOTE` | States that these terms influenced the score, but don't prove why a message is or isn't spam |

## 5. Key implementation decisions

**Why this method is justified:** a Linear SVM's score is a sum:

`score = intercept + sum(TF-IDF value × learned weight)`

So each term's contribution is exact. It's the model's real calculation, not an approximation of it.

- **`other_terms_total` makes it add up:** only the strongest terms are listed, so this covers the rest, and the parts visibly equal the score.
- **Only terms in the message can appear:** so it can't reveal the removed words or the wider vocabulary.
- **Ties have a fixed order:** sorting by contribution, then term, keeps results repeatable.
- **The size of a contribution depends on the message:** TF-IDF values are scaled to each message's length, so a word's contribution differs between messages.

**What it doesn't show:** why a message is spam, what would happen if the wording changed, or that a term's influence is meaningful. It can reflect patterns specific to this dataset.

## 6. Dependencies

- **Packages:** `numpy`, `scipy`.
- **Project files:** none, which makes it easy to test alone.

## 7. How its output is used next

`predict.py`'s `classify` includes it in each result, and `routes.py` returns it. The website displays it through `TermContributions.tsx`.

## 8. Tests

Tests are in [`test_explain.py`](../../backend/tests/test_explain.py). On real data, [`verify_api.py`](../../backend/training/verify_api.py) confirmed the parts add up to the score across 18,929 validation messages. From the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| SHAP | For a linear model, it adds a library and runtime cost, without a clear benefit over the exact calculation here |
| LIME | Approximates the model by trying altered text, and results can vary between runs |
| Listing the model's strongest words overall | Wouldn't explain this message, and could expose words that include surnames |
| Listing only the top terms, with no remainder | The numbers wouldn't add up to the score |
