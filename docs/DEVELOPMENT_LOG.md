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
