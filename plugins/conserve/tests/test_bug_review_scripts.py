"""Regression tests from the bug review of conserve scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import growth_analyzer
from agent_memory import MemoryManager
from safe_replacer import SafeDependencyUpdater


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


@pytest.fixture
def updater():
    return SafeDependencyUpdater()


@pytest.mark.unit
def test_update_file_does_not_double_prefix_a_file_with_prefixed_and_bare_refs(
    tmp_path: Path, updater
) -> None:
    """A bare reference next to a prefixed one must not turn the prefixed one into sanctum:sanctum:."""
    skill = tmp_path / "SKILL.md"
    skill.write_text("Use sanctum:git-workspace-review, or git-workspace-review.\n")

    updater.update_file(skill)

    assert skill.read_text() == (
        "Use sanctum:git-workspace-review, or sanctum:git-workspace-review.\n"
    )


@pytest.mark.unit
def test_update_file_repairs_wrong_prefix_to_single_correct_prefix(
    tmp_path: Path, updater
) -> None:
    """workspace-utils:X must become sanctum:X, not workspace-utils:sanctum:X."""
    skill = tmp_path / "SKILL.md"
    skill.write_text("Call workspace-utils:git-workspace-review now.\n")

    updater.update_file(skill)

    assert skill.read_text() == "Call sanctum:git-workspace-review now.\n"


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
