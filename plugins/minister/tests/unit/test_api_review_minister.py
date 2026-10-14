"""Regression tests from the API review."""

from __future__ import annotations

import json

import pytest

from minister.project_tracker import ProjectTracker, Task, run_cli


def test_update_task_raises_key_error_when_task_id_unknown(
    empty_tracker: ProjectTracker,
) -> None:
    """An unknown task id is an error, not a silent no-op."""
    with pytest.raises(KeyError, match="nope"):
        empty_tracker.update_task("nope", {"status": "Done"})


def test_update_task_raises_value_error_when_field_is_not_a_task_field(
    empty_tracker: ProjectTracker, minimal_task: Task
) -> None:
    """A typo'd field name is rejected, not set as a transient attribute."""
    empty_tracker.add_task(minimal_task)
    with pytest.raises(ValueError, match="statuss"):
        empty_tracker.update_task(minimal_task.id, {"statuss": "Done"})
    assert not hasattr(empty_tracker.data.tasks[0], "statuss")


def test_update_command_exits_nonzero_when_task_id_unknown(
    empty_tracker: ProjectTracker,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI reports the failure instead of printing success."""
    monkeypatch.setattr(
        "minister.project_tracker.ProjectTracker", lambda *a, **k: empty_tracker
    )
    code = run_cli(["--output-json", "update", "--id", "nope", "--status", "Done"])
    assert code == 1
    assert json.loads(capsys.readouterr().out)["success"] is False
