# SpamShield AI

An explainable email spam classifier, planned as an end-to-end machine learning application with a FastAPI backend and a React frontend. This is a learning and research prototype, not an email security product.

## Project status

**Milestones 1 and 2 of 6 are complete.** There is no final model, API or web interface yet. The only scores so far are validation results from feature experiments, so they aren't final model performance.

| Status | Work |
|---|---|
| Done | Python environment, dataset inspection, preprocessing, leakage-safe splits, TF-IDF feature experiments, tests |
| Planned | Model comparison and final evaluation, API, web application, final verification |

The dataset's licence is not verified, so the raw data is not included or redistributed here. See the [dataset card](docs/dataset-card.md).

## Documentation

- [Product requirements](docs/PRD.md)
- [Project explanation](docs/PROJECT_EXPLANATION.md)
- [Dataset card](docs/dataset-card.md)
- [Development log](docs/DEVELOPMENT_LOG.md)
- [Source-file explanations](docs/file-explanations/)

## Setup

These commands are for Windows PowerShell, run from the repository root, and use Python 3.14.

1. Create and activate the virtual environment, then install the dependencies:

   ```powershell
   py -V:3.14 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r backend\requirements.txt
   ```

   If PowerShell says running scripts is disabled, you can run this once and then activate again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

   This setting lets local scripts run for your Windows account, and requires downloaded scripts to be signed.

2. Get the dataset by following the [dataset instructions](backend/data/README.md). It is not included in this repository.

## Run

Run the tests. They use made-up data, so they don't need the dataset:

```powershell
python -m pytest backend
```

Inspect the dataset. This checks the file's hash and writes [`backend/reports/dataset_inspection.json`](backend/reports/dataset_inspection.json):

```powershell
python backend\training\inspect_dataset.py
```

Add `--show-examples` to print short text previews to the terminal. Previews are never saved to the report.

Run the data pipeline from the `backend` folder, in this order. The feature experiments take several minutes, and the largest needs about 3 GB of free memory:

```powershell
cd backend
python -m training.analyse_format
python -m training.prepare_data
python -m training.analyse_vocabulary
python -m training.feature_experiments --stage sample
python -m training.feature_experiments --stage scale
python -m training.feature_experiments --stage all_train
python -m training.feature_experiments --near-duplicates
```

## Repository layout

```text
spamshield-ai/
├── backend/
│   ├── app/ml/                    Preprocessing shared by training and the future API
│   ├── data/
│   │   ├── README.md              How to get the dataset
│   │   ├── processed/             Generated split file (not committed)
│   │   └── raw/                   Local dataset file (not committed)
│   ├── reports/                   Generated results
│   ├── tests/                     Automated tests
│   ├── training/                  Inspection, data preparation and experiments
│   ├── pytest.ini
│   └── requirements.txt
├── docs/                          Requirements, explanations and logs
├── .gitignore
└── README.md
```

Other folders will be added when a milestone needs them.
