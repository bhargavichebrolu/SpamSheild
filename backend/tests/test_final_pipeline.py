"""Tests for saving, loading and evaluating the final pipeline. All text is made up."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest

from app.ml.predict import load_pipeline, model_fingerprint
from training import final_evaluation as final
from training import source_leakage, train_final

TEXTS = [
    "win a free prize today 100",
    "free money and a prize",
    "claim your free prize now",
    "meeting moved to monday",
    "monday meeting notes attached",
    "notes from the monday meeting",
]
LABELS = ["Spam", "Spam", "Spam", "Ham", "Ham", "Ham"]
ROWS = pd.DataFrame({"label": LABELS, "text": TEXTS})
BACKEND_DIR = Path(__file__).resolve().parents[1]

FINAL_MODEL = {
    "model_version": "test",
    "model": "logistic_regression",
    "setting_name": "C",
    "setting_value": 1.0,
    "features": "word_1",
}


def fitted_pipeline():
    pipeline = train_final.build_final_pipeline(FINAL_MODEL)
    pipeline.named_steps["tfidf"].set_params(min_df=1, max_df=1.0)
    return pipeline.fit(ROWS["text"], ROWS["label"])


@pytest.fixture
def frozen_files(tmp_path: Path) -> dict[str, Path]:
    """Create a saved pipeline, split file and metadata that match each other."""
    pipeline_path = tmp_path / "pipeline.joblib"
    assignments = tmp_path / "assignments.csv"
    assignments.write_text("row_index,split\n0,train\n", encoding="utf-8", newline="\n")
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "model_version": "test",
                "pipeline_sha256": train_final.save_pipeline(fitted_pipeline(), pipeline_path),
                "split_assignments_sha256": train_final.sha256_file(assignments),
            }
        ),
        encoding="utf-8",
    )
    return {"metadata": metadata_path, "pipeline": pipeline_path, "assignments": assignments}


def test_saved_pipeline_gives_the_same_predictions_after_reloading(tmp_path: Path) -> None:
    pipeline = fitted_pipeline()
    path = tmp_path / "pipeline.joblib"
    train_final.save_pipeline(pipeline, path)
    texts = ["WIN 500 FREE prizes at HTTPS example", "Monday meeting notes"]
    assert load_pipeline(path).predict(texts).tolist() == pipeline.predict(texts).tolist()


def test_saved_pipeline_loads_without_any_training_code(tmp_path: Path) -> None:
    """The API must be able to load the file, importing only from app/."""
    path = tmp_path / "pipeline.joblib"
    train_final.save_pipeline(fitted_pipeline(), path)
    script = (
        "import sys; from pathlib import Path; from app.ml.predict import load_pipeline; "
        f"p = load_pipeline(Path(r'{path}')); "
        "print(p.predict(['free prize money'])[0]); "
        "print(any(name == 'training' or name.startswith('training.') for name in sys.modules))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND_DIR, capture_output=True, text=True, check=True
    )
    assert completed.stdout.split() == ["Spam", "False"]


def test_saved_pipeline_applies_preprocessing_to_raw_text() -> None:
    pipeline = fitted_pipeline()
    assert "escapenumber" in pipeline.named_steps["tfidf"].vocabulary_
    assert pipeline.predict(["WIN A FREE PRIZE 999"])[0] == "Spam"


def test_load_pipeline_explains_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="training.train_final"):
        load_pipeline(tmp_path / "missing.joblib")


def test_metadata_records_settings_hashes_and_versions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assignments = tmp_path / "assignments.csv"
    assignments.write_text("row_index,split\n", encoding="utf-8")
    monkeypatch.setattr(train_final, "SPLIT_ASSIGNMENTS", assignments)
    metadata = train_final.build_metadata(fitted_pipeline(), FINAL_MODEL, "abc", 6)
    assert metadata["setting"] == {"C": 1.0}
    assert metadata["pipeline_sha256"] == "abc"
    assert metadata["classes"] == ["Ham", "Spam"]
    assert metadata["training_split"] == "train"
    assert "scikit-learn" in metadata["versions"]
    assert "meeting" not in json.dumps(metadata)


def test_verify_frozen_accepts_matching_files(frozen_files: dict[str, Path]) -> None:
    metadata = final.verify_frozen(frozen_files["metadata"], frozen_files["pipeline"], frozen_files["assignments"])
    assert metadata["model_version"] == "test"


def test_verify_frozen_refuses_a_changed_pipeline(frozen_files: dict[str, Path]) -> None:
    with open(frozen_files["pipeline"], "ab") as file:
        file.write(b"changed")
    with pytest.raises(final.EvaluationRefused, match="pipeline doesn't match"):
        final.verify_frozen(frozen_files["metadata"], frozen_files["pipeline"], frozen_files["assignments"])


def test_verify_frozen_refuses_a_changed_split(frozen_files: dict[str, Path]) -> None:
    with open(frozen_files["assignments"], "a", encoding="utf-8") as file:
        file.write("1,test\n")
    with pytest.raises(final.EvaluationRefused, match="split file doesn't match"):
        final.verify_frozen(frozen_files["metadata"], frozen_files["pipeline"], frozen_files["assignments"])


def test_verify_frozen_refuses_when_nothing_was_saved(tmp_path: Path) -> None:
    with pytest.raises(final.EvaluationRefused, match="No pipeline metadata"):
        final.verify_frozen(tmp_path / "m.json", tmp_path / "p.joblib", tmp_path / "a.csv")


def test_test_split_can_only_be_evaluated_once(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    final.refuse_repeat_test_run("test", report)
    report.write_text("{}", encoding="utf-8")
    with pytest.raises(final.EvaluationRefused, match="evaluated only once"):
        final.refuse_repeat_test_run("test", report)


def test_validation_can_be_rerun(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("{}", encoding="utf-8")
    final.refuse_repeat_test_run("validation", report)


def test_main_refuses_a_repeat_test_run_before_loading_any_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report = tmp_path / "report.json"
    report.write_text("{}", encoding="utf-8")
    monkeypatch.setitem(final.REPORT_PATHS, "test", report)

    def must_not_load(*_: object, **__: object) -> None:
        raise AssertionError("Rows were loaded despite the refusal")

    monkeypatch.setattr(final, "load_split", must_not_load)
    assert final.main(["--split", "test"]) == 1


def test_class_results_match_a_hand_worked_example() -> None:
    results = final.class_results(
        {"true_ham": 90, "true_spam": 80, "ham_flagged_as_spam": 10, "spam_missed": 20}
    )
    assert results["Ham"] == {
        "rows": 100,
        "precision": round(90 / 110, 4),
        "recall": 0.9,
        "share_wrongly_flagged_as_spam": 0.1,
    }
    assert results["Spam"] == {
        "rows": 100,
        "precision": round(80 / 90, 4),
        "recall": 0.8,
        "share_missed": 0.2,
    }


def test_report_has_counts_for_each_band_and_no_email_text(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = fitted_pipeline()
    relaxed = final.similarity_to_training.__globals__["build_vectorizer"]
    monkeypatch.setitem(
        final.similarity_to_training.__globals__,
        "build_vectorizer",
        lambda name: relaxed(name).set_params(min_df=1, max_df=1.0),
    )
    monkeypatch.setattr(final, "LATENCY_ROWS", 4)
    report = final.build_report(
        "validation",
        pipeline,
        {"model_version": "test", "pipeline_sha256": "abc"},
        ROWS,
        ROWS["text"],
    )
    assert report["rows"] == len(ROWS)
    bands = report["metrics_by_similarity_band"]
    assert sum(band["rows"] for band in bands.values()) == len(ROWS)
    assert all("rows" in band and "share_of_rows" in band for band in bands.values())
    assert "meeting" not in json.dumps(report)


SELECTED = {"features": "word_1", "model": "logistic_regression", "setting": {"C": 1.0}}


def test_words_to_remove_combines_lists_without_repeats() -> None:
    removal = source_leakage.MarkerRemoval("x", (("a", 2), ("b", 2)))
    lists = {"a": ["one", "two", "three"], "b": ["two", "four", "five"]}
    assert source_leakage.words_to_remove(removal, lists) == ["one", "two", "four"]


def test_removed_words_are_absent_from_vocabulary_and_bigrams() -> None:
    pipeline = source_leakage.build_pipeline(SELECTED, ["prize"])
    pipeline.named_steps["tfidf"].set_params(min_df=1, max_df=1.0, ngram_range=(1, 2))
    pipeline.fit(ROWS["text"], ROWS["label"])
    assert not any("prize" in term for term in pipeline.named_steps["tfidf"].vocabulary_)


def test_every_marker_removal_uses_a_known_list() -> None:
    known = {"style_leaning", "ham_leaning", "spam_leaning"}
    for removal in source_leakage.MARKER_REMOVALS.values():
        assert {name for name, _ in removal.lists} <= known


def test_leakage_experiments_never_load_the_test_split(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: list[str] = []

    def fake_load(split: str, **_: object) -> pd.DataFrame:
        requested.append(split)
        return ROWS

    captured: list[dict] = []
    monkeypatch.setattr(source_leakage, "load_split", fake_load)
    monkeypatch.setattr(source_leakage, "selected_model", lambda: SELECTED)
    monkeypatch.setattr(source_leakage, "load_markers", lambda: {"lists": {}})
    monkeypatch.setattr(
        source_leakage, "save_result", lambda section, result, selected: captured.append(result)
    )
    original = source_leakage.build_vectorizer
    monkeypatch.setattr(
        source_leakage,
        "build_vectorizer",
        lambda name: original(name).set_params(min_df=1, max_df=1.0),
    )
    source_leakage.run_one("baseline_no_removal")
    assert requested == ["train", "validation"]
    assert captured[0]["words_removed"] == 0
    assert captured[0]["validation"]["rows"] == len(ROWS)


def style_rows() -> pd.DataFrame:
    rows = []
    for number in range(10, 20):
        rows.append(("Spam", f"free prize money {number}"))
        rows.append(("Ham", f"meeting notes monday {number}"))
        rows.append(("Spam", "free prize money escapenumber"))
        rows.append(("Ham", "meeting notes monday escapenumber"))
    return pd.DataFrame(rows, columns=["label", "text"])


@pytest.mark.parametrize(
    "name, style, words_removed, expected_rows",
    [
        ("train_digits_only", "digits_only", 0, 20),
        ("train_placeholder_only", "placeholder_only", 0, 20),
        ("train_placeholder_only_matched_size", "placeholder_only", 0, 20),
        ("train_digits_only_remove_style_300_and_ham_300", "digits_only", 1, 20),
    ],
)
def test_cross_style_trains_only_on_the_named_style(
    monkeypatch: pytest.MonkeyPatch, name: str, style: str, words_removed: int, expected_rows: int
) -> None:
    monkeypatch.setattr(
        source_leakage,
        "load_markers",
        lambda: {"lists": {"style_leaning": ["notes"], "ham_leaning": ["notes"]}},
    )
    original = source_leakage.build_vectorizer
    monkeypatch.setattr(
        source_leakage,
        "build_vectorizer",
        lambda feature_name: original(feature_name).set_params(min_df=1, max_df=1.0),
    )
    monkeypatch.setattr(source_leakage, "evaluate_pipeline", lambda pipeline, rows: {"rows": len(rows)})
    rows = style_rows()
    result = source_leakage.run_cross_style(name, SELECTED, rows, rows)
    assert result["training_style"] == style
    assert result["words_removed"] == words_removed
    assert result["training_rows"] == expected_rows
    assert result["validation_by_style"]["digits_only"]["rows"] == 20
    assert result["validation_by_style"]["placeholder_only"]["rows"] == 20


def test_cross_style_rejects_an_unknown_run() -> None:
    with pytest.raises(ValueError, match="Unknown cross-style run"):
        source_leakage.run_cross_style("train_everything", SELECTED, ROWS, ROWS)


def leakage_report(baseline: float, removed: float, digits: tuple[float, float], placeholder: tuple[float, float]) -> dict:
    def f1(value: float) -> dict:
        return {"metrics": {"f1_spam": value}}

    name = source_leakage.CANDIDATE_REMOVAL
    return {
        "marker_removal": {
            "baseline_no_removal": {"validation": f1(baseline)},
            name: {"validation": f1(removed)},
        },
        "cross_style": {
            "train_digits_only": {"validation_by_style": {"placeholder_only": f1(digits[0])}},
            f"train_digits_only_{name}": {"validation_by_style": {"placeholder_only": f1(digits[1])}},
            "train_placeholder_only": {"validation_by_style": {"digits_only": f1(placeholder[0])}},
            f"train_placeholder_only_{name}": {"validation_by_style": {"digits_only": f1(placeholder[1])}},
        },
    }


@pytest.mark.parametrize(
    "baseline, removed, digits, placeholder, adopt",
    [
        (0.99, 0.989, (0.80, 0.85), (0.90, 0.91), True),
        (0.99, 0.98, (0.80, 0.85), (0.90, 0.91), False),
        (0.99, 0.989, (0.80, 0.79), (0.90, 0.91), False),
        (0.99, 0.989, (0.80, 0.85), (0.90, 0.90), False),
    ],
)
def test_removal_rule_needs_a_small_cost_and_improvement_both_ways(
    baseline: float, removed: float, digits: tuple, placeholder: tuple, adopt: bool
) -> None:
    decision = source_leakage.decide_removal(leakage_report(baseline, removed, digits, placeholder))
    assert decision["adopt"] is adopt


def test_final_removal_uses_the_training_only_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        train_final, "load_markers", lambda: {"lists": {"style_leaning": ["alpha", "beta"], "ham_leaning": ["beta", "gamma"]}}
    )
    words = train_final.final_removed_words({"removed_words": "remove_style_300_and_ham_300"})
    assert words == ["alpha", "beta", "gamma"]
    assert train_final.final_removed_words({}) == []


def test_final_pipeline_excludes_removed_words(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        train_final, "load_markers", lambda: {"lists": {"style_leaning": ["prize"], "ham_leaning": ["notes"]}}
    )
    pipeline = train_final.build_final_pipeline({**FINAL_MODEL, "removed_words": "remove_style_300_and_ham_300"})
    pipeline.named_steps["tfidf"].set_params(min_df=1, max_df=1.0)
    pipeline.fit(ROWS["text"], ROWS["label"])
    vocabulary = pipeline.named_steps["tfidf"].vocabulary_
    assert "prize" not in vocabulary
    assert "notes" not in vocabulary
    assert "free" in vocabulary


def test_two_fits_learn_identical_values() -> None:
    assert train_final.learned_values_differences(fitted_pipeline(), fitted_pipeline()) == []


def test_learned_values_comparison_detects_a_changed_weight() -> None:
    changed = fitted_pipeline()
    changed.named_steps["classifier"].coef_ = changed.named_steps["classifier"].coef_ + 1
    assert train_final.learned_values_differences(fitted_pipeline(), changed) == ["classifier weights"]


def test_learned_values_comparison_detects_different_vocabulary() -> None:
    other = train_final.build_final_pipeline(FINAL_MODEL)
    other.named_steps["tfidf"].set_params(min_df=1, max_df=1.0)
    other.fit(["other words entirely", "more different words"], ["Ham", "Spam"])
    assert "vocabulary" in train_final.learned_values_differences(fitted_pipeline(), other)


def test_fingerprint_is_the_same_for_identical_fits() -> None:
    assert model_fingerprint(fitted_pipeline()) == model_fingerprint(fitted_pipeline())


def test_fingerprint_survives_saving_and_reloading(tmp_path: Path) -> None:
    pipeline = fitted_pipeline()
    path = tmp_path / "pipeline.joblib"
    train_final.save_pipeline(pipeline, path)
    assert model_fingerprint(load_pipeline(path)) == model_fingerprint(pipeline)


def test_fingerprint_does_not_depend_on_file_bytes(tmp_path: Path) -> None:
    pipeline = fitted_pipeline()
    first, second = tmp_path / "first.joblib", tmp_path / "second.joblib"
    joblib.dump(pipeline, first, compress=3)
    joblib.dump(pipeline, second, compress=0)
    assert first.read_bytes() != second.read_bytes()
    assert model_fingerprint(load_pipeline(first)) == model_fingerprint(load_pipeline(second))


def test_fingerprint_is_the_same_across_processes_with_different_hash_seeds(tmp_path: Path) -> None:
    path = tmp_path / "pipeline.joblib"
    train_final.save_pipeline(fitted_pipeline(), path)
    script = (
        "from pathlib import Path; from app.ml.predict import load_pipeline, model_fingerprint; "
        f"print(model_fingerprint(load_pipeline(Path(r'{path}'))))"
    )
    outputs = {
        subprocess.run(
            [sys.executable, "-c", script],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        ).stdout.strip()
        for seed in ("1", "2")
    }
    assert outputs == {model_fingerprint(load_pipeline(path))}


def test_fingerprint_ignores_the_order_of_removed_words() -> None:
    def with_stop_words(words: list[str]):
        pipeline = train_final.build_final_pipeline(FINAL_MODEL)
        pipeline.named_steps["tfidf"].set_params(min_df=1, max_df=1.0, stop_words=words)
        return pipeline.fit(ROWS["text"], ROWS["label"])

    assert model_fingerprint(with_stop_words(["prize", "notes"])) == model_fingerprint(
        with_stop_words(["notes", "prize"])
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda p: setattr(p.named_steps["classifier"], "coef_", p.named_steps["classifier"].coef_ + 1e-12),
        lambda p: setattr(p.named_steps["classifier"], "intercept_", p.named_steps["classifier"].intercept_ + 1e-12),
        lambda p: p.named_steps["tfidf"].vocabulary_.update({"newword": 0}),
        lambda p: setattr(p.named_steps["tfidf"], "stop_words", ["extra"]),
        lambda p: setattr(p.named_steps["tfidf"], "sublinear_tf", False),
        lambda p: setattr(p.named_steps["tfidf"], "preprocessor", str.upper),
        lambda p: setattr(p.named_steps["classifier"], "C", 2.0),
    ],
    ids=["weights", "intercept", "vocabulary", "removed_words", "tfidf_setting", "preprocessor", "classifier_setting"],
)
def test_fingerprint_detects_a_change(change) -> None:
    pipeline = fitted_pipeline()
    before = model_fingerprint(pipeline)
    change(pipeline)
    assert model_fingerprint(pipeline) != before


def test_fingerprint_detects_changed_preprocessing_behaviour_under_the_same_name() -> None:
    pipeline = fitted_pipeline()
    original = pipeline.named_steps["tfidf"].preprocessor
    before = model_fingerprint(pipeline)

    def changed(text: str) -> str:
        return original(text).replace("escapenumber", "number")

    changed.__module__, changed.__qualname__ = original.__module__, original.__qualname__
    pipeline.named_steps["tfidf"].preprocessor = changed
    assert model_fingerprint(pipeline) != before


def test_metadata_records_the_file_hash_and_content_fingerprint_separately(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assignments = tmp_path / "assignments.csv"
    assignments.write_text("row_index,split\n", encoding="utf-8")
    monkeypatch.setattr(train_final, "SPLIT_ASSIGNMENTS", assignments)
    pipeline = fitted_pipeline()
    metadata = train_final.build_metadata(pipeline, FINAL_MODEL, "file-hash", 6)
    assert metadata["pipeline_sha256"] == "file-hash"
    assert metadata["model_content_sha256"] == model_fingerprint(pipeline)


def test_record_fingerprint_changes_only_the_metadata(frozen_files: dict[str, Path]) -> None:
    pipeline_before = frozen_files["pipeline"].read_bytes()
    metadata_before = json.loads(frozen_files["metadata"].read_text(encoding="utf-8"))

    assert train_final.record_fingerprint(frozen_files["metadata"], frozen_files["pipeline"]) == 0

    assert frozen_files["pipeline"].read_bytes() == pipeline_before
    metadata_after = json.loads(frozen_files["metadata"].read_text(encoding="utf-8"))
    assert metadata_after["model_content_sha256"] == model_fingerprint(load_pipeline(frozen_files["pipeline"]))
    assert {key: metadata_after[key] for key in metadata_before} == metadata_before


def test_record_fingerprint_refuses_a_file_that_does_not_match(frozen_files: dict[str, Path]) -> None:
    with open(frozen_files["pipeline"], "ab") as file:
        file.write(b"changed")
    metadata_before = frozen_files["metadata"].read_text(encoding="utf-8")
    assert train_final.record_fingerprint(frozen_files["metadata"], frozen_files["pipeline"]) == 1
    assert frozen_files["metadata"].read_text(encoding="utf-8") == metadata_before


def test_verify_fingerprint_detects_a_wrong_fingerprint(
    monkeypatch: pytest.MonkeyPatch, frozen_files: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(train_final, "load_split", lambda split, **_: ROWS)
    train_final.record_fingerprint(frozen_files["metadata"], frozen_files["pipeline"])
    assert train_final.verify_fingerprint(frozen_files["metadata"], frozen_files["pipeline"]) == 0
    assert "Fingerprint matches metadata: True" in capsys.readouterr().out

    metadata = json.loads(frozen_files["metadata"].read_text(encoding="utf-8"))
    metadata["model_content_sha256"] = "0" * 64
    frozen_files["metadata"].write_text(json.dumps(metadata), encoding="utf-8")
    assert train_final.verify_fingerprint(frozen_files["metadata"], frozen_files["pipeline"]) == 1


def test_fingerprint_imports_no_training_code(tmp_path: Path) -> None:
    path = tmp_path / "pipeline.joblib"
    train_final.save_pipeline(fitted_pipeline(), path)
    script = (
        "import sys; from pathlib import Path; "
        "from app.ml.predict import load_pipeline, model_fingerprint; "
        f"model_fingerprint(load_pipeline(Path(r'{path}'))); "
        "print(any(name == 'training' or name.startswith('training.') for name in sys.modules))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND_DIR, capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == "False"


def test_final_configuration_matches_a_known_model_and_removal() -> None:
    from training.config import FINAL_MODEL as CONFIGURED
    from training.models import PARAMETER_GRID

    setting_name, values = PARAMETER_GRID[CONFIGURED["model"]]
    assert CONFIGURED["setting_name"] == setting_name
    assert CONFIGURED["setting_value"] in values
    assert CONFIGURED["removed_words"] in source_leakage.MARKER_REMOVALS


def test_interpretation_note_says_this_is_not_proof() -> None:
    assert "not proof of generalisation" in source_leakage.INTERPRETATION_NOTE
