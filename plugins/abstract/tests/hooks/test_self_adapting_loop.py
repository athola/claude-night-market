"""The ADR-0006 loop, driven through the hooks that run it.

Each test feeds a hook the payload Claude Code sends and checks the
file or output the next stage of the loop reads: the logger stores an
experience, the pre hook injects it, and the homeostatic monitor moves
a skill through its evaluation window.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from abstract.experience_library import ExperienceLibrary
from abstract.improvement_queue import ImprovementQueue

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import homeostatic_monitor as hm

SKILL = "abstract:skill-auditor"
_LEGACY_ENV = (
    "CLAUDE_TOOL_NAME",
    "CLAUDE_TOOL_INPUT",
    "CLAUDE_TOOL_OUTPUT",
    "CLAUDE_SESSION_ID",
)


def _run_hook(name: str, payload: dict, home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CLAUDE_HOME"] = str(home)
    for key in _LEGACY_ENV:
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(_HOOKS_DIR / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _library(home: Path) -> ExperienceLibrary:
    return ExperienceLibrary(home / "skills" / "experience-library")


def _post_payload(tool_input: dict, response: object) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": tool_input,
        "tool_response": response,
        "session_id": "sess-1",
    }


class TestLoggerStoresExperience:
    """A successful Skill call becomes an experience-library entry."""

    @pytest.mark.unit
    def test_successful_execution_with_args_is_stored(self, tmp_path: Path) -> None:
        payload = _post_payload(
            {"skill": SKILL, "args": "audit the hooks directory"}, {"success": True}
        )

        result = _run_hook("skill_execution_logger.py", payload, tmp_path)

        assert result.returncode == 0, result.stderr
        entries = _library(tmp_path).list_entries(SKILL)
        assert [e["task_description"] for e in entries] == ["audit the hooks directory"]
        # The hook knows nothing about approach or tools; it must not
        # invent them.
        assert entries[0]["approach_taken"] == ""
        assert entries[0]["tools_used"] == []

    @pytest.mark.unit
    def test_failed_execution_is_not_stored(self, tmp_path: Path) -> None:
        payload = _post_payload(
            {"skill": SKILL, "args": "audit the hooks directory"},
            "Error: skill failed to load",
        )

        result = _run_hook("skill_execution_logger.py", payload, tmp_path)

        assert result.returncode == 0, result.stderr
        assert not (tmp_path / "skills" / "experience-library").exists()

    @pytest.mark.unit
    def test_execution_without_args_is_not_stored(self, tmp_path: Path) -> None:
        """No args means no task to recall; every such call shares one hash."""
        payload = _post_payload({"skill": SKILL}, {"success": True})

        result = _run_hook("skill_execution_logger.py", payload, tmp_path)

        assert result.returncode == 0, result.stderr
        assert not (tmp_path / "skills" / "experience-library").exists()


class TestPreHookInjectsExperience:
    """The PreToolUse hook puts recent experiences in additionalContext."""

    @staticmethod
    def _context(home: Path) -> str:
        payload = {
            "tool_name": "Skill",
            "tool_input": {"skill": SKILL},
            "session_id": "sess-1",
        }
        result = _run_hook("pre_skill_execution.py", payload, home)
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        return str(output["hookSpecificOutput"]["additionalContext"])

    @pytest.mark.unit
    def test_no_library_leaves_the_base_context(self, tmp_path: Path) -> None:
        assert self._context(tmp_path) == f"[Skill Invocation] Executing {SKILL}"

    @pytest.mark.unit
    def test_injects_at_most_three_most_recent_entries(self, tmp_path: Path) -> None:
        library = _library(tmp_path)
        for task in ("task one", "task two", "task three", "task four"):
            library.store(
                skill_ref=SKILL,
                task_description=task,
                approach_taken="",
                outcome="success",
                duration_ms=10,
            )

        context = self._context(tmp_path)

        assert "task four" in context
        assert "task three" in context
        assert "task two" in context
        assert "task one" not in context

    @pytest.mark.unit
    def test_long_entry_is_capped(self, tmp_path: Path) -> None:
        _library(tmp_path).store(
            skill_ref=SKILL,
            task_description="x" * 10_000,
            approach_taken="",
            outcome="success",
            duration_ms=10,
        )

        context = self._context(tmp_path)

        # Injected, but at ~500 tokens (4 characters each) plus headers.
        assert "x" * 100 in context
        assert len(context) < 2_500

    @pytest.mark.unit
    def test_other_skills_entries_are_not_injected(self, tmp_path: Path) -> None:
        _library(tmp_path).store(
            skill_ref="other:skill",
            task_description="unrelated task",
            approach_taken="",
            outcome="success",
            duration_ms=10,
        )

        assert "unrelated task" not in self._context(tmp_path)


# Worst five-run window rates: 0.8 healthy (gap 0.2), 0.4 critical (gap 0.6).
HEALTHY = [1, 1, 1, 1, 0]
CRITICAL = [1, 0, 0, 0, 1]


def _seed_history(home: Path, accuracies: list[int]) -> None:
    logs = home / "skills" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / ".history.json").write_text(
        json.dumps({SKILL: {"accuracies": accuracies, "durations": []}})
    )


def _queue(home: Path) -> ImprovementQueue:
    return ImprovementQueue(home / "skills" / "improvement-queue.json")


def _start_evaluation(home: Path, baseline: float, target: int) -> None:
    queue = _queue(home)
    queue.flag_skill(SKILL, baseline, "exec-0")
    queue.start_evaluation(SKILL, baseline)
    queue.skills[SKILL]["eval_target"] = target
    queue._save()


def _run_monitor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, home: Path
) -> tuple[int, str]:
    monkeypatch.setenv("CLAUDE_HOME", str(home))
    payload = {"tool_name": "Skill", "tool_input": {"skill": SKILL}, "session_id": "s"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        hm.main()
    return exc.value.code, capsys.readouterr().out


class TestMonitorDrivesEvaluationWindow:
    """An evaluating skill records each execution and is decided when full."""

    @pytest.mark.unit
    def test_healthy_execution_is_recorded_during_evaluation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed_history(tmp_path, HEALTHY)
        _start_evaluation(tmp_path, baseline=0.6, target=10)

        code, out = _run_monitor(monkeypatch, capsys, tmp_path)

        assert code == 0
        entry = _queue(tmp_path).skills[SKILL]
        assert entry["eval_executions"] == 1
        assert entry["status"] == "evaluating"
        report = json.loads(out)["hookSpecificOutput"]
        assert report["evaluation"] == {"executions": 1, "target": 10}

    @pytest.mark.unit
    def test_full_window_with_improved_gap_is_promoted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed_history(tmp_path, HEALTHY)
        _start_evaluation(tmp_path, baseline=0.6, target=1)

        _, out = _run_monitor(monkeypatch, capsys, tmp_path)

        assert _queue(tmp_path).skills[SKILL]["status"] == "promoted"
        report = json.loads(out)["hookSpecificOutput"]
        assert report["evaluation_decision"] == "promote"

    @pytest.mark.unit
    def test_full_window_without_improvement_goes_to_review(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed_history(tmp_path, CRITICAL)
        _start_evaluation(tmp_path, baseline=0.2, target=1)

        _, out = _run_monitor(monkeypatch, capsys, tmp_path)

        assert _queue(tmp_path).skills[SKILL]["status"] == "pending_rollback_review"
        report = json.loads(out)["hookSpecificOutput"]
        assert report["evaluation_decision"] == "pending_rollback_review"

    @pytest.mark.unit
    def test_healthy_skill_without_queue_file_creates_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        _seed_history(tmp_path, HEALTHY)

        code, out = _run_monitor(monkeypatch, capsys, tmp_path)

        assert code == 0
        assert json.loads(out)["hookSpecificOutput"]["status"] == "healthy"
        assert not (tmp_path / "skills" / "improvement-queue.json").exists()


_BLOCK_YAML_AND_IMPORT_MONITOR = """
import sys

class _BlockYaml:
    def find_spec(self, name, path=None, target=None):
        if name == "yaml" or name.startswith("yaml."):
            raise ImportError("yaml blocked")

sys.meta_path.insert(0, _BlockYaml())
sys.path.insert(0, sys.argv[1])
import homeostatic_monitor
print(homeostatic_monitor._HAS_QUEUE)
"""


@pytest.mark.unit
def test_monitor_reaches_the_queue_without_pyyaml() -> None:
    """Hooks run under a python3 without PyYAML; the window needs the queue.

    The monitor imports the queue in a try block, so an import chain that
    reaches yaml does not fail loudly: it silently turns off flagging and
    every evaluation window.
    """
    result = subprocess.run(
        [sys.executable, "-c", _BLOCK_YAML_AND_IMPORT_MONITOR, str(_HOOKS_DIR)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True"
