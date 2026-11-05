# `backend/tests/test_models.py`

Source: [`test_models.py`](../../backend/tests/test_models.py).

## 1. Why the file exists

The selection rule decides which model is used, so a mistake in it would silently pick the wrong one.

## 2. Responsibility and design intention

It tests the candidates, each step of the selection rule, and the shared metrics, using tiny made-up data.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Six made-up messages, and hand-written result dictionaries |
| **Output** | Pass or fail results from `pytest` |

## 4. Important functions and variables

| Test | What it checks |
|---|---|
| `test_every_candidate_fits_and_separates_simple_text` | Every model and setting works |
| `test_select_best_picks_clear_f1_winner_despite_more_flagged_ham` | A real F1 lead wins |
| `test_select_best_breaks_f1_ties_by_fewest_flagged_ham` | The tie-break favours fewer false alarms |
| `test_select_best_ignores_runs_that_did_not_converge` | A failed fit can't win |
| `test_spam_scores_rank_spam_above_ham_for_every_candidate` | The score direction is right for each model type |
| `test_comparison_never_loads_the_test_split` | Only train and validation are requested |

## 5. Key implementation decisions

- **Each rule step has its own test:** a failure shows exactly which step broke.
- **Results are written by hand:** so the rule can be tested without training anything.

## 6. Dependencies

`pytest`, `numpy`, `pandas`, `scikit-learn`, and the project's `compare_models`, `evaluate` and `models` modules.

## 7. How its output is used next

Passing tests are part of Milestone 3's acceptance check.

## 8. Tests and how to run them

```powershell
python -m pytest backend
```

Result on 2026-11-05: the full suite of 290 tests passed.

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Asserting a specific model always wins | Would tie the test to one dataset's results, not to the rule |
| Testing on the real dataset | Slow, and it needs a file that isn't in Git |
