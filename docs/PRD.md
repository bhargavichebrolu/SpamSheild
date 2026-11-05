# Product Requirements Document (PRD)
# SpamShield AI — Explainable Email Spam Detection Platform

**Version:** 2.0  
**Status:** Approved on 2026-11-05. Implementation in progress.  
**Project type:** End-to-end machine learning and full-stack application  
**Primary goal:** Build a working, explainable email spam classification application while developing a genuine understanding of its architecture, data flow, machine-learning decisions, and implementation.

> **Approved decisions:** Section 18 records decisions made when this plan was approved. Where they differ from earlier sections, Section 18 takes precedence.

---

## 1. Project Overview

SpamShield AI is an end-to-end machine-learning application that classifies email text into:

- **Spam** — unwanted, deceptive, or unsolicited email
- **Ham** — legitimate email

The application will allow a user to submit email text, receive a prediction, inspect the model’s confidence where supported, and understand which text features influenced the prediction.

This is not intended to be only a machine-learning notebook. It must become a functioning web application with a reproducible training pipeline, backend API, frontend interface, tests, and technical documentation.

The project will also serve as a structured learning project. Every substantial implementation decision must be documented so the developer can explain the project during technical interviews.

---

## 2. Problem Statement

Spam email can contain misleading language, suspicious links, promotional content, and attempts to manipulate recipients.

The project investigates whether machine-learning and natural-language-processing techniques can distinguish spam from legitimate email using labelled email data.

The application must demonstrate:

1. How raw email text becomes machine-readable features.
2. How different classification algorithms learn from labelled examples.
3. How models are evaluated fairly.
4. How a trained model is integrated into a backend API.
5. How predictions and explanations are presented through a web interface.
6. How the implementation can be tested, reproduced, and maintained.

The application is a learning and research prototype. It must **not** claim to provide guaranteed email security or automatically block messages.

---

## 3. Project Objectives

### 3.1 Functional objectives

- Inspect and validate the selected dataset before modelling.
- Build a reproducible data preparation and training pipeline.
- Compare multiple suitable machine-learning models.
- Evaluate models using appropriate classification metrics.
- Save and reload the selected trained pipeline.
- Expose prediction functionality through a FastAPI backend.
- Build a React and TypeScript frontend.
- Display predictions and supported explanations.
- Provide model comparison and evaluation results.
- Add tests for the data pipeline, prediction API, and frontend.
- Document the project architecture, implementation, limitations, and development history.

### 3.2 Learning objectives

By the end of the project, the developer should be able to explain:

- Python modules, functions, classes, imports, and virtual environments used in the project.
- NumPy and Pandas operations used for data analysis.
- Text preprocessing and feature extraction.
- Tokenisation, vocabulary, TF-IDF, n-grams, and sparse feature matrices.
- The selected classification algorithms and their assumptions.
- Train, validation, and test splits.
- Data leakage and how the project avoids it.
- Precision, recall, F1-score, confusion matrix, and ROC-AUC where appropriate.
- Model persistence and inference.
- FastAPI request and response handling.
- React component structure and frontend-to-backend communication.
- Testing, error handling, configuration, and reproducibility.
- The project’s limitations and alternative technical approaches.

---

## 4. Target Users

### Primary user

A person who wants to paste email content and receive a spam-versus-legitimate classification.

### Developer / evaluator

A recruiter, interviewer, tutor, or technical reviewer who wants to inspect:

- The application
- The source code
- The machine-learning methodology
- The evaluation results
- The tests
- The documentation
- The developer’s technical understanding

---

## 5. Dataset Requirements

### 5.1 Candidate dataset

Kaggle 190K+ Spam/Ham Email Classification Dataset:

https://www.kaggle.com/datasets/meruvulikith/190k-spam-ham-email-dataset-for-classification

The dataset has been selected for the project, but its exact contents must be verified locally before implementation relies on them.

### 5.2 Mandatory dataset verification

The first milestone must establish:

