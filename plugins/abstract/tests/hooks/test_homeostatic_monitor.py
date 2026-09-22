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

import homeostatic_monitor as hm  # noqa: E402 - import after sys.path setup
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


def _write_memory(claude_home: Path, outcomes: dict[str, list[dict]]) -> Path:
    """Plant an improvement_memory.json where _needs_metacognition looks.

    The file is written directly rather than through ImprovementMemory so
    that each test states the exact outcome mix its trigger needs, with
    no dependence on how record_outcome scores an improvement.
    """
    skills_dir = claude_home / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    mem_file = skills_dir / "improvement_memory.json"
    mem_file.write_text(json.dumps({"insights": {}, "outcomes": outcomes}))
    return mem_file


def _outcome(improvement: float, *, timestamp: str, outcome_type: str) -> dict:
    """One outcome record in the shape ImprovementMemory reads back."""
    return {
        "improvement": improvement,
        "outcome_type": outcome_type,
        "timestamp": timestamp,
    }


class TestNeedsMetacognition:
    """Feature: deciding when a metacognitive pass is warranted.

    As a homeostatic monitor
    I want to recommend deeper analysis only on specific signals
    So that the expensive pass runs when it can pay for itself.
    """

    def test_returns_false_when_memory_is_unavailable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: the ImprovementMemory import failed at load time
        When: _needs_metacognition is asked
        Then: it declines, without touching the filesystem
        """
        _write_memory(
            tmp_path, {"a:b": [_outcome(-1.0, timestamp="1", outcome_type="failure")]}
        )
        monkeypatch.setattr(hm, "_HAS_MEMORY", False)

        assert hm._needs_metacognition(tmp_path) is False

    def test_returns_false_when_no_memory_file_exists(self, tmp_path: Path) -> None:
        """Given: no improvement_memory.json under the Claude home
        When: _needs_metacognition is asked
        Then: it declines rather than creating one
        """
        assert hm._needs_metacognition(tmp_path) is False
        assert not (tmp_path / "skills" / "improvement_memory.json").exists()

    def test_returns_false_when_memory_holds_no_outcomes(self, tmp_path: Path) -> None:
        """Given: a memory file with an empty outcomes map
        When: _needs_metacognition is asked
        Then: it declines, because there is nothing to reason about
        """
        _write_memory(tmp_path, {})

        assert hm._needs_metacognition(tmp_path) is False

    def test_triggers_when_effectiveness_falls_below_half(self, tmp_path: Path) -> None:
        """Given: five outcomes of which two improved and three regressed
        When: _needs_metacognition is asked
        Then: it recommends the pass on the low-effectiveness trigger

        Two of five is 0.4, under the 0.5 bar, and five meets the
        five-outcome minimum. One fewer outcome would fail the minimum
        instead, which is the neighbouring branch.
        """
        _write_memory(
            tmp_path,
            {
                "a:b": [
                    _outcome(0.5, timestamp="1", outcome_type="success"),
                    _outcome(0.5, timestamp="2", outcome_type="success"),
                    _outcome(-0.5, timestamp="3", outcome_type="failure"),
                    _outcome(-0.5, timestamp="4", outcome_type="failure"),
                    _outcome(-0.5, timestamp="5", outcome_type="failure"),
                ]
            },
        )

        assert hm._needs_metacognition(tmp_path) is True

    def test_triggers_on_every_tenth_outcome(self, tmp_path: Path) -> None:
        """Given: exactly ten outcomes, all of them improvements
        When: _needs_metacognition is asked
        Then: it recommends the pass on the periodic trigger

        Effectiveness is 1.0 here and no outcome regressed, so the
        low-effectiveness and recent-regression triggers are both ruled
        out and only the count can explain a True.
        """
        _write_memory(
            tmp_path,
            {
                "a:b": [
                    _outcome(0.5, timestamp=str(i), outcome_type="success")
                    for i in range(10)
                ]
            },
        )

        assert hm._needs_metacognition(tmp_path) is True

    def test_triggers_when_the_most_recent_outcome_regressed(
        self, tmp_path: Path
    ) -> None:
        """Given: eight improvements and one regression, the regression latest
        When: _needs_metacognition is asked
        Then: it recommends the pass on the recent-regression trigger

        Nine outcomes clears neither the effectiveness bar (8/9 is well
        over half) nor the periodic one (9 % 10 is not 0), so the
        ordering by timestamp is what decides this case.
        """
        outcomes = [
            _outcome(0.5, timestamp=f"2026-01-{i:02d}", outcome_type="success")
            for i in range(1, 9)
        ]
        outcomes.append(_outcome(-0.5, timestamp="2026-02-01", outcome_type="failure"))
        _write_memory(tmp_path, {"a:b": outcomes})

        assert hm._needs_metacognition(tmp_path) is True

    def test_declines_when_the_regression_is_not_the_latest_outcome(
        self, tmp_path: Path
    ) -> None:
        """Given: the same nine outcomes with the regression oldest
        When: _needs_metacognition is asked
        Then: it declines

        The mirror of the test above. Both mixes hold one regression, so
        a check that merely asked whether any failure exists would pass
        both; only sorting by timestamp separates them.
        """
        outcomes = [_outcome(-0.5, timestamp="2026-01-01", outcome_type="failure")]
        outcomes.extend(
            _outcome(0.5, timestamp=f"2026-02-{i:02d}", outcome_type="success")
            for i in range(1, 9)
        )
        _write_memory(tmp_path, {"a:b": outcomes})

        assert hm._needs_metacognition(tmp_path) is False


class TestStewardshipVelocity:
    """Feature: counting stewardship actions from the JSONL tracker."""

    def test_returns_zero_when_tracker_is_absent(self, tmp_path: Path) -> None:
        """Given: no stewardship/actions.jsonl
        When: _stewardship_velocity is asked
        Then: it reports zero actions
        """
        assert hm._stewardship_velocity(tmp_path) == 0

    def test_counts_only_non_blank_lines(self, tmp_path: Path) -> None:
        """Given: a tracker holding three records padded with blank lines
        When: _stewardship_velocity is asked
        Then: it reports three

        A trailing newline is normal for an append-only file, so the
        blank-line skip is load-bearing rather than defensive.
        """
        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        (actions_dir / "actions.jsonl").write_text(
            '{"action": "a"}\n\n{"action": "b"}\n   \n{"action": "c"}\n'
        )

        assert hm._stewardship_velocity(tmp_path) == 3

    def test_reports_zero_and_names_the_file_when_it_cannot_be_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Given: a tracker whose read fails with OSError
        When: _stewardship_velocity is asked
        Then: it reports zero and names the unreadable path on stderr

        The velocity feeds a hook that must not break the session, so
        the failure is swallowed; naming the path is what keeps the
        swallow from being silent.
        """
        actions_dir = tmp_path / "stewardship"
        actions_dir.mkdir(parents=True)
        actions_file = actions_dir / "actions.jsonl"
        actions_file.write_text("{}\n")

        def boom(*args: object, **kwargs: object) -> str:
            raise OSError("disk gone")

        monkeypatch.setattr(Path, "read_text", boom)

        assert hm._stewardship_velocity(tmp_path) == 0

        stderr = capsys.readouterr().err
        assert str(actions_file) in stderr
        assert "disk gone" in stderr


class TestBuildOutput:
    """Feature: the hookSpecificOutput envelope the monitor emits."""

    def test_wraps_the_health_fields_under_hook_specific_output(self) -> None:
        """Given: a skill's gap, status, velocity and trend
        When: _build_output assembles the payload
        Then: every field sits under hookSpecificOutput with the
        PostToolUse event name
        """
        output = hm._build_output("abstract:auditor", 0.42, "degrading", 7, 0.1)

        assert output == {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "monitor": "homeostatic",
                "skill": "abstract:auditor",
                "stability_gap": 0.42,
                "status": "degrading",
                "stewardship_actions": 7,
                "improvement_trend": 0.1,
            }
        }

    def test_extra_keyword_fields_join_the_payload(self) -> None:
        """Given: extra fields passed alongside the fixed ones
        When: _build_output assembles the payload
        Then: they sit beside the fixed fields rather than nested
        """
        output = hm._build_output(
            "abstract:auditor",
            0.9,
            "critical",
            0,
            None,
            flagged_count=3,
            improvement_triggered=True,
        )

        payload = output["hookSpecificOutput"]
        assert payload["flagged_count"] == 3
        assert payload["improvement_triggered"] is True
        assert payload["improvement_trend"] is None
