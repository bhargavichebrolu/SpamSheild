# `backend/training/feature_experiments.py`

Source: [`feature_experiments.py`](../../backend/training/feature_experiments.py).

## 1. Why the file exists

Preprocessing and feature choices need evidence, along with a measure of what they cost in time and memory. Available memory was also limited, so larger runs had to be justified by smaller ones first.

## 2. Responsibility and design intention

It compares options under controlled conditions: each experiment fits on training rows and scores on validation rows, with one fixed classifier so only the representation changes. **It doesn't select a model**, which is Milestone 3's job.

## 3. Inputs and outputs

| | Details |
|---|---|
| **Input** | Training and validation splits, through `load_split`. The test split is never requested. |
| **Output** | `backend/reports/feature_experiments.json`: settings, rows used, metrics and cost for each experiment |
| **Output** | `backend/reports/near_duplicate_check.json`: template similarity, and scores for each similarity band |

Run from `backend/`:

```powershell
python -m training.feature_experiments --list
python -m training.feature_experiments --stage sample
python -m training.feature_experiments --stage scale
python -m training.feature_experiments --stage all_train
python -m training.feature_experiments --near-duplicates
```

## 4. Important functions and variables

| Name | Purpose |
|---|---|
| `PREPROCESSORS` | The preprocessing variants compared |
| `Experiment`, `EXPERIMENTS` | Each experiment's settings, grouped into `sample`, `scale` and `all_train` stages |
| `peak_memory_gb` | Reads the process's peak memory from the operating system |
| `stratified_sample` | Takes a seeded sample with the same label balance |
| `score` | Calculates metrics with Spam as the positive class, plus both error types |
| `run_experiment` | Fits a `Pipeline`, scores it, and records costs |
| `closest_training_similarity` | Finds each row's most similar training row |
| `score_by_similarity_band` | Scores rows separately by that similarity |
| `run_stage` | Runs each experiment in its own process |

## 5. Key implementation decisions

- **One process per experiment:** a process's peak memory only ever rises, so sharing one would blur the measurements.
- **Stages:** sample first, then 40,000 rows, then all training data, so each step's cost is known before the next. Character n-grams stopped at 40,000 rows.
- **A fixed classifier:** Logistic Regression with the `liblinear` solver is fast on sparse data. Using one classifier keeps this a comparison of features.
- **Similarity is calculated in batches:** multiplying sparse matrices can use a lot of memory, so it's done 100 rows at a time.
- **Results can't be directly compared across different validation rows:** this caught one of my own mistakes. Character n-grams were first scored on 5,000 rows and bigrams on 19,082, so I rescored them on the same rows.

## 6. Dependencies

- **Packages:** `numpy`, `pandas`, `scipy`, `scikit-learn`, plus `ctypes` and `subprocess` from the standard library.
- **Project files:** `preprocess.py`, `features.py`, `config.py`, `prepare_data.py`, and `write_report` from `inspect_dataset.py`.

## 7. How its output is used next

Its results set Milestone 3's starting features, and Milestone 3 will report results by similarity band too. Decisions and results are explained in the [project explanation](../PROJECT_EXPLANATION.md#feature-extraction).

## 8. Tests

Tests are in [`test_features.py`](../../backend/tests/test_features.py). One replaces `load_split` with a stand-in that records what's requested, and confirms experiments only ask for train and validation. Run from the repository root:

```powershell
python -m pytest backend
```

## 9. Alternatives considered

| Alternative | Why it wasn't used |
|---|---|
| Grid search over many settings | Costly, and Milestone 3 handles model tuning |
| Using scikit-learn's cross-validation here | Takes several times as long, and a fixed validation split is enough to compare these options |
| Running character n-grams on all training data immediately | Would risk memory problems before knowing whether they help |
| A sampled similarity check | Its first version used 2,000 rows, but the result mattered too much to rely on a sample |
