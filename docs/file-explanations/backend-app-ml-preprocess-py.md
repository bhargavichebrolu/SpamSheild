# `backend/app/ml/preprocess.py`

Source: [`preprocess.py`](../../backend/app/ml/preprocess.py). `backend/app/__init__.py` and `backend/app/ml/__init__.py` are empty files that let Python import these folders as packages.

## 1. Why the file exists

Predictions must use the same text handling as training. Keeping that logic in one function means they can't drift apart.

## 2. Responsibility and design intention

It turns one message into the form the model expects. The dataset's text was processed before this project received it, so these steps make real email look more like that text, and remove what real email can't match.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | One string of raw message text |
| **Output** | One string: lowercase, with numbers as `escapenumber`, no `escapelong`, `https` as `http`, single spaces, at most 20,000 characters before the replacements |

For example, `"WIN  $500 at\nHTTPS://Example.com TODAY!"` becomes `"win $escapenumber at http://example.com today!"`.

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `MAX_TEXT_CHARS` | Characters kept from each message: 20,000 |
| `NUMBER_PLACEHOLDER` | The dataset's own placeholder, `escapenumber` |
| `truncate`, `unify_numbers`, `remove_escapelong`, `unify_url_scheme`, `collapse_whitespace` | One transformation each, so the experiments can test them separately |
| `preprocess_text` | Applies all the steps in order. This is the function the project uses |

## 5. Key implementation decisions

- **It lives in `app/`:** a saved pipeline refers to `preprocess_text` by its import path, so the API must be able to import it without training code.
- **Truncation comes first:** it limits the regular-expression work on a message of about 11.5 million characters.
- **Lowercasing comes before the replacements:** so capitalised forms like `HTTPS` and `EscapeLong` also match.
- **No spaces around the placeholder:** the dataset has joined forms such as `shaescapenumber`. My first version added spaces, which didn't match, and the vocabulary analysis revealed this.
- **`https` becomes `http`:** the word appears in 6.56% of Ham and 0.30% of Spam. Modern spam commonly uses `https`, so learning this pattern would be misleading.
- **`escapelong` is removed rather than reproduced:** rows containing it still have tokens up to 77 characters long, so its rule isn't clear.
- **Repeating it normally changes nothing:** preprocessing already-preprocessed text gives the same result, and a test checks this on short messages. The exception is a message near the length cap, because placeholders can lengthen it past 20,000 characters and a second pass would cut it again. The project only applies preprocessing once.

## 6. Dependencies

Only `re` from the standard library. It imports nothing from the project, which keeps the API's dependencies small.

## 7. How its output is used next

- `prepare_data.py` uses it to find rows that look identical to the model.
- `features.py` passes it to TF-IDF, so it runs automatically during fitting and prediction.
- Milestone 4's API will use it through the saved pipeline.

## 8. Tests

Tests are in [`test_preprocess.py`](../../backend/tests/test_preprocess.py). Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Keep the data's formatting as it is | Real email would then differ from training text, and digits vs placeholder could reveal a message's source |
| Remove all numbers | Loses whether a message contains numbers, which may be useful |
| Remove stop words | No measured benefit on the sample (F1 0.9608 vs 0.9609) |
| Stemming or lemmatisation | Not tested: adds a dependency, without evidence of need on text with placeholders and fragments |
| Choose steps by validation score alone | Leaked source signals raise validation scores, so the score can favour the less realistic option |
