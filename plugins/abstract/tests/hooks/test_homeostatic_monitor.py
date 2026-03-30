"""Tests for the homeostatic monitor hook.

Covers the pure-function logic: stability gap calculation,
history reading, and Claude home resolution. The main() entry
point is integration-tested indirectly via skill observability.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add hooks directory to path for direct import
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from homeostatic_monitor import (  # noqa: E402 - import after sys.path setup
    calculate_stability_gap,
    get_claude_home,
    read_history,
)


class TestCalculateStabilityGap:
    """Feature: Stability gap measurement.

    As a homeostatic monitor
    I want to measure the gap between average and worst accuracy
    So that degrading skills are flagged for improvement
    """

    def test_empty_accuracies_returns_zero(self) -> None:
        """Scenario: No accuracy data available.

        Given a history entry with no accuracies
        When calculating stability gap
        Then the result is 0.0
        """
        assert calculate_stability_gap({}) == 0.0
        assert calculate_stability_gap({"accuracies": []}) == 0.0

    def test_uniform_accuracies_returns_zero(self) -> None:
        """Scenario: All executions had the same accuracy.

        Given accuracies [0.9, 0.9, 0.9]
        When calculating stability gap
        Then gap is 0.0 (no variance)
        """
        entry = {"accuracies": [0.9, 0.9, 0.9]}
        assert calculate_stability_gap(entry) == pytest.approx(0.0)

    def test_varied_accuracies_computes_gap(self) -> None:
        """Scenario: Mixed accuracy results.

        Given accuracies [1.0, 0.8, 0.6]
        When calculating stability gap
        Then gap = avg(0.8) - min(0.6) = 0.2
        """
        entry = {"accuracies": [1.0, 0.8, 0.6]}
        assert calculate_stability_gap(entry) == pytest.approx(0.2)

    def test_single_accuracy_returns_zero(self) -> None:
        """Scenario: Only one accuracy measurement.

        Given accuracies [0.75]
        When calculating stability gap
        Then gap is 0.0 (avg == min for single element)
        """
        entry = {"accuracies": [0.75]}
        assert calculate_stability_gap(entry) == pytest.approx(0.0)

    def test_large_gap_detected(self) -> None:
        """Scenario: One bad execution among good ones.

        Given accuracies [1.0, 1.0, 0.2]
        When calculating stability gap
        Then gap > 0.5 (critical threshold)
        """
        entry = {"accuracies": [1.0, 1.0, 0.2]}
        gap = calculate_stability_gap(entry)
        assert gap > 0.5


class TestReadHistory:
    """Feature: Execution history persistence.

    As a homeostatic monitor
    I want to read skill execution history from disk
    So that I can track accuracy trends
    """

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: History file does not exist.

        Given no history file on disk
        When reading history
        Then an empty dict is returned
        """
        result = read_history(tmp_path / "nonexistent")
        assert result == {}

    def test_valid_history_file(self, tmp_path: Path) -> None:
        """Scenario: Valid history JSON.

        Given a history file with skill data
        When reading history
        Then the parsed dict is returned
        """
        logs_dir = tmp_path / "skills" / "logs"
        logs_dir.mkdir(parents=True)
        history = {"my-skill": {"accuracies": [0.9, 0.8]}}
        (logs_dir / ".history.json").write_text(json.dumps(history))
        result = read_history(tmp_path)
        assert "my-skill" in result
        assert result["my-skill"]["accuracies"] == [0.9, 0.8]

    def test_corrupt_json_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: Corrupt history file.

        Given a history file with invalid JSON
        When reading history
        Then an empty dict is returned (no crash)
        """
        logs_dir = tmp_path / "skills" / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / ".history.json").write_text("{bad json")
        result = read_history(tmp_path)
        assert result == {}


class TestGetClaudeHome:
    """Feature: Claude home directory resolution."""

    def test_uses_env_var_when_set(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Scenario: CLAUDE_HOME is set."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        assert get_claude_home() == tmp_path

    def test_falls_back_to_home_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: CLAUDE_HOME is not set."""
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        result = get_claude_home()
        assert result.name == ".claude"
