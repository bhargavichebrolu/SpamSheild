# `backend/tests/test_preprocess.py`

Source: [`test_preprocess.py`](../../backend/tests/test_preprocess.py).

## 1. Why the file exists

If preprocessing changes by accident, a saved model would quietly receive different input from what it was trained on. These tests catch that.

## 2. Responsibility and design intention

It tests each preprocessing step alone, and the full function on realistic made-up text.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Short made-up strings written in the test file |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_unify_numbers` | Numbers become the placeholder, including joined forms such as `sha1` |
| `test_remove_escapelong_matches_whole_word_only` | `escapelongest` isn't altered |
| `test_unify_url_scheme` | `https` becomes `http`, and `httpsx` isn't altered |
| `test_preprocess_makes_real_style_email_match_the_dataset_style` | Capitals, digits, spacing and `HTTPS` all work together |
| `test_preprocess_limits_length` | Output stays within the limit |
| `test_preprocess_is_stable_when_repeated` | Preprocessing short messages twice gives the same result as once |

## 5. Key implementation decisions

- **`sha1` has its own test:** it records the bug in my first version, so it can't quietly return.
- **Parametrised tests:** one test runs against several inputs, keeping cases short and easy to add to.

## 6. Dependencies

`pytest` and `app.ml.preprocess`.

## 7. How its output is used next

Passing tests are part of Milestone 2's acceptance check, and they protect the saved pipeline in later milestones.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 79 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Testing only the full function | A failure wouldn't show which step broke |
| Using real dataset messages | Slower, needs a file that isn't in Git, and could put real email in the repository |