- Exact dataset filename and file format
- Exact number of rows and columns
- Column names
- Label values and their meanings
- Missing-value counts
- Duplicate-row counts
- Class distribution
- Example records
- Dataset licence shown on Kaggle
- Whether the downloaded file is from the selected Kaggle source

Do not assume the dataset contains a particular column name, row count, label encoding, or licence.

### 5.3 Data handling requirements

- Preserve the original downloaded dataset unchanged.
- Store raw data locally and exclude it from Git unless redistribution is explicitly permitted and appropriate.
- Document where the dataset came from and how it is obtained.
- Keep data inspection and cleaning reproducible.
- Investigate duplicates and possible leakage before splitting.
- Use a stratified split where appropriate.
- Fit preprocessing and feature extraction only on training data.
- Do not use test data to select or tune the model.
- Record random seeds and relevant configuration.
- Do not fabricate dataset statistics or model results.

---

## 6. Scope

### 6.1 Included in version 1

- Dataset inspection and validation
- Exploratory data analysis
- Text preprocessing
- TF-IDF feature extraction
- Word and character n-gram experiments where appropriate
- Comparison of suitable traditional machine-learning models
- Model evaluation and selection
- Reproducible saved pipeline
- Prediction API
- Web-based email classifier
- Prediction explanation
- Model comparison page
- Dataset exploration page
- Prediction history with privacy-conscious storage
- Model card and technical documentation
- Automated tests
- GitHub-ready project structure

### 6.2 Excluded from version 1

- Connecting to a user’s email inbox
- Automatically deleting, blocking, or moving emails
- Production email gateway integration
- Paid LLM APIs
- Using an LLM as the primary classifier
- Claims of guaranteed spam detection
- Claims of enterprise-grade email security
- Claims of clinical, financial, or other high-stakes validation
- Features that cannot be completed and tested within the approved project scope

Additional features may be considered only after the core application works and is documented.

---

## 7. Technical Stack

The following stack is proposed. Changes must be justified and documented.

### Machine learning and data

- Python
- NumPy
- Pandas
- scikit-learn
- TF-IDF vectorisation
- Candidate models:
  - Multinomial Naive Bayes
  - Logistic Regression
  - Linear Support Vector Machine

These are candidate models, not predetermined winners. The final model must be selected using measured evaluation results.

### Backend

- FastAPI
- Pydantic
- Uvicorn
- Python-based prediction pipeline
- SQLite for prediction history, if implemented

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS, if appropriate

### Testing and development

- pytest
- Vitest
- React Testing Library
- Git and GitHub
- Docker and Docker Compose, if time permits and justified

---

## 8. Application Features

### 8.1 Email Classifier

The user can:

1. Paste email text into a text field.
2. Submit the text for classification.
3. View the predicted label: Spam or Ham.
4. View a confidence or probability value only if the selected model supports a meaningful, properly interpreted value.
5. View an explanation of influential text features.
6. Receive clear validation errors for empty or invalid input.

The application must not present model confidence as a guarantee of correctness.

### 8.2 Model Comparison

Display measured results for the models that were actually trained and evaluated.

Potential metrics:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- ROC-AUC, where appropriate

The page must identify the dataset split and evaluation method used. Results must come from actual experiment outputs, not manually entered or fabricated values.

### 8.3 Dataset Explorer

Display verified dataset information, such as:

- Number of records
- Label distribution
- Missing values
- Duplicate records
- Relevant text statistics

Only show information that has been computed from the actual dataset.

### 8.4 Prediction Explanation

Explain which terms or features influenced a prediction.

The initial approach should use model-supported feature importance or coefficients where appropriate.

SHAP or other explanation methods may be considered only if they are justified, computationally practical, and correctly interpreted.

The explanation must not imply that the model understands the email’s intent in the same way a human does.

### 8.5 Prediction History

If implemented:

- Store prediction metadata and timestamps.
- Avoid storing full email content by default.
- Make data retention and privacy behaviour explicit.
- Handle database errors safely.
- Provide a way to clear stored history.

---

