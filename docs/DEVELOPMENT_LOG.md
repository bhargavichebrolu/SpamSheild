# Development log

## 2026-11-05: Milestone 1, project foundation and dataset verification

**Status:** Complete. The project owner chose to proceed with the licence marked "not verified" and the Kaggle URL recorded as the reported source.

**Commit:** Not committed yet.

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

- Project owner to review and commit.

## 2026-11-05: Milestone 2, data analysis, preprocessing and features

**Status:** Implemented and awaiting review.

**Commit:** Not committed yet.

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

- Project owner to review and commit.
- Milestone 3: compare candidate models, run the source-leakage experiment, evaluate once on the test split, and save the selected pipeline.
