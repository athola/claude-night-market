"""A tracker file that fails to parse must not be overwritten by the next save.

``_load_data`` used to return an empty tracker on a parse error, and the
next ``add_task`` wrote that empty tracker over the file: one truncated
write destroyed every tracked initiative.
"""

from __future__ import annotations

import json
from pathlib import Path

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
