# Development log

## 2026-11-05: Milestone 1, project foundation and dataset verification

**Status:** Complete. The project owner chose to proceed with the licence marked "not verified" and the Kaggle URL recorded as the reported source.

**Commit:** `bc3cdfd`

### Work completed

- Rebuilt the project from an empty folder, after the first attempt's files were deliberately cleared when the PRD moved to v2.
- Backed up the five staged files from the first attempt outside the repository and verified them against Git's hashes.
- Created `.venv` on Python 3.14.3 and installed pinned dependencies.
- Copied the dataset from the original download and verified its SHA-256.
- Wrote the inspection script and its tests, and generated the dataset report.
- Wrote the dataset card, project explanation, this log and the source-file explanations.

### Important decisions

| Decision | Reason |
|---|---|
| Keep Python 3.14.3 | In a throwaway environment, the planned packages installed from Windows wheels and a small smoke test passed |
| Keep `backend/training/` separate from API code | The API only needs to predict |
| Add `features.py` only if it has a distinct responsibility | Avoids redundant abstraction |
| Read the CSV with `keep_default_na=False` and strict UTF-8 | Keeps email text literal, and makes invalid bytes an error |
| Load the whole file instead of reading in chunks | Measured peak memory of about 0.78 GB was acceptable, and the code is simpler |
| Keep email text out of the saved report | The report is committed, and the licence is not verified |
| Proceed with the licence marked "not verified" | Project owner's decision. The raw data stays out of Git and isn't redistributed; the licence is revisited only if that changes. |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| `Activate.ps1` was blocked | PowerShell's execution policy blocked scripts. This was a Windows setting, not a Python problem. | The project owner ran `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Kaggle's page could not be read automatically | The page's content is rendered with JavaScript | The licence is recorded as "not verified" by the project owner's decision |
| Project folder was empty when v2 work began | The project owner cleared it on purpose, leaving the hidden `.git` folder | Rebuilt, reusing `.git`, after backing up the staged files |
| Python 3.14 smoke test warned that `httpx` is deprecated for FastAPI's test client | The warning suggests `httpx2` instead | Not a problem yet; to be checked in Milestone 4 when API tests are written |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 17 passed |
| `pip check` | No broken requirements |
| Dataset hash | Matches the recorded SHA-256 |
| Inspection run twice | Both exited successfully; the reports were byte-identical |
| Run time per inspection | About 26 seconds |
| Peak memory per inspection | About 0.78 GB, sampled every 500 ms |
| Comparison with the earlier one-off count | Row, label, blank-text, near-duplicate and length results agree |

Benchmarks were measured on an i7-12650H with 15.7 GB RAM, with other applications open.

The script also found a result the earlier check didn't measure: 5 near-identical texts appear under both labels, covering 11 rows.

### Remaining work

None.

## 2026-11-05: Milestone 2, data analysis, preprocessing and features

**Status:** Complete.

**Commit:** `aad0375`

### Work completed

- Analysed the text's format, and word usage on training data only.
- Built preprocessing shared by training and inference, plus cleaning and a seeded, stratified 80/10/10 split.
- Added a guard against accidentally loading the test split.
- Added named TF-IDF configurations and ran 11 experiments, starting with a controlled sample.
- Measured template similarity between validation and training rows, with scores for each similarity band.
- Wrote 62 new tests, and updated the documentation.

### Important decisions

| Decision | Reason |
|---|---|
| Convert digits to `escapenumber`, remove `escapelong`, convert `https` to `http` | Makes training text match real email and removes source and era signals. Measured cost is within noise. |
| Compare rows after preprocessing when removing duplicates | Rows that look identical to the model must not land in separate splits |
| Remove all copies of text with both labels | Neither label can be trusted |
| Keep the first 20,000 characters | Just above Ham's 99th percentile, with no meaningful effect on scores |
| Keep stop words; don't stem | Removal added no value; stemming wasn't justified by evidence |
| Don't run character n-grams on all training data | Scored below bigrams at 40,000 rows, at over 2.5 times the fit time |
| Use word unigrams and bigrams as Milestone 3's main features | Best measured result, with unigrams kept as a lighter comparison |
| Keep the random split, and report similarity bands | Clustering about 190,000 rows is costly, and repeated campaigns do occur in reality |
| Put `preprocess.py` in `app/` and `features.py` in `training/` | The saved pipeline and API need preprocessing, but not the configuration list |
| Run scripts from `backend/` with `python -m` | Matches import paths used by the future API and saved pipeline |
| Keep the vocabulary report out of Git | Its words can include people's surnames, and it can be regenerated |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| Preprocessing didn't match the dataset's joined tokens | I added spaces around the number placeholder, turning `sha1` into `sha escapenumber`. The vocabulary analysis revealed joined forms such as `shaescapenumber`. | Removed the spaces, added a test, and rebuilt the split. The split file's hash didn't change. |
| `https` could teach a misleading signal | It appears in 6.56% of Ham and 0.30% of Spam | Added a step that converts it to `http` |
| The leakage count in the report was hard-coded to 0 | The check would stop the run if it failed, so I wrote the value in directly | The report now records the measured count |
| `describe` crashed on an empty group | A test with no `escapelong` rows produced `NaN`. The real dataset doesn't trigger this. | Empty groups now report `None`, with a test |
| Character and bigram results weren't comparable | Character n-grams were scored on 5,000 validation rows and bigrams on 19,082 | Rescored character n-grams on all 19,082 rows |
| Similarity check first used only 2,000 validation rows | It started as a quick check, but the result was too important for a sample | Ran it on all rows, and added scores by band |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 79 passed |
| Split reproducibility | Rerunning preparation gave an identical split file |
| Metric reproducibility | Rerunning two experiments gave identical metrics and vocabulary sizes; timings differed |
| Rows in more than one split | 0 |
| Test split used by experiments or word analysis | No. Format analysis and cleaning read every row before the split, but they score no model and choose no features. |

