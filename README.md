# SpamShield AI

An explainable email spam classifier, planned as an end-to-end machine learning application with a FastAPI backend and a React frontend. This is a learning and research prototype, not an email security product.

## Project status

**Milestone 1 of 6 (project foundation and dataset verification) is complete.** There is no trained model, API or web interface yet, and no model performance results exist.

| Status | Work |
|---|---|
| Done | Python environment, dataset inspection script and report, tests, starter documentation |
| Planned | Preprocessing and features, model comparison, API, web application, final verification |

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

## Repository layout

```text
spamshield-ai/
├── backend/
│   ├── data/
│   │   ├── README.md              How to get the dataset
│   │   └── raw/                   Local dataset file (not committed)
│   ├── reports/                   Generated dataset report
│   ├── tests/                     Automated tests
│   ├── training/                  Dataset inspection, and training code later
│   ├── pytest.ini
│   └── requirements.txt
├── docs/                          Requirements, explanations and logs
├── .gitignore
└── README.md
```

Other folders will be added when a milestone needs them.
