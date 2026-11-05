"""The tracker file is replaced whole, through a temp name no writer shares.

Feature: tracker persistence
    As two minister processes saving the same tracker
    I want each save to stage its own temp file
    So that one process's rename never publishes the other's half-written file
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from minister.project_tracker import ProjectTracker


@pytest.mark.unit
def test_two_saves_do_not_share_a_temp_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fixed ``tracker.json.tmp`` sibling let concurrent writers clobber."""
    data_file = tmp_path / "tracker.json"
    first = ProjectTracker(data_file=data_file)
    second = ProjectTracker(data_file=data_file)
    sources: list[str] = []
    real_replace = os.replace

    def record(src: str, dst: str) -> None:
        sources.append(str(src))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", record)

    first._save_data()
    second._save_data()

    assert len(sources) == 2
    assert sources[0] != sources[1]


@pytest.mark.unit
def test_interrupted_save_keeps_the_tracker_and_leaves_no_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl-C between staging and rename must not strand the temp file."""
    data_file = tmp_path / "tracker.json"
    tracker = ProjectTracker(data_file=data_file)
    tracker._save_data()
    saved = data_file.read_text(encoding="utf-8")

    def interrupt(src: str, dst: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", interrupt)

    with pytest.raises(KeyboardInterrupt):
        tracker._save_data()

    assert data_file.read_text(encoding="utf-8") == saved
    assert [p.name for p in tmp_path.iterdir()] == ["tracker.json"]
    assert json.loads(saved)["tasks"] == []


@pytest.mark.unit
def test_save_keeps_the_mode_the_tracker_already_had(tmp_path: Path) -> None:
    """The old plain write kept the tracker's mode; the atomic one does too."""
    data_file = tmp_path / "tracker.json"
    tracker = ProjectTracker(data_file=data_file)
    tracker._save_data()
    data_file.chmod(0o644)

    tracker._save_data()

    assert stat.S_IMODE(data_file.stat().st_mode) == 0o644