Experiments were run on an i7-12650H with 15.7 GB RAM, with other applications open. Highest peak memory was 2.88 GB.

Full results are in [`feature_experiments.json`](../backend/reports/feature_experiments.json) and [`near_duplicate_check.json`](../backend/reports/near_duplicate_check.json), and are explained in the [project explanation](PROJECT_EXPLANATION.md#feature-extraction).

### Remaining work

None. Milestone 3 continued this work.

## 2026-11-05: Milestone 3, model training, comparison and evaluation

**Status:** Implemented and awaiting review.

**Commit:** Not committed yet.

### Work completed

- Committed Milestones 1 and 2 separately, after checking the author, staged files and history.
- Compared three models with three settings each, on two feature sets (18 runs), using one split.
- Derived source-marker word lists from training data, and ran marker-removal and cross-style experiments on validation data.
- Froze a final pipeline, checked reproducibility, and rehearsed the evaluation on validation data.
- Evaluated the frozen pipeline once on the test split.
- Added a model-content fingerprint, recorded separately from the file hash, without retraining or changing the frozen model.
- Wrote 83 new tests, the model card and the architecture document, and updated the other documentation.

### Important decisions

| Decision | Reason |
|---|---|
| Fix the selection rule before running any comparison | Stops a rule being adjusted to fit a favoured result |
| Linear SVM, single words, `C=10` | Result of that rule: within the F1 tie margin, with the fewest legitimate messages flagged |
| Don't overrule the rule for bigrams' higher F1 | Their F1 lead was inside the tie margin, and they flagged more legitimate messages |
| Three settings per model, using one shared matrix | Keeps tuning small and cheap, as the project owner required |
| Remove 575 likely source-marker words | A rule fixed in advance was met, narrowly. The caveats are in the model card. |
| Train the final model on the training split only | So the test result describes exactly the saved file |
| Add cross-style experiments | Random splits can't show dependence on source, and number style is the available stand-in |
| Keep the saved model and marker lists out of Git | They contain words that can include surnames, and come from a dataset with an unverified licence |
| Enforce one test run in code | A rule that can't be forgotten |
| Add a content fingerprint alongside the file hash | The file's bytes differ between identical retrains, so a file hash alone can't show two files hold the same model. Approved by the project owner. |
| Fingerprint preprocessing by its results on sample text | Catches behaviour changes, while editing a comment doesn't change the fingerprint |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| Two training runs gave different file hashes | Likely a memory address stored on the vectoriser. I first guessed Python's set ordering, then found the address in scikit-learn's source. Neither is proved. | Added `--verify-reproducible`, which confirmed identical vocabulary, IDF values, removed words, weights and validation predictions |
| I gave slightly wrong totals in a cross-style summary during the work | I quoted Ham counts from memory instead of the report | Recalculated all counts from the report before documenting them |
| Marker removal met its rule only narrowly | One cross-style improvement was only 0.0005, which is within noise | Followed the rule, and documented the caveats |
| The fingerprint crashed on some callables | Built-ins such as `str.upper` have no `__module__`. A test found this. The project's own preprocessor wasn't affected. | Fell back to the callable's type for the module name |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 162 passed |
| Retraining with `--verify-reproducible` | No learned values differ; same content fingerprint; identical predictions on 19,082 validation rows |
| Reloading in two processes with different hash seeds | Same fingerprint, and identical predictions on 19,082 validation rows |
| Frozen file while adding the fingerprint | Same hash before and after (`ed9f16df…212e862`), with no retraining |
| Validation rehearsal vs experiment | Identical: F1 0.9886, 107 flagged, 99 missed |
| Loading the real model with no training code | Worked, with no `training` modules imported |
| Second test evaluation attempt | Refused, as designed |

**Final test result, from its one run:** accuracy 0.9900, precision 0.9899, recall 0.9889, F1 0.9894, ROC-AUC 0.9987, with 91 of 10,057 Ham flagged and 100 of 9,025 Spam missed. F1 is 0.9727 on the 6,684 rows with no close training match.

**The strongest warning:** trained on digit-style rows and scored on placeholder-style rows, F1 is 0.8400, with 21.3% of Ham flagged. This doesn't prove how the model behaves on unseen sources, but it shows random-split scores can hide a real weakness.

Experiments were run on an i7-12650H with 15.7 GB RAM, with other applications open. Highest peak memory was 2.77 GB, in the bigram comparison. The final model peaked at 1.35 GB during evaluation.

### Remaining work

- Project owner to review and commit.