## 9. Proposed Architecture

```text
                 ┌──────────────────────┐
                 │  Raw labelled dataset│
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Dataset inspection   │
                 │ and validation       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Data preparation     │
                 │ and text handling    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ TF-IDF feature       │
                 │ extraction           │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Model training       │
                 │ and comparison       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Evaluation and       │
                 │ model selection      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Saved ML pipeline    │
                 └──────────┬───────────┘
                            │
                            ▼
┌─────────────────┐  ┌──────────────────────┐
│ React frontend  │◄►│ FastAPI backend      │
│                 │  │                      │
│ Email input     │  │ Validation           │
│ Prediction view │  │ Model inference      │
│ Explanation     │  │ Explanation response │
│ Model results   │  │ Optional history     │
└─────────────────┘  └──────────────────────┘
```

The architecture may evolve during implementation. The final architecture documentation must describe the code that actually exists.

---

## 10. Repository Structure

Create the repository progressively. Do not generate every file before its milestone requires it.

```text
spamshield-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── schemas/
│   │   │   └── prediction.py
│   │   ├── ml/
│   │   │   ├── preprocess.py
│   │   │   ├── features.py
│   │   │   ├── train.py
│   │   │   ├── evaluate.py
│   │   │   ├── predict.py
│   │   │   └── explain.py
│   │   ├── database/
│   │   │   └── db.py
│   │   └── config.py
│   ├── data/
│   │   └── README.md
│   ├── models/
│   ├── experiments/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── docs/
│   ├── PRD.md
│   ├── PROJECT_EXPLANATION.md
│   ├── DEVELOPMENT_LOG.md
│   ├── architecture.md
│   ├── model-card.md
│   ├── dataset-card.md
│   └── file-explanations/
├── .gitignore
├── README.md
└── docker-compose.yml
```

This structure is a target, not a requirement to create empty files. Files may be renamed or reorganised if the implementation benefits from it.

---

## 11. Documentation Requirements

Documentation is a required project deliverable, not an optional final task.

### 11.1 Primary project explanation

File:

`docs/PROJECT_EXPLANATION.md`

This must explain the complete project as one connected system:

- Problem and objective
- Dataset and labels
- End-to-end data flow
- Text preprocessing
- Feature extraction
- Candidate models and selection rationale
- Training and evaluation
- Model persistence
- Backend request flow
- Frontend request flow
- Prediction and explanation flow
- Testing strategy
- Limitations
- Alternative approaches and why they were not selected

It must include a source-file map showing how the main files connect.

### 11.2 Individual source-file explanation logs

Location:

`docs/file-explanations/`

Create or update an explanation log for every source file created or substantially modified.

Example filenames:

- `backend-app-main-py.md`
- `backend-api-routes-py.md`
- `backend-ml-preprocess-py.md`
- `backend-ml-features-py.md`
- `backend-ml-train-py.md`
- `backend-ml-evaluate-py.md`
- `backend-ml-predict-py.md`
- `backend-ml-explain-py.md`
- `frontend-app-tsx.md`

Each log must explain:

1. Why the file exists.
2. Its responsibility and design intention.
3. Inputs and outputs.
4. Important functions, classes, and variables.
5. Key implementation decisions.
6. Dependencies and files it calls or imports.
7. How its output is used by the next part of the system.
8. Relevant tests and how to run them.
9. Important alternatives and why the selected approach was used.

Logs must describe actual implementation, not planned code.

### 11.3 Development log

File:

`docs/DEVELOPMENT_LOG.md`

Maintain a chronological record containing:

- Date or development session
- Milestone
- Work completed
- Important decisions
- Problems encountered
- How problems were resolved
- Tests and their actual results
- Remaining work
- Commit reference, when applicable

### 11.4 Architecture documentation

File:

`docs/architecture.md`

Keep this synchronised with the implemented system. Include component responsibilities, dependencies, and request/data flow.

### 11.5 Dataset card

File:

`docs/dataset-card.md`

