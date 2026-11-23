"""Regression tests from the bug review of conserve scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import growth_analyzer
from agent_memory import MemoryManager


@pytest.mark.unit
def test_archive_to_cold_keeps_earlier_archive_for_same_period(tmp_path: Path) -> None:
    """A second archive in the same period must not erase the first."""
    manager = MemoryManager(tmp_path / "agent-x")
    manager.init()

    manager.archive_to_cold("2026-03", "first summary")
    manager.archive_to_cold("2026-03", "second summary")

    archived = (tmp_path / "agent-x" / "archive" / "2026-03.md").read_text()
    assert "first summary" in archived
    assert "second summary" in archived


@pytest.mark.unit
def test_growth_analyzer_turns_flag_limits_projection_horizon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--turns 10 must drop the 20-turn projection."""
    context = tmp_path / "context.json"
    context.write_text(
        json.dumps({"growth_trend": {"current_usage": 30, "rate": 0.05}})
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "growth_analyzer.py",
            "--context-file",
            str(context),
            "--output-json",
            "--turns",
            "10",
        ],
    )

    growth_analyzer.main()

    projections = json.loads(capsys.readouterr().out)["projections"]
    assert "10_turns" in projections
    assert "20_turns" not in projections


@pytest.mark.parametrize("bad", ["../../escaped", "a/b", "..", ""])
def test_topic_name_with_parent_segments_is_refused(tmp_path: Path, bad: str) -> None:
    """A `../` topic or period wrote outside the agent's tier directories."""
    manager = MemoryManager(tmp_path / "agent-x")
    with pytest.raises(ValueError, match="file name"):
        manager.write_warm_topic(bad, "x")
    with pytest.raises(ValueError, match="file name"):
        manager.archive_to_cold(bad, "x")
    assert not (tmp_path / "escaped.md").exists()
