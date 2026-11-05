# Project explanation

This document explains SpamShield AI as one connected system. It grows with each milestone and describes only what exists now. Anything not built yet is listed under [Not built yet](#not-built-yet).

**Current state:** Milestone 3. The project can verify its dataset, prepare it, compare models, and train, save and load a final pipeline. It has no API or frontend yet. The [model card](model-card.md) has the full results and limitations.

## Problem and objective

The project investigates whether machine learning and natural language processing can distinguish spam from legitimate email using labelled examples, and how to present those predictions honestly in a web application. It is a learning and research prototype, and it does not provide guaranteed email security.

## Dataset and labels

The project uses a Kaggle CSV of 193,852 messages with two columns, `label` (`Ham` or `Spam`) and `text`. Its reported source is Kaggle and its licence is not verified, so the raw data is not committed or redistributed. After cleaning, 190,817 rows remain. The [dataset card](dataset-card.md) has the verified details and known limitations.

## End-to-end data flow

```text
spam_Emails_data.csv (raw, not in Git, never changed)
        │
        ├──► inspect_dataset.py ──► dataset_inspection.json
        │
        ├──► analyse_format.py ───► format_analysis.json
        │         │
        │         └─ informs preprocess.py
        │
        ├──► prepare_data.py ─────► split_assignments.csv (row number → split)
        │     uses preprocess.py    data_preparation.json
        │         │
        │         ▼
        │     load_split()  ── refuses "test" unless explicitly allowed
        │         │
        │         ├──► analyse_vocabulary.py (train only)
        │         │         └─► vocabulary_analysis.json (not in Git)
        │         │
        │         └──► feature_experiments.py (train and validation only)
        │               uses features.py and preprocess.py
        │                   ├─► feature_experiments.json
        │                   └─► near_duplicate_check.json
        │
        ├──► compare_models.py (train and validation) ──► model_comparison.json
        ├──► source_markers.py (train) ──► source_markers.json (not in Git)
        ├──► source_leakage.py (train and validation) ──► source_leakage.json
        │
        ▼
     FINAL_MODEL in config.py (set from validation results only)
        │
        ▼
     train_final.py (train) ──► spamshield_pipeline.joblib (not in Git)
        │                       pipeline_metadata.json
        ▼
     final_evaluation.py ──► validation rehearsal, then one test evaluation
```

Each script's output is the next one's input, so the [architecture document](architecture.md) shows the same flow by component.

## Why the inspection works this way

- **Hash check first:** results only mean something for a known file. If the file changes, the script stops instead of quietly reporting on different data.
- **Literal text:** by default Pandas turns text such as `null` or `NA` into missing values, which would be wrong for email. On this dataset the setting only affects the 2 empty rows, but it makes the behaviour explicit.
- **Strict decoding:** invalid UTF-8 causes an error instead of being silently altered.
- **Fingerprints for duplicates:** comparing short hashes finds duplicates without keeping a second copy of the text in memory.
- **No email text in reports:** committed reports hold only aggregates, because the dataset's licence is not verified.

## Text preprocessing

The dataset's text was already processed before this project received it: no uppercase, no `http://`, and placeholders such as `escapenumber`. A real pasted email looks very different. [`preprocess.py`](../backend/app/ml/preprocess.py) makes both look alike, using one function for training and inference.

| Step | Example | Why |
|---|---|---|
| Keep the first 20,000 characters | | Bounds the cost of extreme messages |
| Lowercase | `WIN` → `win` | The dataset has no uppercase, so real capitals would never match its vocabulary |
| Digits to `escapenumber` | `sha1` → `shaescapenumber` | Matches the dataset's placeholder and removes the digits-or-placeholder source signal |
| Remove `escapelong` | | Real email can't produce it, because its rule can't be reproduced |
| `https` to `http` | | `https` appears in 6.56% of Ham but 0.30% of Spam, which would teach a model that the secure form means legitimate |
| Collapse whitespace | | Spacing differences carry no meaning for these features |

### Why validation scores alone can't choose these steps

Removing a source signal could lower a validation score even when it's the right thing to do, because the validation data has the same sources and the same leak. So these steps are chosen because they make training text match real text. The experiments measure what they cost:

| Preprocessing (word features, 10,000 training and 5,000 validation rows) | F1 (Spam) |
|---|---:|
| Full preprocessing | 0.9612 |
| Length cap and lowercase only | 0.9604 |
| Digits to placeholder only | 0.9606 |
| Full, with no length cap | 0.9617 |

These differences are within noise, which is roughly ±0.3 points on 5,000 rows. **So the realistic preprocessing costs nothing measurable.** This doesn't show it improves real-world results, because no real-world data has been tested.

### The length cap

The value of 20,000 characters was chosen because it sits just above the 99th percentile of Ham message length (19,719). Removing the cap made no meaningful difference in the experiment above.

### What isn't used, and why

- **Removing stop words:** the sample scores were F1 0.9608 with removal and 0.9609 without, so removal adds no value. Words like "your" can also carry style signals.
- **Stemming and lemmatisation:** not tested. The text contains placeholders and broken word fragments, and these steps would add a dependency without evidence of need.
- **Removing punctuation:** the word tokeniser already ignores it.

## Feature extraction

TF-IDF turns each message into a list of numbers, one per term in a vocabulary learned from training data:

- **TF (term frequency)** counts how often a term appears in a message. `sublinear_tf` dampens this, so 100 repeats don't count 100 times as much.
- **IDF (inverse document frequency)** gives more weight to rarer terms, because a term in nearly every message says little.
- Each message's values are scaled to length 1, so long messages don't dominate.
- The result is a **sparse matrix**. Most values are zero, because a message uses few of the 300,000 terms, so only the non-zero values are stored.

**Unigrams** are single words, and **bigrams** add pairs such as `free prize`. **Character n-grams** are short letter sequences, which could help with broken-up words like `ogy`.

### Results

All runs used the same fixed Logistic Regression, so only the features differ. This compares features and isn't model selection, which belongs to Milestone 3. All rows below were scored on the full validation split of 19,082 rows.

| Features | Training rows | F1 (Spam) | Ham wrongly flagged | Spam missed | Terms per message | Fit time | Peak memory |
|---|---:|---:|---:|---:|---:|---:|---:|
| Characters (3–5) | 40,000 | 0.9711 | 344 | 183 | 1,244 | 120 s | 2.01 GB |
| Words (1–2) | 40,000 | 0.9733 | 315 | 170 | 224 | 46 s | 1.49 GB |
| Words (1) | 152,653 | 0.9799 | 242 | 124 | 120 | about 40 s | 1.26 GB |
| Words (1–2) | 152,653 | 0.9826 | 212 | 104 | 238 | 148 s | 2.88 GB |

Timings vary between runs and are only a rough guide.

### Decisions

- **Character n-grams were not run on all training data.** They started on a controlled sample as planned. At 40,000 rows they scored lower than bigrams and cost more than 2.5 times the fit time, and a full matrix would need about 1.4 GB by itself. Their possible strength is resisting broken-up words, which hasn't been tested, so this may be worth revisiting.
- **Milestone 3 compared both word feature sets.** With Logistic Regression, bigrams had 50 fewer errors across 19,082 rows, for about 3.5 times the fit time and over twice the memory. The final selection, using more models, chose single words, as explained under [candidate models](#candidate-models-and-selection).

## Leakage safeguards

| Risk | Safeguard |
|---|---|
| The same message in two splits | Duplicates are removed on preprocessed text before splitting, and `verify_no_overlap` stops the run if any remain |
| Vocabulary or IDF learning from held-out data | The vectoriser is fitted inside a `Pipeline` on training rows only. Tests confirm that transforming new text doesn't change the vocabulary |
| Accidentally using the test set | `load_split("test")` raises an error unless `allow_test=True` is passed, and a test confirms experiments request only train and validation |
| Word analysis influencing choices through held-out data | Vocabulary analysis uses training rows only. Format analysis and cleaning do read every row before the split, but they score no model and choose no features |
| A different split each run | The split uses a fixed seed, and the file's hash is recorded and was reproduced |

### Templates remain

Removing identical text can't remove templates: messages with the same wording and small changes. The similarity check measures how close each validation row is to its nearest training row, and scores each group separately, using word unigrams and Logistic Regression:

| Closest training message (cosine similarity) | Share of rows | F1 (Spam) | Ham wrongly flagged | Spam missed |
|---|---:|---:|---:|---:|
| Under 0.80 | 34.6% | 0.9714 | 3.4% | 2.2% |
| 0.80 to 0.90 | 13.1% | 0.9829 | 2.5% | 0.4% |
| 0.90 to 0.95 | 19.8% | 0.9758 | 2.0% | 1.5% |
| 0.95 and above | 32.4% | 0.9890 | 1.6% | 0.8% |
| All rows | 100% | 0.9799 | 2.4% | 1.4% |

**How to read this:**
- Overall scores are lifted by close templates. The "under 0.80" row is a fairer guide to messages the model hasn't effectively seen.
- It's still optimistic. Those messages come from the same sources, so this doesn't show how the model would do on someone's real inbox.
- The bands don't improve smoothly, and their spam share varies from 36.8% to 52.6%, which also affects F1. So this isn't an exact measure of inflation.

**Why the split wasn't changed:** keeping similar messages together in one split would need clustering across about 190,000 rows, which is costly. Repeated spam campaigns also really happen, so a model seeing near-copies isn't entirely unrealistic. Instead, the final evaluation reports these bands alongside its overall results. A group-aware split remains an option for future work.

## Candidate models and selection

Three classifiers were compared, each on the same split and the same TF-IDF matrix, with three values of its main setting:

- **Multinomial Naive Bayes** estimates how likely each word is under each label, and assumes words are independent. `alpha` is smoothing, which stops an unseen combination counting as impossible.
- **Logistic Regression** learns a weight per word, and turns the total into a probability. `C` controls how strongly weights are held back: a higher `C` means less restraint.
- **Linear SVM** also learns a weight per word, but aims for the widest gap between the labels. It gives a score, not a probability.

The selection rule was written down before any results existed: take the highest F1 for Spam, treat anything within 0.002 as tied, and among ties choose the fewest legitimate messages flagged. That chose a **Linear SVM with single words and `C=10`**: validation F1 0.9900, 93 flagged and 88 missed.

It isn't the highest F1. Linear SVM with bigrams reached 0.9915 and missed fewer spam, but flagged 10 more legitimate messages, and the gap was inside the tie margin. The point of a rule fixed in advance is to stop results being explained away afterwards, so the rule stands.

The [model card](model-card.md#why-this-model-was-selected) has the full table.

## Source-leakage experiment

The aim is to measure dependence on likely source signals, using training and validation rows only. **It is not proof of generalisation to unseen sources.**

1. [`source_markers.py`](../backend/training/source_markers.py) ranks words from training rows, by how much they differ between number styles and between labels.
2. [`source_leakage.py`](../backend/training/source_leakage.py) retrains without the top words, and scores on validation rows.
3. It also trains on one number style and scores on the other.

| Test | F1 (Spam) | Ham wrongly flagged |
|---|---:|---:|
| Random split, baseline | 0.9900 | 93 of 10,056 (0.9%) |
| Random split, 575 words removed | 0.9886 | 107 of 10,056 (1.1%) |
| Digit style to placeholder style | 0.8400 | 1,547 of 7,276 (21.3%) |
| Placeholder style to digit style | 0.9589 | 55 of 1,436 (3.8%) |

**How to read this:** removing words barely changes random-split scores, but crossing styles hurts a lot. So a random split can look excellent while hiding a real weakness. Part of the gap is training size, which the [model card](model-card.md#source-leakage) separates out.

The final model excludes the 575 words, because a rule fixed in advance was met: validation F1 stayed within 0.002, and cross-style F1 improved both ways. It was met narrowly, since one improvement was only 0.0005, and the list already reflects both styles, which flatters that result.

## Training and evaluation

`FINAL_MODEL` in `config.py` records the choice, and [`train_final.py`](../backend/training/train_final.py) fits it on training rows only. That way, the final test result describes exactly the saved file.

[`final_evaluation.py`](../backend/training/final_evaluation.py) was rehearsed on validation data first, and reproduced the experiment's numbers exactly. Then the frozen pipeline was evaluated once on the test split:

| Metric | Test result |
|---|---:|
| F1 (Spam) | 0.9894 |
| Precision (Spam) | 0.9899 |
| Recall (Spam) | 0.9889 |
| Ham wrongly flagged | 91 of 10,057 (0.9%) |
| Spam missed | 100 of 9,025 (1.1%) |
| F1 with no close training match (6,684 rows) | 0.9727 |

181 of the 191 errors are in that no-close-match group. The evaluation refuses a second test run, and refuses any file that doesn't match the hash recorded at freezing, so its result can't feed back into choices.

**This result only describes this dataset's sources.** It's unknown how the model would do on a real inbox, and the cross-style results suggest it could be much worse.

## Model persistence

The fitted `Pipeline` is saved with `joblib`, and contains the TF-IDF vectoriser, its reference to `preprocess_text`, the 575 removed words and the classifier. So one file does everything inference needs.

[`predict.py`](../backend/app/ml/predict.py) loads it, using only code from `app/`. A test confirms no training code is imported.

Retraining reproduces identical learned values and predictions, but the file's bytes differ. The likely cause, not yet proved, is that scikit-learn stores a memory address on the vectoriser. So the model is identified in two separate ways:

- **File hash (`pipeline_sha256`):** a SHA-256 of the file's bytes. It proves this is exactly the file that was evaluated.
- **Content fingerprint (`model_content_sha256`):** a SHA-256 of what the model learned and how it's configured, in a fixed order and encoding. It proves two files hold the same model, even if their bytes differ.

A fresh retrain changes the first, but gave the same second. The [model card](model-card.md#two-hashes-identify-the-model) has the values, what was verified and the limits.

## Source-file map

| File | Responsibility | Used by |
|---|---|---|
| [`backend/app/ml/preprocess.py`](../backend/app/ml/preprocess.py) | Text preprocessing for training and inference | `prepare_data.py`, `features.py`, and later the API through the saved pipeline |
| [`backend/app/ml/predict.py`](../backend/app/ml/predict.py) | Load the saved pipeline, and calculate its content fingerprint | `final_evaluation.py`, `train_final.py`, and later the API |
| [`backend/training/config.py`](../backend/training/config.py) | Shared paths, seed and split shares | Training scripts |
| [`backend/training/inspect_dataset.py`](../backend/training/inspect_dataset.py) | Verify the dataset; shared loading and hashing helpers | Other training scripts |
| [`backend/training/analyse_format.py`](../backend/training/analyse_format.py) | Describe the text's format | Informs `preprocess.py` |
| [`backend/training/prepare_data.py`](../backend/training/prepare_data.py) | Clean, split, and guard the test set | Analysis and experiment scripts |
| [`backend/training/analyse_vocabulary.py`](../backend/training/analyse_vocabulary.py) | Find the most label-separating words, on training data | Informs Milestone 3's leakage experiment |
| [`backend/training/features.py`](../backend/training/features.py) | Named TF-IDF configurations | Experiments and final training |
| [`backend/training/feature_experiments.py`](../backend/training/feature_experiments.py) | Compare preprocessing and features; measure template similarity | Informed Milestone 3 |
| [`backend/training/evaluate.py`](../backend/training/evaluate.py) | Shared metrics and similarity bands | Experiments and final evaluation |
| [`backend/training/models.py`](../backend/training/models.py) | Candidate models, settings and the selection rule | `compare_models.py`, `source_leakage.py`, `train_final.py` |
| [`backend/training/compare_models.py`](../backend/training/compare_models.py) | Compare candidates on validation data | Informs `FINAL_MODEL` |
| [`backend/training/source_markers.py`](../backend/training/source_markers.py) | Derive word lists from training data | `source_leakage.py`, `train_final.py` |
| [`backend/training/source_leakage.py`](../backend/training/source_leakage.py) | Measure dependence on likely source signals | Informs `FINAL_MODEL` |
| [`backend/training/train_final.py`](../backend/training/train_final.py) | Fit, save and describe the final pipeline | `final_evaluation.py`, and later the API through the saved file |
| [`backend/training/final_evaluation.py`](../backend/training/final_evaluation.py) | Evaluate the frozen pipeline, with one test run | The model card |
| [`backend/tests/`](../backend/tests/) | Automated tests on made-up data | `pytest` |
| [`backend/reports/`](../backend/reports/) | Generated results | The dataset and model cards, this document, and later the web application |
| [`backend/models/`](../backend/models/) | The saved pipeline (not in Git) and its metadata | Later the API |
| [`backend/requirements.txt`](../backend/requirements.txt) | Pinned Python dependencies | `pip` |
| [`backend/pytest.ini`](../backend/pytest.ini) | Lets tests import from `backend/` and tells `pytest` where they are | `pytest` |

Each source file also has a detailed log in [`file-explanations/`](file-explanations/).

## Structure decisions

- **`backend/training/` is separate from API code.** Inspection and training run before the application does, and the API only needs to make predictions.
- **`preprocess.py` is in `app/`, not `training/`.** A saved pipeline refers to `preprocess_text` by its import path, so the API must be able to import it without training code.
- **`features.py` is in `training/`, not `app/ml/`.** It has a distinct job: one definition of each configuration, shared by experiments and final training. The API doesn't need it, because a saved pipeline contains its own fitted vectoriser.
- **`training` imports from `app`, and never the reverse.** So the API can run without any training code.
- **Splits are stored as row numbers, not text.** This avoids copying the dataset, and the file stays small.
- **Scripts run from `backend/`** using `python -m`, so the import paths match those used by the future API and saved pipeline.

## Testing strategy so far

The 162 tests use small made-up data, so they run quickly without the real dataset and contain no private email. They cover:

- Dataset loading, validation, hashing and statistics
- Each preprocessing step, and that repeating preprocessing doesn't change the result for normal-length messages
- Cleaning rules, reproducible splits, overlap detection and the test-set guard
- Fitting on training text only, and vectoriser save and reload
- Experiment metrics, similarity bands, and that experiments never request the test split
- The selection and word-removal rules, including that a run that didn't converge can't win
- Saving and reloading a pipeline, including with no training code imported
- That a changed model or split file is refused, and that the test split can't be evaluated twice
- That the content fingerprint survives reloading and different hash seeds, and detects changed values

Run them from the repository root:

```powershell
python -m pytest backend
```

## Limitations so far

- The dataset's licence, label accuracy and original sources have not been verified.
- Text format differs from real email, and preprocessing only narrows that gap.
- No result has been tested on email from outside this dataset, so real-world performance is unknown.
- The cross-style results suggest performance could fall sharply on unfamiliar sources.
- Overall scores are lifted by near-copies of training messages.
- The model gives a score, not a probability.
- The similarity check uses single words and one similarity measure, so it's an estimate of template overlap.

## Not built yet

| Topic | Planned milestone |
|---|---|
| Backend request flow, prediction and explanations | 4 |
| Frontend request flow and display | 5 |
| Final limitations and alternative approaches | Updated in each milestone, finalised in 6 |