Document the verified source, licence, structure, label meaning, class balance, known limitations, and data handling.

### 11.6 Model card

File:

`docs/model-card.md`

Document:

- Model type and configuration
- Training data and split method
- Evaluation metrics
- Intended use
- Limitations
- Known failure modes
- Reproducibility instructions
- Any confidence-calibration caveats

Do not write final model results until they have been measured.

---

## 12. Development Workflow

### Required process

1. Claude reviews this PRD and the existing repository.
2. Claude presents a milestone plan only.
3. Claude waits for approval.
4. Claude implements one approved milestone.
5. Claude runs relevant checks and reports actual results.
6. Claude updates the required documentation in the same milestone.
7. Claude shows the user the visible result and changed files.
8. The user reviews and commits the milestone.
9. The next milestone begins only after approval.

### Learning and explanation approach

Do not stop after every function or file to ask whether the user understands.

Instead:

- Provide concise inline explanations during implementation.
- Explain important decisions at the point they are made.
- Write detailed, connected explanations in the documentation.
- Keep the user’s review time focused on the implementation and logs.
- Do not silently change code to fix errors; explain the cause and the fix.
- Do not generate large amounts of code without explaining the data flow and design.

### Environment requirements

- Use VS Code.
- Use the local Python virtual environment.
- Use Python scripts and modules for the core pipeline.
- Do not use Google Colab as the primary development environment.
- Notebooks may be used only if they provide a specific benefit; they must not become the core application.
- Keep raw datasets, virtual environments, secrets, generated databases, and unnecessary model artefacts out of Git.

---

## 13. Major Milestones

The project must contain no more than **six major milestones**. Do not create a long list of minor milestones or stop for approval after every small task.

### Milestone 1 — Project Foundation and Dataset Verification

**Objective:** Establish a reproducible local project and verify the actual dataset.

**Deliverables:**

- Repository and environment structure
- `.gitignore`
- Verified dataset source, licence, filename, columns, labels, row count, missing values, duplicates, and class distribution
- Dataset handling instructions
- Initial dataset card
- Initial development log
- Initial project explanation and source-file map

**Acceptance criteria:**

- The environment runs locally.
- Dataset inspection can be reproduced.
- Dataset facts are verified rather than assumed.
- Raw data is not accidentally committed.
- Documentation matches the actual repository.

### Milestone 2 — Data Analysis, NLP Preprocessing, and Feature Engineering

**Objective:** Understand and implement the data preparation and text representation pipeline.

**Deliverables:**

- Data analysis scripts
- Cleaning and preprocessing implementation
- TF-IDF feature extraction
- Word and character n-gram experiments where justified
- Data leakage safeguards
- Tests for preprocessing and feature extraction
- Updated project explanation, file logs, dataset card, and development log

**Acceptance criteria:**

- Data preparation is reproducible.
- Feature extraction is fitted only on training data.
- The code has tests for important transformations.
- Key NLP decisions and alternatives are documented.

### Milestone 3 — Model Training, Comparison, and Evaluation

**Objective:** Train and fairly compare suitable models.

**Deliverables:**

- Training pipeline
- Candidate model experiments
- Evaluation pipeline
- Metrics and confusion matrices
- Saved best-performing pipeline based on measured results
- Reproducibility instructions
- Updated model card, file logs, project explanation, and development log

**Acceptance criteria:**

- Models are evaluated on an appropriate held-out split.
- No test-set leakage occurs.
- Results are generated from actual runs.
- The selected model is justified by evidence and project requirements.
- Training and evaluation can be reproduced.

### Milestone 4 — FastAPI Backend and Prediction Pipeline

**Objective:** Expose the trained model through a reliable API.

**Deliverables:**

- FastAPI application
- Prediction request and response schemas
- Model loading and inference
- Input validation and error handling
- Explanation response where supported
- API tests
- Updated architecture, source-file logs, project explanation, and development log

**Acceptance criteria:**

- The API loads the saved pipeline.
- Valid text produces a prediction.
- Invalid input produces a controlled error.
- API behaviour is covered by tests.
- Backend instructions work locally.

