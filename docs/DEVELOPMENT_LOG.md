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

**Status:** Complete.

**Commit:** `1f4dd8c`

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

None. Milestone 4 continued this work.

## 2026-11-05: Milestone 4, FastAPI backend and prediction pipeline

**Status:** Complete.

**Commit:** `620d9c2`

### Work completed

- Committed Milestone 3 as `1f4dd8c`, at the project owner's request, after their pre-commit checks passed.
- Built health, classify and model-info endpoints, with request validation and one error shape.
- Added verified model loading: file hash before loading, then content fingerprint and structure.
- Added explanations calculated from the model's own weights.
- Wrote 98 new tests, and a tool comparing API results with direct inference.
- Tested a real server over HTTP.
- Updated the architecture, project explanation, model card, README and source-file logs.

The frozen model wasn't retrained or modified. Its file hash stayed `ed9f16df…212e862`, and its content fingerprint stayed `6f5135d9…a10c2e2`.

### Important decisions

| Decision | Reason |
|---|---|
| Reject text over 20,000 characters | The model only reads that many, so accepting more would silently ignore part of the message. Required by the project owner. |
| `confidence` is always `null` | A Linear SVM doesn't provide a meaningful probability. Required by the project owner. |
| Term contributions as the explanation | They're the model's own calculation and add up exactly to the score, so no approximation or extra library is needed |
| Check the file's hash before loading it | Loading a tampered file could run code |
| Reject text with no recognised words | The score would just be the intercept, so the label would say nothing about the message |
| Keep the API running without a model | `/api/health` can then explain the problem, rather than the server failing to start |
| Replace FastAPI's validation errors | The defaults repeat the rejected input, which could be someone's email |
| Add `model_info.py`, which wasn't in the plan | Keeps reading reports out of the endpoints, and results come from generated reports rather than being written by hand |
| Use `httpx2` for the test client | Starlette has deprecated `httpx` for this, which settled the warning from Milestone 1's checks |
| Compare against direct inference on validation data only | The test split has had its one evaluation |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| Oversized uploads got a connection reset instead of a `413` | The middleware replied while the client was still sending. Only real HTTP showed this; the test client can't. | Read and discard the rest of the upload, up to 16 MB, before replying. Added a test using a real server. |
| One validation row appeared as a failure in the comparison | It was over 256 KB, so it correctly got a `413`, which my tool counted as a failure | Changed the tool to record each status and code, and confirmed this by rerunning it |
| A test for training imports failed on a docstring | It searched file text, and matched the phrase "imports from training/" | Parsed real import statements instead |
| A test expected 3 failures, and got 5 | My expectation was wrong: when classification is fully broken, the rejections inside it fail too | Corrected the test |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 260 passed |
| Every validation message through the API (19,082) | 18,929 accepted and 153 correctly refused, with 0 label mismatches, 0 score mismatches, 0 explanation mismatches and 0 unexpected failures |
| Real server start | About 3 seconds, peak memory about 0.24 GB |
| Real HTTP latency, 300 requests with a new connection each | Median 16 ms, 95th percentile 28 ms |
| All error types over real HTTP | Correct status, code and message |
| Marker word in submitted text | Not in any response or server log |
| CORS | Local website address allowed, another origin not |
| Frozen model | Same file hash and fingerprint throughout |

Latency was measured on an i7-12650H with other applications open. The results of [`verify_api.py`](../backend/reports/api_verification.json) are saved as a report.

### Remaining work

None. Milestone 5 continued this work.

## 2026-11-05: Milestone 5, React web application and explainability

**Status:** Complete.

**Commit:** `908a5fb`

### Work completed

- Committed Milestone 4 as `620d9c2`, at the project owner's request, after their pre-commit checks passed.
- Added two read-only results endpoints, whose schemas act as an allowlist.
- Built a React and TypeScript website with Classifier, Models and Dataset pages, connected to the real API.
- Added loading, validation and error states, the short-message caution, and responsive layouts.
- Wrote 90 frontend unit tests, 54 browser tests and 30 new backend tests, and captured screenshots of the actual pages.
- Updated the architecture, project explanation, PRD, README and source-file logs.

The frozen model, its metadata and the training pipeline weren't changed. The file hash stayed `ed9f16df…212e862`, and the content fingerprint stayed `6f5135d9…a10c2e2`.

### Important decisions

