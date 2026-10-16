"""In-process tests for homeostatic_monitor.main() branches and error paths.

The subprocess tests in test_homeostatic_monitor_input.py drive the
stdin contract. These run main() in-process, so each early exit, the
queue paths, and the degraded-dependency paths are exercised and counted.
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import homeostatic_monitor as hm  # noqa: E402 - import after sys.path setup

SKILL = "abstract:skill-auditor"
# Worst five-run window rates: 0.8 healthy (gap 0.2), 0.6 degrading
# (gap 0.4), 0.4 critical (gap 0.6).
HEALTHY = [1, 1, 1, 1, 0]
DEGRADING = [1, 1, 0, 0, 1]
CRITICAL = [1, 0, 0, 0, 1]


def _seed(home: Path, accuracies: list[int], skill: str = SKILL) -> None:
    logs = home / "skills" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / ".history.json").write_text(
        json.dumps({skill: {"accuracies": accuracies, "durations": []}})
    )


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    home: Path,
    payload: dict,
) -> tuple[int, str, str]:
    monkeypatch.setenv("CLAUDE_HOME", str(home))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        hm.main()
    out = capsys.readouterr()
    return exc.value.code, out.out, out.err


def _skill_payload(skill: str = SKILL) -> dict:
    return {
        "tool_name": "Skill",
        "tool_input": {"skill": skill},
        "session_id": "sess-1",
    }


class TestEarlyExits:
    """Payloads with nothing to judge exit 0 and print nothing."""

    @pytest.mark.unit
    def test_payload_without_skill_ref_prints_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed(tmp_path, CRITICAL)
        payload = {"tool_name": "Skill", "tool_input": {}, "session_id": "s"}

        code, out, _ = _run_main(monkeypatch, capsys, tmp_path, payload)

        assert (code, out) == (0, "")

    @pytest.mark.unit
    def test_skill_absent_from_history_prints_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed(tmp_path, CRITICAL, skill="other:skill")

        code, out, _ = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        assert (code, out) == (0, "")
        assert not (tmp_path / "skills" / "improvement-queue.json").exists()


class TestReadHistoryErrors:
    """read_history degrades to empty on unreadable or mis-shaped files."""

    @pytest.mark.unit
    def test_unreadable_history_is_reported_and_empty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        (tmp_path / "skills" / "logs" / ".history.json").mkdir(parents=True)

        assert hm.read_history(tmp_path) == {}
        assert "failed to read history file" in capsys.readouterr().err

    @pytest.mark.unit
    def test_non_object_history_is_empty(self, tmp_path: Path) -> None:
        logs = tmp_path / "skills" / "logs"
        logs.mkdir(parents=True)
        (logs / ".history.json").write_text("[1, 2, 3]")

        assert hm.read_history(tmp_path) == {}


class TestDegradedDependencies:
    """Missing or failing optional modules never stop the verdict."""

    @pytest.mark.unit
    def test_tracker_error_is_reported_and_trend_is_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """A tracker entry without skill_ref raises KeyError inside the trend."""
        _seed(tmp_path, HEALTHY)
        (tmp_path / "skills" / "performance_history.json").write_text(
            json.dumps({"history": [{"version": "1.0.0", "score": 0.5}]})
        )

        code, out, err = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        assert code == 0
        verdict = json.loads(out)["hookSpecificOutput"]
        assert verdict["status"] == "healthy"
        assert verdict["improvement_trend"] is None
        assert "homeostatic_monitor: tracker error" in err

    @pytest.mark.unit
    def test_trend_is_none_when_tracker_module_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(hm, "_HAS_TRACKER", False)

        assert hm._get_improvement_trend(tmp_path, SKILL) is None
        assert not (tmp_path / "skills" / "performance_history.json").exists()

    @pytest.mark.unit
    def test_degrading_without_queue_reports_and_skips_queue(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed(tmp_path, DEGRADING)
        monkeypatch.setattr(hm, "_HAS_QUEUE", False)

        code, out, err = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        assert code == 0
        assert json.loads(out)["hookSpecificOutput"]["status"] == "degrading"
        assert "ImprovementQueue unavailable" in err
        assert not (tmp_path / "skills" / "improvement-queue.json").exists()

    @pytest.mark.unit
    @pytest.mark.skipif(
        os.geteuid() == 0, reason="root ignores directory write permission"
    )
    def test_read_only_claude_home_warns_and_skips_the_queue(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """A read-only ~/.claude costs the queue update, not the hook."""
        _seed(tmp_path, DEGRADING)
        skills = tmp_path / "skills"
        skills.chmod(0o500)
        try:
            code, out, err = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())
        finally:
            skills.chmod(0o700)

        assert code == 0
        assert json.loads(out)["hookSpecificOutput"]["status"] == "degrading"
        assert "queue not updated" in err
        assert not (skills / "improvement-queue.json").exists()

    @pytest.mark.unit
    def test_malformed_memory_outcome_is_reported_not_raised(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An outcome missing 'improvement' raises KeyError in the memory API."""
        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "improvement_memory.json").write_text(
            json.dumps({"insights": {}, "outcomes": {SKILL: [{"timestamp": "t"}]}})
        )

        assert hm._needs_metacognition(tmp_path) is False
        assert "_needs_metacognition" in capsys.readouterr().err


class TestQueueFlagging:
    """A degrading skill is flagged, rated, and escalated on the third flag."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("accuracies", "status"),
        [(DEGRADING, "degrading"), (CRITICAL, "critical")],
        ids=["gap-0.4", "gap-0.6"],
    )
    def test_flag_status_follows_the_critical_threshold(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
        accuracies: list[int],
        status: str,
    ) -> None:
        _seed(tmp_path, accuracies)

        code, out, _ = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        verdict = json.loads(out)["hookSpecificOutput"]
        assert code == 0
        assert verdict["status"] == status
        assert verdict["flagged_count"] == 1
        assert verdict["improvement_triggered"] is False

    @pytest.mark.unit
    def test_third_flag_triggers_improvement_and_says_so(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed(tmp_path, DEGRADING)
        for _ in range(2):
            _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        code, out, err = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        verdict = json.loads(out)["hookSpecificOutput"]
        assert code == 0
        assert verdict["flagged_count"] == 3
        assert verdict["improvement_triggered"] is True
        assert f"HOMEOSTATIC: {SKILL} flagged 3x" in err

    @pytest.mark.unit
    @pytest.mark.parametrize("held", ["evaluating", "pending_rollback_review"])
    def test_skill_under_evaluation_is_not_reflagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, held: str
    ) -> None:
        _seed(tmp_path, DEGRADING)
        queue_file = tmp_path / "skills" / "improvement-queue.json"
        entry = {
            "skill_name": SKILL,
            "stability_gap": 0.4,
            "flagged_count": 0,
            "last_flagged": "",
            "execution_ids": [],
            "status": held,
        }
        queue_file.write_text(json.dumps({"skills": {SKILL: entry}}))

        code, out, _ = _run_main(monkeypatch, capsys, tmp_path, _skill_payload())

        assert (code, out) == (0, "")
        stored = json.loads(queue_file.read_text())["skills"][SKILL]
        assert stored["flagged_count"] == 0