### Milestone 5 — React Web Application and Explainability

**Objective:** Build a usable frontend connected to the backend.

**Deliverables:**

- React and TypeScript application
- Email input and prediction interface
- Prediction result display
- Supported explanation display
- Model comparison page using real experiment results
- Dataset explorer using verified data
- Prediction history if time and privacy requirements permit
- Frontend tests
- Updated frontend file logs, project explanation, architecture, and development log

**Acceptance criteria:**

- Frontend communicates with the backend.
- The core user flow works end to end.
- Loading, validation, and error states are handled.
- Results shown in the UI come from actual backend responses or experiment outputs.
- The interface does not make unsupported security claims.

### Milestone 6 — Testing, Documentation, Packaging, and Portfolio Readiness

**Objective:** verify the complete application and prepare it for review.

**Deliverables:**

- Backend and frontend test suite
- End-to-end verification of the core flow
- README with setup and run instructions
- Final project explanation
- Final architecture documentation
- Complete source-file explanation logs
- Dataset card and model card
- Development log
- Screenshots or demonstration instructions, if useful
- Optional Docker packaging, only if feasible and tested
- Portfolio-ready project summary based on verified implementation

**Acceptance criteria:**

- A new developer can follow the documented setup.
- Core tests pass, or remaining failures are clearly reported.
- Documentation reflects the final code.
- No fabricated metrics, features, or claims appear.
- Known limitations are stated clearly.
- The repository is ready for user review and a milestone commit.

---

## 14. Quality Requirements

### Correctness

- Predictions must use the same preprocessing and feature extraction pipeline used during training.
- Evaluation must be methodologically sound.
- The API must validate inputs.
- Explanations must reflect the actual model or method.

### Reproducibility

- Record random seeds and relevant configuration.
- Document dataset preparation.
- Document training and evaluation commands.
- Keep experiment outputs identifiable and traceable.

### Maintainability

- Use clear module responsibilities.
- Avoid unnecessary abstraction.
- Keep configuration separate from implementation where appropriate.
- Use meaningful names and type hints where practical.

### Privacy

- Do not store full email content by default.
- Do not commit private data, secrets, or local environment files.
- Explain any stored prediction metadata.

### Testing

- Test important preprocessing behaviour.
- Test feature extraction and training/inference compatibility.
- Test API validation and prediction responses.
- Test frontend states and API integration.
- Report actual test results.

---

## 15. Risks and Constraints

| Risk | Mitigation |
|---|---|
| Dataset structure differs from assumptions | Verify the dataset before writing dependent code |
| Dataset licence restricts redistribution | Document licence and avoid committing raw data |
| Data leakage produces misleading metrics | Split correctly and fit transformations on training data only |
| Class imbalance distorts accuracy | Report precision, recall, F1, and confusion matrix |
| Model explanation is misleading | Use model-supported explanations and document limitations |
| Project scope becomes too large | Prioritise the core end-to-end flow; defer optional features |
| Documentation falls behind code | Update documentation in the same milestone |
| Developer cannot explain AI-generated code | Maintain connected explanation logs and review them after milestones |
| Completion today is unrealistic | Claude must estimate feasibility and identify risks before implementation |

---

## 16. Definition of Done

SpamShield AI is considered portfolio-ready when:

- The dataset has been verified and documented.
- A reproducible ML pipeline has been implemented.
- Multiple candidate models have been evaluated fairly.
- The selected model has measured results.
- The backend exposes working prediction functionality.
- The frontend supports the core classification flow.
- Explanations are implemented where technically supported.
- Tests cover the important application behaviour.
- Setup and execution instructions are verified.
- The primary project explanation connects the entire system.
- Every source file created or substantially modified has an explanation log.
- The development log records the actual chronological work.
- The dataset card and model card are complete.
- All claims in the README and portfolio summary are supported by implementation or measured evidence.

---

## 17. Instructions for Claude — Start Here

Do **not** begin implementation immediately.