| Decision | Reason |
|---|---|
| Add `/api/results/models` and `/api/results/dataset` | The existing API couldn't serve these pages. Approved by the project owner. |
| Label the raw score a decision score | It isn't a probability. Required by the project owner. |
| Caution below 5 recognised words | The intercept leans towards spam. The threshold is a display warning, not a measured boundary, and it doesn't change the prediction. Approved by the project owner. |
| Defer prediction history | Optional in the PRD, and it adds storage and privacy work. Decided by the project owner. |
| Call the API directly, not through a proxy | Exercises the real CORS rules |
| One file for all network calls | Failure handling stays in one place, and a test can check this |
| Build charts from plain HTML and CSS | The bars are simple, and every value is also written as text |
| Validate the Ham and Spam colours with a script | Colour-vision safety was checked by calculation, not by eye, in both modes |
| No text on coloured fills | White text on those colours would fail contrast checks |
| Browser tests against the real backend | A stubbed API couldn't catch a real mismatch |
| Use the installed Edge browser for tests | Avoids downloading another browser |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| A pre-commit check stopped the Milestone 4 commit | A new pattern, `secret_`, matched a made-up test constant called `SECRET_TEXT` | Narrowed the pattern, confirmed it still caught real secrets, and reran every check |
| **Text was cut off on phones, though all tests passed** | Source details and captions were inside tables, and the tests only checked that the page didn't scroll sideways. I only noticed by looking at screenshots. | Moved source details to a wrapping list and captions outside tables, added a scroll hint, and added a browser test that checks text fits |
| 55 unit tests failed at first | Testing Library's automatic cleanup didn't run, so pages carried over between tests | Added explicit cleanup |
| The no-fabrication scan failed on my own code | `0.473` was in a comment, as a formatting example | Reworded the comment |
| Browser tests couldn't start the backend | Windows' command shell can't run a forward-slash path | Resolved and quoted the path |
| A backend test failed after I split it | I'd dropped the exception for words a committed report publishes on purpose | The test now reads those words from that report |
| A website process kept running after a check | My cleanup didn't reach a process started through `cmd` | Stopped it, after confirming it was this project's server |
| Type error with the accessibility tool | It has its own copy of Playwright's types | Added a cast, with a comment |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 290 passed |
| `npm test` | 90 passed |
| `npm run test:e2e`, real backend and model | 50 passed |
| `npm run test:e2e:api-down`, backend really stopped | 4 passed |
| Layouts at 360, 768 and 1280 pixels | No sideways page scrolling, text fits, and every overflowing table says so. Also inspected by eye |
| Automated accessibility checks (axe, WCAG A and AA), light and dark | No violations found |
| Clean `npm ci` in a temporary copy | Installed, built and passed the 90 unit tests |
| `npm audit` at install | 0 vulnerabilities |
| Every validation message through the API (19,082) | 0 label, score or explanation mismatches, and 0 unexpected failures |
| The exact start commands | Both applications started, and all pages and endpoints responded |
| Production bundle | Contains no test data |
| Frozen model | Same file hash and fingerprint, with no changes under `backend/training` or `backend/models` |

These were run on an i7-12650H with 15.7 GB RAM, with other applications open, using Edge.

**Not tested:** a screen reader, a real phone, browsers other than Edge, or email from outside this dataset.

### Remaining work

None. The visual redesign below continued this work.

## 2026-11-05: Visual redesign of the website

**Status:** Implemented and awaiting review. Requested by the project owner after reviewing Milestone 5.

**Commit:** Not committed yet.

### Work completed

- Replaced the visual style with a gradient navigation bar, shield logo, colourful cards and page banners.
- Added a landing page with a hero, headline results, a "how it works" strip and charts.
- Added charts to the Models and Dataset pages, and a decision gauge to the result.
- Wrote 29 unit tests and 11 browser tests. The backend, frozen model and API weren't changed.

### Important decisions

| Decision | Reason |
|---|---|
| Commit the reviewed Milestone 5 first | Keeps the reviewed version in history, separate from an unreviewed redesign |
| Show the weaker results beside the strongest in the hero | A vibrant page shouldn't overstate performance |
| Chart error counts, not F1, where values are close | F1 values from 0.97 to 0.99 look the same from zero, and a cut-off axis would exaggerate differences |
| Make the gauge a position on the model's scale | A speedometer style could read as a percentage |
| Validate colours before using them | Vibrant palettes often fail contrast. Two low-contrast split colours rely on their text labels, as the validator requires |

### Problems encountered

| Problem | Cause | Resolution |
|---|---|---|
| A chart said errors were in "messages unlike anything in training" | My wording overstated the data, which only measures having no close match. I noticed it when reviewing the screenshots. | Corrected the wording |
| The sticky navigation bar could cover focused items | It stays on screen while the page scrolls | Added scroll padding |
| Browser tests wouldn't start | The project owner's own servers were using the ports, and the tests refuse to reuse a server | Ran them against those servers, using a temporary config, and ran the API-stopped suite on a separate port. Those servers weren't stopped. |

### Tests and actual results

| Check | Result |
|---|---|
| `python -m pytest backend` | 290 passed |
| Frontend type check and production build | Passed |
| `npm test` | 119 passed |
| Browser tests, real API and frozen model | 61 passed, including layouts at 360, 768 and 1280 pixels, and accessibility checks in both colour modes |
| Browser tests, no API listening | 4 passed, on a separate port pointed at an API port with nothing listening |
| Frozen model | Same file hash and fingerprint |

**Not tested:** a screen reader, a real phone, or browsers other than Edge.

### Remaining work

- Project owner to review and decide whether to commit.
- Milestone 6: full verification, final documentation, and portfolio readiness.
