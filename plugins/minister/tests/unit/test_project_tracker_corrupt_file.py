"""A tracker file that fails to parse must not be overwritten by the next save.

``_load_data`` used to return an empty tracker on a parse error, and the
next ``add_task`` wrote that empty tracker over the file: one truncated
write destroyed every tracked initiative.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pytest

from minister.project_tracker import ProjectTracker, Task


def _task(task_id: str) -> Task:
    return Task(
        id=task_id,
        title="t",
        initiative="init",
        phase="build",
        priority="low",
        status="pending",
        owner="me",
        effort_hours=1.0,
        completion_percent=0.0,
        due_date="2026-10-01",
        created_date="2026-09-21",
        updated_date="2026-09-21",
    )


def test_corrupt_file_is_set_aside_before_the_next_save(tmp_path: Path) -> None:
    """The unparseable bytes survive under a corrupt-* name; the new save is clean."""
    data_file = tmp_path / "tracker.json"
    data_file.write_text('{"tasks": [', encoding="utf-8")

    tracker = ProjectTracker(data_file=data_file)
    tracker.add_task(_task("new"))

    aside = list(tmp_path.glob("tracker.corrupt-*.json"))
    assert len(aside) == 1, aside
    assert aside[0].read_text(encoding="utf-8") == '{"tasks": ['
    assert [t["id"] for t in json.loads(data_file.read_text())["tasks"]] == ["new"]


def test_save_leaves_no_temp_file_and_a_parseable_tracker(tmp_path: Path) -> None:
    """The rename step leaves only the tracker behind."""
    data_file = tmp_path / "tracker.json"
    tracker = ProjectTracker(data_file=data_file)
    tracker.add_task(_task("a"))

    assert json.loads(data_file.read_text(encoding="utf-8"))["tasks"][0]["id"] == "a"
    assert list(tmp_path.iterdir()) == [data_file]


def test_interrupted_save_keeps_the_previous_tracker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dump that dies partway leaves the last good tracker parseable."""
    data_file = tmp_path / "tracker.json"
    tracker = ProjectTracker(data_file=data_file)
    tracker.add_task(_task("a"))

    def fail_before_publish(src: object, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fail_before_publish)
    with pytest.raises(OSError, match="disk full"):
        tracker.add_task(_task("b"))
    monkeypatch.undo()

    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert [t["id"] for t in saved["tasks"]] == ["a"]


def test_corrupt_file_that_cannot_be_moved_aside_is_logged_and_left_in_place(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When the rename fails the warning says the file stayed; the bytes stay."""
    data_file = tmp_path / "tracker.json"
    data_file.write_text('{"tasks": [', encoding="utf-8")

    def refuse(src: object, dst: object) -> None:
        raise PermissionError("read-only directory")

    monkeypatch.setattr(os, "replace", refuse)
    with caplog.at_level(logging.WARNING, logger="minister.project_tracker"):
        tracker = ProjectTracker(data_file=data_file)

    assert tracker.data.tasks == []
    assert data_file.read_text(encoding="utf-8") == '{"tasks": ['
    assert list(tmp_path.glob("tracker.corrupt-*.json")) == []
    assert "moved aside to None" not in caplog.text
    assert "left in place" in caplog.text