First:

1. Review this PRD.
2. Inspect the existing repository and current virtual environment without changing files.
3. Present a final milestone plan with no more than six major milestones.
4. For each milestone, state:
   - Objective
   - Main deliverables
   - Documentation updates
   - Acceptance criteria
5. Estimate whether completing the project today is realistic.
6. Identify the main risks, dependencies, and features that may need to be deferred.
7. Confirm that the workflow will be:
   **Plan → Approval → Implement one milestone → Verify → Update documentation → User review and commit → Approval for next milestone.**

Then **wait for approval**.

Do not create files, install packages, modify the repository, or start Milestone 1 until approval is given.

---

## 18. Approved Decisions

Agreed by the project owner on 2026-11-05 when approving the milestone plan.

### Scope and timing

- Milestones 1–4 are the target for the first day, with Milestone 5 as a stretch only. Results must not be rushed or fabricated to meet this target.

### Dataset licence

- The Kaggle URL in Section 5.1 is recorded as the reported source, and the exact licence is marked "not verified". This replaces the licence and source verification required in Section 5.2 and Milestone 1.
- The raw CSV stays out of Git and is not redistributed. The licence is revisited only if the project owner decides to publish or redistribute the raw data.

### Structure

- Training code lives in `backend/training/`, separate from API inference code. This replaces `train.py` and `evaluate.py` in `backend/app/ml/` in Section 10.
- `features.py` is included only if it has a distinct responsibility. It should be left out if feature extraction is already contained in the scikit-learn pipeline.

### Method

- Begin with a controlled sample before running full character n-gram experiments, because available memory is limited.
- Keep the test set reserved for final evaluation.
- Document the source-leakage experiment carefully, and report its outcome in the model card.

### Milestone 3 requirements

- Compare models on the same split with comparable feature configurations, and select using validation results only.
- Do not use test results to tune models, preprocessing, thresholds or feature choices.
- Derive source-marker words from training data only. Do not describe the experiment as proof of generalisation to unseen sources.
- After freezing the pipeline, evaluate the test set once, reporting overall and similarity-band results with sample counts.
- Avoid broad hyperparameter searches unless a small controlled experiment shows they are feasible.

### Milestone 3 model identity

- Record a deterministic model-content fingerprint separately from the serialized file's SHA-256, without retraining or overwriting the frozen model.

### Milestone 4 requirements

- Provide health, email classification and model information endpoints, with clear validation and error responses.
- Limit input to 20,000 characters.
- Load the frozen pipeline without importing training modules, with no retraining or modification of it.
- Return no probability or confidence percentage, because the selected Linear SVM doesn't provide meaningful calibrated probabilities.
- Explain predictions using a technically justified, model-supported method.
- Test valid, empty and oversized input, model loading, prediction and error handling, and that API predictions match direct inference from the frozen pipeline.

### Website (Milestone 5)

The website is a required deliverable of Milestone 5: a working React and TypeScript frontend connected to the FastAPI backend, not screenshots or a design mock-up. When implemented:

- Provide the exact commands to start the frontend and backend locally, and the local URL.
- It must open in a browser and support email classification end to end.
- Show the actual implemented screens, and explain how the frontend calls the backend.
- Include loading, validation and error states.
- Do not claim the website exists until it has been implemented and verified running.

Further Milestone 5 decisions:

- Add two read-only results endpoints, for the model comparison and dataset pages.
- Defer prediction history, which replaces its inclusion in Sections 6.1 and 8.5 for now.
- Show a caution when fewer than five words are recognised, stating clearly that this threshold is a display warning and not a measured reliability boundary. It must not change the model's prediction or classification threshold.
- Label the raw SVM score as a decision score, never a probability or confidence.
- Keep the frozen model, its metadata and the training pipeline unchanged.
- Keep dataset and model reports restricted to verified aggregate information, with no mock predictions or fabricated metrics in the application.
- Verify responsive layouts at 360, 768 and 1280 pixels, and test the complete application with the real model.
