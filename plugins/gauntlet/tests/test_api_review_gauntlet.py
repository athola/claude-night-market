"""Regression tests for API-review findings."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from gauntlet.blast_radius import analyze_changes
from gauntlet.graph import GraphStore
from gauntlet.incremental import incremental_update
from gauntlet.models import AnswerRecord, ChallengeType
from gauntlet.progress import ProgressTracker
from gauntlet.search import detect_kind_boost


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    return GraphStore(tmp_path / "graph.db")


def _progress_file(tmp_path: Path) -> Path:
    return tmp_path / "progress" / "dev.json"


def test_corrupt_progress_file_is_moved_aside_before_fresh_record(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = _progress_file(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{bad")

    progress = ProgressTracker(tmp_path).get_or_create("dev")

    assert progress.history == []
    assert not path.exists()
    assert path.with_suffix(".json.corrupt").read_text() == "{bad"
    assert str(path) in caplog.text


def test_progress_with_retired_enum_value_is_moved_aside_not_raised(
    tmp_path: Path,
) -> None:
    path = _progress_file(tmp_path)
    path.parent.mkdir(parents=True)
    tracker = ProgressTracker(tmp_path)
    good = tracker.get_or_create("dev")
    tracker.record_answer(
        good,
        AnswerRecord(
            challenge_id="c1",
            knowledge_entry_id="k1",
            challenge_type=next(iter(ChallengeType)),
            category="cat",
            difficulty=1,
            result="pass",
        ),
    )
    payload = json.loads(path.read_text())
    payload["history"][0]["challenge_type"] = "retired_type"
    path.write_text(json.dumps(payload))

    fresh = tracker.get_or_create("dev")

    assert fresh.history == []
    assert path.with_suffix(".json.corrupt").exists()


def test_analyze_changes_reports_unknown_risk_when_git_fails(
    store: GraphStore,
) -> None:
    with patch("gauntlet.blast_radius.subprocess.run", side_effect=FileNotFoundError):
        report = analyze_changes(store)
    assert report["overall_risk"] == "unknown"
    assert "error" in report


def test_analyze_changes_empty_diff_has_full_result_shape(store: GraphStore) -> None:
    ok = type("R", (), {"returncode": 0, "stdout": ""})()
    with patch("gauntlet.blast_radius.subprocess.run", return_value=ok):
        report = analyze_changes(store)
    assert report["overall_risk"] == "none"
    assert report["total_affected"] == 0
    assert report["direct_changes"] == 0
    assert report["untested_functions"] == []


def test_dotted_query_yields_only_node_kind_boosts() -> None:
    assert detect_kind_boost("pkg.module.func") == {}


def test_incremental_update_reports_error_when_git_times_out(
    tmp_path: Path, store: GraphStore
) -> None:
    with patch(
        "gauntlet.incremental.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="git", timeout=10),
    ):
        report = incremental_update(str(tmp_path), store)
    assert "error" in report
    assert "skipped" not in report
    assert report["edges_resolved"] == 0


def test_incremental_update_no_changes_carries_edges_resolved(
    tmp_path: Path, store: GraphStore
) -> None:
    with patch("gauntlet.incremental.get_changed_files", return_value=[]):
        report = incremental_update(str(tmp_path), store)
    assert report["edges_resolved"] == 0


def test_second_corrupt_progress_file_keeps_the_first_backup(tmp_path: Path) -> None:
    path = _progress_file(tmp_path)
    path.parent.mkdir(parents=True)
    tracker = ProgressTracker(tmp_path)
    path.write_text("{first")
    tracker.get_or_create("dev")
    path.write_text("{second")

    tracker.get_or_create("dev")

    backups = sorted(p.read_text() for p in path.parent.glob("dev.json*.corrupt"))
    assert backups == ["{first", "{second"]


def test_corrupt_progress_already_moved_by_another_load_returns_fresh(
    tmp_path: Path,
) -> None:
    path = _progress_file(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{bad")

    with patch.object(Path, "replace", side_effect=FileNotFoundError(str(path))):
        progress = ProgressTracker(tmp_path).get_or_create("dev")

    assert progress.history == []
