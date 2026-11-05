# Model card: SpamShield AI 1.0.0

**This is a learning and research prototype, not an email security product.** Its scores come from one dataset whose sources and licence are not verified. They don't show how it would perform on someone's real inbox.

## Model

| Item | Details |
|---|---|
| Type | Linear Support Vector Machine (`LinearSVC`, `C=10.0`, `random_state=42`) |
| Features | Word TF-IDF: single words, `min_df=2`, `max_df=0.95`, `sublinear_tf=True`, `float32` |
| Vocabulary | 242,607 words |
| Words excluded | 575 likely source markers, chosen from training data (see [source leakage](#source-leakage)) |
| Preprocessing | Keep the first 20,000 characters, lowercase, digits to `escapenumber`, remove `escapelong`, `https` to `http`, collapse whitespace |
| Saved file | `backend/models/spamshield_pipeline.joblib` (3.5 MB, not in Git) |
| Details | [`pipeline_metadata.json`](../backend/models/pipeline_metadata.json) |

## Training data and split

The [dataset card](dataset-card.md) has the full details. After cleaning, 190,817 of 193,852 rows remain, split with stratification and seed 42:

| Split | Rows | Spam share | Used for |
|---|---:|---:|---|
| Train | 152,653 | 47.3% | Fitting the saved model |
| Validation | 19,082 | 47.3% | All selection decisions |
| Test | 19,082 | 47.3% | One final evaluation of the frozen model |

The saved model was fitted on the training split only, so the test result describes that exact file.

## Evaluation

### Final test results

The frozen pipeline was evaluated once on the test split, with file hash `ed9f16df…212e862` recorded in the [test report](../backend/reports/final_test_evaluation.json).

| Metric | Result |
|---|---:|
| Accuracy | 0.9900 |
| Precision (Spam) | 0.9899 |
| Recall (Spam) | 0.9889 |
| F1 (Spam) | 0.9894 |
| ROC-AUC | 0.9987 |

| | Predicted Ham | Predicted Spam | Error rate |
|---|---:|---:|---:|
| **Actually Ham** (10,057) | 9,966 | 91 | 0.9% wrongly flagged |
| **Actually Spam** (9,025) | 100 | 8,925 | 1.1% missed |

Ham precision is 0.9901 and Ham recall is 0.9910.

### Results by similarity to training data

Each test message is grouped by its closest training message, using cosine similarity of word TF-IDF fitted on training rows.

| Closest training message | Rows | Share of rows | F1 (Spam) | Ham wrongly flagged | Spam missed |
|---|---:|---:|---:|---:|---:|
| Under 0.80 | 6,684 | 35.0% | **0.9727** | 85 (2.5%) | 96 (2.9%) |
| 0.80 to 0.90 | 2,450 | 12.8% | 0.9982 | 2 (0.1%) | 2 (0.2%) |
| 0.90 to 0.95 | 3,719 | 19.5% | 0.9996 | 1 (0.0%) | 0 (0.0%) |
| 0.95 and above | 6,229 | 32.6% | 0.9992 | 3 (0.1%) | 2 (0.1%) |

**Nearly all errors (181 of 191) are in the lowest band.** Messages with close training matches are almost always right, so overall scores partly reflect recognising near-copies. The first row is a fairer guide to messages without a close match, but those messages still come from this dataset's sources.

### Speed

One-message-at-a-time prediction, including preprocessing and TF-IDF, took a median of 0.56 ms and a 95th percentile of 1.15 ms on the test run. On the validation rehearsal, it took 1.49 ms and 3.07 ms. Timings vary between runs. These were measured on an i7-12650H with other applications open, and exclude any API overhead.

## Why this model was selected

The selection rule was fixed before any comparison was run, and it only used validation results:

1. Find the highest F1 for Spam among runs that converged.
2. Treat anything within 0.002 of it as tied, since that's about the size of random variation.
3. Among ties, choose the fewest legitimate messages flagged as spam, because that's the costlier mistake.
4. If still tied, prefer the simpler model, then the smaller feature set.

All models shared one split, and within each feature set every classifier used an identical TF-IDF matrix. Best validation result for each combination:

| Model | Features | Best setting | F1 (Spam) | Ham flagged | Spam missed | ROC-AUC |
|---|---|---|---:|---:|---:|---:|
| Multinomial Naive Bayes | Words | `alpha=0.01` | 0.9713 | 121 | 390 | 0.9971 |
| Multinomial Naive Bayes | Words and bigrams | `alpha=0.01` | 0.9701 | 101 | 429 | 0.9976 |
| Logistic Regression | Words | `C=10` | 0.9883 | 124 | 87 | 0.9987 |
| Logistic Regression | Words and bigrams | `C=10` | 0.9898 | 125 | 60 | 0.9990 |
| Linear SVM | Words | `C=1` | 0.9900 | 99 | 82 | 0.9988 |
| **Linear SVM (selected)** | **Words** | **`C=10`** | **0.9900** | **93** | **88** | **0.9987** |
| Linear SVM | Words and bigrams | `C=10` | 0.9915 | 103 | 50 | 0.9990 |

The [full comparison](../backend/reports/model_comparison.json) has all 18 runs, with the exact settings.

**What this choice gives up:** Linear SVM with bigrams has the highest F1 and misses fewer spam (50 vs 88). Its F1 lead is inside the tie margin, and it flags 10 more legitimate messages, so the rule picks the single-word model. It also needs less memory to train (peak 1.47 GB vs 2.77 GB).

Tuning was deliberately small, with three values per model. The best Logistic Regression and SVM values were at the top of that range, so higher values weren't explored. The test split played no part in any of this.

## Source leakage

The dataset appears to combine separately processed sources, so a model could learn where a message came from rather than whether it's spam. **These experiments show dependence on signals in this dataset. They are not proof of how the model generalises to unseen sources:** the sources are unverified, the word lists are estimates, and all rows come from this one dataset.

### How the word lists were created

[`source_markers.py`](../backend/training/source_markers.py) builds the lists from **training rows only**, using words found in at least 50 training rows:

- **Style-leaning:** words differing most between the digit style and placeholder style, measured within each label. The styles are evidence of different processing, so these words may mark a source.
- **Ham-leaning and Spam-leaning:** words differing most between the labels.

The lists are estimates, and they mix different things. Style-leaning words include list and organisation terms such as `enron`, `listinfo` and `linguist`, but also disguised spellings such as `technoiogy`, which may be real spam signals. Removing a word therefore doesn't only remove source information. The saved lists can include people's surnames, so they aren't in Git, and the reports only record hashes.

### Removing marker words

Words were removed before forming features, then the model was retrained and scored on validation rows:

| Words removed | Count | F1 (Spam) | Ham flagged | Spam missed |
|---|---:|---:|---:|---:|
| None (baseline) | 0 | 0.9900 | 93 | 88 |
| Top 300 style-leaning | 300 | 0.9894 | 103 | 89 |
| Top 1,000 style-leaning | 1,000 | 0.9889 | 108 | 93 |
| Top 300 Ham-leaning | 300 | 0.9895 | 98 | 92 |
| **Top 300 style-leaning and top 300 Ham-leaning (used)** | **575** | **0.9886** | **107** | **99** |
| Top 300 Ham-leaning and top 300 Spam-leaning | 600 | 0.9894 | 100 | 92 |

Scores barely change, even without the strongest words. That isn't reassuring by itself: the remaining 242,000 words can carry the same source patterns.

### Training on one number style and scoring on another

This is a harder test, because it uses the number styles as a stand-in for separate sources. These runs use the selected model and are scored on validation rows:

| Trained on | Training rows | Scored on | Rows | F1 (Spam) | Ham wrongly flagged | Spam missed |
|---|---:|---|---:|---:|---:|---:|
| Digit style | 20,196 | Digit style | 2,559 | 0.9911 | 16 of 1,436 (1.1%) | 4 of 1,123 (0.4%) |
| Digit style | 20,196 | **Placeholder style** | 12,525 | **0.8400** | **1,547 of 7,276 (21.3%)** | 328 of 5,249 (6.2%) |
| Placeholder style | 100,496 | Placeholder style | 12,525 | 0.9955 | 21 of 7,276 (0.3%) | 26 of 5,249 (0.5%) |
| Placeholder style | 100,496 | **Digit style** | 2,559 | **0.9589** | **55 of 1,436 (3.8%)** | 38 of 1,123 (3.4%) |
| Placeholder style, matched size | 20,196 | Placeholder style | 12,525 | 0.9831 | 99 of 7,276 (1.4%) | 79 of 5,249 (1.5%) |
| Placeholder style, matched size | 20,196 | Digit style | 2,559 | 0.9559 | 62 of 1,436 (4.3%) | 38 of 1,123 (3.4%) |

**This is the most important limitation here.** When training and scoring styles differ, F1 falls and false alarms rise sharply, even with no sign of trouble on a random split. The matched-size rows show training size explains only part of the drop. Rows with neither style, which can't be assigned to either group, are in the [full report](../backend/reports/source_leakage.json) and also score lower.

### Why the final model excludes 575 words

This rule was also fixed before any leakage result was seen: use the removal only if validation F1 stays within 0.002 of the baseline, and cross-style F1 improves in both directions.

| Check | Result |
|---|---:|
| Validation F1 drop | 0.0014, within the margin |
| Cross-style F1, digit to placeholder | +0.0170 (0.8400 to 0.8570) |
| Cross-style F1, placeholder to digit | +0.0005 (0.9589 to 0.9594) |

**The rule was met, but narrowly, and these points limit what it shows:**
- The second improvement is within noise.
- The removal cost a little on validation: 14 more legitimate messages flagged, and 11 more spam missed.
- Scores on rows with neither style were mixed.
- The word list was built from all training rows, so it already reflects both styles. That flatters the cross-style improvement, as real unseen sources wouldn't have that advantage.

## Intended use

- Demonstrating and learning about an explainable text classification pipeline
- Trying out individual messages in the local website, with the understanding that results are indicative only

## Out-of-scope uses

- Automatically blocking, deleting or moving email
- Relying on it to detect phishing, fraud or malware
- Use as a production email filter, or any high-stakes decision

## Limitations

- **Unknown real-world performance:** no email from outside this dataset has been tested. The cross-style results suggest performance could fall sharply on unfamiliar sources.
- **Overall scores are lifted by near-copies:** about two-thirds of test rows have a training match at similarity 0.80 or above.
- **Text mismatch:** the training text was already processed, and preprocessing only narrows the gap with real email.
- **Topic bias:** Ham appears dominated by a few organisations and mailing lists. Ordinary personal email may look less familiar, and could be flagged more often.
- **Unverified data:** the dataset's licence, label accuracy and original sources have not been verified.
- **Fixed balance:** the spam share is 47.3%, and real inboxes differ. Precision would change with a different share.
- **Ageing:** spam changes over time, and the model will not adapt by itself.

## Known failure modes

These are expected from the results above. Specific real-world rates haven't been measured.

- Legitimate email from an unfamiliar source or topic being flagged as spam
- Spam with no close match in training being missed
- Short messages, which give the model few words to use. The model's intercept is positive (+0.71), so its starting score leans towards spam, and a message needs enough Ham-leaning terms to overcome that. For example, the harmless text `Example message text` is classified as Spam, which is a single example and not a measured rate
- Odd word associations learned from this dataset. In one test message, `congratulations` pushed the score towards Ham, and explanations will show patterns like this

The website adds a caution when fewer than 5 words are recognised. That threshold is a display warning, not a measured reliability boundary, and it doesn't change the prediction.
- Messages with few or no known words, such as other languages, where the result says little
- Text after the first 20,000 characters, which the model doesn't read

## Confidence and calibration

**This model doesn't provide a probability.** A Linear SVM produces a score, where the sign gives the label and a larger size means further from the decision boundary. That score isn't a percentage or a chance of being correct, and it must not be displayed as one. The API's `confidence` field is therefore always `null`, and the website labels the value a decision score and shows no percentage with a prediction.

Calibrating it into a probability would change the frozen pipeline after its one test evaluation, so that's future work needing its own held-out data.

## Explanations

The API explains each score using the model's own numbers. A Linear SVM's score is a sum:

`score = intercept + sum(TF-IDF value × learned weight)`, for each term in the message

So each term's contribution is calculated exactly, with no approximation, and the parts add up to the score. Across 18,929 validation messages sent through the API, they did.

**This shows which terms moved this score, and nothing more.** It doesn't show why a message is spam, it doesn't show what would happen if the wording changed, and it can reveal patterns from the training data rather than anything meaningful about the message. TF-IDF values also depend on the whole message's length, so a word's contribution differs between messages.

## Reproducibility

Run these from the `backend` folder, with the virtual environment active and the dataset in place:

```powershell
python -m training.prepare_data
python -m training.compare_models
python -m training.source_markers
python -m training.source_leakage
python -m training.train_final
python -m training.train_final --verify-reproducible
python -m training.final_evaluation --split validation
```

The expected versions are in [`requirements.txt`](../backend/requirements.txt), and the seed is 42.

**To load the saved pipeline:**

```powershell
python -c "from app.ml.predict import load_pipeline; print(load_pipeline().predict(['Example message text']))"
```

Only load a model file this project created, because the file format can run code when loaded.

### Two hashes identify the model

[`pipeline_metadata.json`](../backend/models/pipeline_metadata.json) records two different hashes, because they answer different questions:

| | File hash (`pipeline_sha256`) | Content fingerprint (`model_content_sha256`) |
|---|---|---|
| **Question it answers** | Is this exactly the same file? | Is this the same model? |
| **What it covers** | The saved file's bytes | Learned vocabulary, IDF values, weights and intercept, classes, settings, removed words, and preprocessing results on fixed sample text |
| **Value** | `ed9f16df062afe7bb4ba3dd1acb6473d5119aa643ae1bcdf9d042279de788b2c` | `6f5135d9e9e3832ef8513607fe645661abfc84096c983ba7430378652a10c2e2` |
| **After loading and resaving** | Can change | Stays the same |
| **After an identical retrain** | Changes | Stays the same |
| **If any covered value changes** | Changes | Changes |

**The file hash** proves the evaluated file wasn't altered, which is why the test report records it. **The fingerprint** proves two files hold the same model, even when their bytes differ.

Together they connect the test result to a model: the [test report](../backend/reports/final_test_evaluation.json) names the file hash, and the metadata pairs that file hash with the fingerprint. So any file with this fingerprint holds the model that was tested.

**What was verified on the frozen file, which was not retrained or changed:**
- The fingerprint matched in two separate processes with different hash seeds, and their predictions on 19,082 validation rows were identical.
- A fresh retrain, held in memory and not saved, gave the same fingerprint.
- The frozen file's hash was the same before and after.

**Limits of the fingerprint:**
- **Matching fingerprints don't prove matching real-world performance.** They show matching stored values and configuration, under this method. How well a model works still depends on the email it sees and the environment it runs in.
- It's an exact match on stored numbers, so it was only verified on this computer and these package versions. A different processor or library could change the last digits of a weight, and so change the fingerprint, even with a nearly identical model.
- It includes preprocessing results on six sample strings, so it catches behaviour changes that affect those strings, but not every possible change.

### What retraining does

The saved file's bytes differ between training runs, although the learned values don't. The likely cause, not yet proved, is that scikit-learn stores a memory address on the vectoriser.

`python -m training.train_final` replaces both the saved file and the metadata's file hash, so **the test report's file hash would no longer match**. To confirm a retrained model is the tested one, compare its fingerprint with the value above. To check without replacing anything:

```powershell
python -m training.train_final --verify-fingerprint
python -m training.train_final --verify-reproducible
```

**The test evaluation is deliberately not in the first list above.** It can run only once, and refuses if its report exists. That's why `python -m training.final_evaluation --split test` now stops with an error.
