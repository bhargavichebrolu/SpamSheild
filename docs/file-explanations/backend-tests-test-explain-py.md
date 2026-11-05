# `backend/tests/test_explain.py`

Source: [`test_explain.py`](../../backend/tests/test_explain.py).

## 1. Why the file exists

An explanation that's wrong would be worse than none, so its arithmetic needs checking.

## 2. Responsibility and design intention

It tests `explain` with small hand-worked numbers, then against a fitted model's real score.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Small arrays with known answers, and the tiny model from `conftest.py` |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_contribution_is_the_tfidf_value_times_the_weight` | The core calculation |
| `test_parts_add_up_to_the_score_even_when_terms_are_left_out` | `other_terms_total` covers what isn't listed |
| `test_only_terms_in_the_message_appear` | The wider vocabulary isn't exposed |
| `test_ties_have_a_repeatable_order` | Results are repeatable |
| `test_explanation_adds_up_to_the_real_models_score` | It matches the classifier's own score |
| `test_explanation_never_shows_a_removed_word` | Removed words don't appear |
| `test_note_does_not_claim_certainty` | The wording stays cautious |

## 5. Key implementation decisions

- **Hand-worked numbers:** so the test can't just repeat what the code does.
- **A real classifier too:** confirming the calculation matches `decision_function`, and isn't only consistent with itself.

## 6. Dependencies

`pytest`, `numpy`, `scipy`, and `app`.

## 7. How its output is used next

Passing tests are part of Milestone 4's acceptance check.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 290 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Checking only with real data | Couldn't confirm individual contributions independently |
