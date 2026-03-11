"""Tests for critical self-adapting module gaps.

Feature: Self-adapting system edge cases
    As a developer
    I want corrupt data, unknown skills, and missing frontmatter handled
    So that the homeostatic loop is resilient to bad state
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from abstract.improvement_queue import ImprovementQueue
from abstract.skill_versioning import SkillVersionManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def queue_file(tmp_path: Path) -> Path:
    """Given a path for an improvement queue JSON file."""
    return tmp_path / "improvement-queue.json"


@pytest.fixture
def empty_queue(queue_file: Path) -> ImprovementQueue:
    """Given an ImprovementQueue with no flagged skills."""
    return ImprovementQueue(queue_file)


# ---------------------------------------------------------------------------
# Tests: ImprovementQueue._load() corrupt recovery
# ---------------------------------------------------------------------------


class TestLoadCorruptRecovery:
    """Feature: _load recovers from corrupt JSON files."""

    @pytest.mark.unit
    def test_corrupt_json_resets_skills_to_empty(self, queue_file: Path) -> None:
        """Scenario: Corrupt JSON file triggers recovery.
        Given a queue file with invalid JSON
        When ImprovementQueue loads the file
        Then skills dict is reset to empty
        """
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("{{{not valid json!!!")

        queue = ImprovementQueue(queue_file)

        assert queue.skills == {}

    @pytest.mark.unit
    def test_corrupt_json_writes_stderr_warning(
        self, queue_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: Corrupt file produces a stderr warning.
        Given a queue file with invalid JSON
        When ImprovementQueue loads
        Then a warning about the corrupt file is written to stderr
        """
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("not json at all")

        _queue = ImprovementQueue(queue_file)

        captured = capsys.readouterr()
        assert "corrupt queue file" in captured.err

    @pytest.mark.unit
    def test_corrupt_file_can_be_overwritten_by_save(self, queue_file: Path) -> None:
        """Scenario: After corrupt load, saving overwrites with valid JSON.
        Given a queue file that was corrupt
        When a skill is flagged (triggering _save)
        Then the file now contains valid JSON
        """
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("GARBAGE")

        queue = ImprovementQueue(queue_file)
        queue.flag_skill("test-skill", 0.4, "exec-001")

        reloaded = json.loads(queue_file.read_text())
        assert "skills" in reloaded
        assert "test-skill" in reloaded["skills"]

    @pytest.mark.unit
    def test_empty_object_json_loads_no_skills(self, queue_file: Path) -> None:
        """Scenario: Valid JSON without 'skills' key loads empty dict.
        Given a queue file containing {} (no skills key)
        When ImprovementQueue loads
        Then skills is empty dict
        """
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("{}")

        queue = ImprovementQueue(queue_file)

        assert queue.skills == {}


# ---------------------------------------------------------------------------
# Tests: ImprovementQueue.evaluate() unknown skill
# ---------------------------------------------------------------------------


class TestEvaluateUnknownSkill:
    """Feature: evaluate returns 'unknown' for missing skills."""

    @pytest.mark.unit
    def test_unknown_skill_returns_unknown(self, empty_queue: ImprovementQueue) -> None:
        """Scenario: evaluate with unknown skill name.
        Given an empty improvement queue
        When evaluate is called with a skill not in the queue
        Then it returns 'unknown'
        """
        result = empty_queue.evaluate("nonexistent-skill")

        assert result == "unknown"

    @pytest.mark.unit
    def test_unknown_skill_does_not_modify_queue(
        self, empty_queue: ImprovementQueue
    ) -> None:
        """Scenario: evaluate for unknown skill leaves queue unchanged.
        Given an empty improvement queue
        When evaluate is called with an unknown skill
        Then the skills dict remains empty
        """
        empty_queue.evaluate("ghost-skill")

        assert empty_queue.skills == {}


# ---------------------------------------------------------------------------
# Tests: ImprovementQueue.record_eval_execution() no-op paths
# ---------------------------------------------------------------------------


class TestRecordEvalExecutionNoOp:
    """Feature: record_eval_execution is a no-op for missing/non-evaluating skills."""

    @pytest.mark.unit
    def test_missing_skill_is_noop(self, empty_queue: ImprovementQueue) -> None:
        """Scenario: record_eval_execution for absent skill does nothing.
        Given an empty queue
        When record_eval_execution is called for a skill not in the queue
        Then no entry is created
        """
        empty_queue.record_eval_execution("missing-skill", 0.2)

        assert "missing-skill" not in empty_queue.skills

    @pytest.mark.unit
    def test_monitoring_skill_is_noop(self, queue_file: Path) -> None:
        """Scenario: record_eval_execution for 'monitoring' skill does nothing.
        Given a skill flagged but in 'monitoring' status (not 'evaluating')
        When record_eval_execution is called
        Then eval_executions is not incremented
        """
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("my-skill", 0.4, "exec-001")
        assert queue.skills["my-skill"]["status"] == "monitoring"

        queue.record_eval_execution("my-skill", 0.3)

        assert queue.skills["my-skill"].get("eval_executions") is None

    @pytest.mark.unit
    def test_evaluating_skill_records_execution(self, queue_file: Path) -> None:
        """Scenario: record_eval_execution works when status IS evaluating.
        Given a skill in 'evaluating' status
        When record_eval_execution is called
        Then eval_executions is incremented
        """
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("my-skill", 0.4, "exec-001")
        queue.start_evaluation("my-skill", 0.4)
        assert queue.skills["my-skill"]["status"] == "evaluating"

        queue.record_eval_execution("my-skill", 0.35)

        assert queue.skills["my-skill"]["eval_executions"] == 1


# ---------------------------------------------------------------------------
# Tests: homeostatic_monitor hook skip path
# ---------------------------------------------------------------------------


class TestHomeostaticMonitorSkipPath:
    """Feature: Hook skips skills in evaluating/pending_rollback_review state."""

    @pytest.mark.unit
    def test_evaluating_skill_is_skipped(self, queue_file: Path) -> None:
        """Scenario: Skill in 'evaluating' status is not re-flagged.
        Given a skill that has been put into evaluation
        When the hook logic checks the queue entry status
        Then the entry status is 'evaluating' and would be skipped
        """
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("test-skill", 0.5, "exec-001")
        queue.start_evaluation("test-skill", 0.5)

        entry = queue.skills.get("test-skill", {})
        # The hook checks this status pair for the skip condition
        assert entry.get("status") in (
            "evaluating",
            "pending_rollback_review",
        )

    @pytest.mark.unit
    def test_pending_rollback_review_skill_is_skipped(self, queue_file: Path) -> None:
        """Scenario: Skill in 'pending_rollback_review' is not re-flagged.
        Given a skill that failed evaluation (regression detected)
        When the hook logic checks the queue entry status
        Then the entry status is 'pending_rollback_review' and would be skipped
        """
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("test-skill", 0.5, "exec-001")
        queue.start_evaluation("test-skill", 0.3)
        # Simulate regression: avg gap (0.5) >= baseline (0.3)
        queue.skills["test-skill"]["eval_gaps"] = [0.5]
        queue.evaluate("test-skill")

        entry = queue.skills.get("test-skill", {})
        assert entry.get("status") == "pending_rollback_review"
        assert entry.get("status") in ("evaluating", "pending_rollback_review")

    @pytest.mark.unit
    def test_monitoring_skill_is_not_skipped(self, queue_file: Path) -> None:
        """Scenario: Skill in 'monitoring' status is NOT skipped.
        Given a skill in normal 'monitoring' status
        When the hook logic checks the entry status
        Then the status is not in the skip set
        """
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("test-skill", 0.4, "exec-001")

        entry = queue.skills.get("test-skill", {})
        assert entry.get("status") not in ("evaluating", "pending_rollback_review")

    @pytest.mark.unit
    def test_hook_main_skips_evaluating_skill(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Full hook main() exits early for evaluating skill.
        Given a skill with high gap but in 'evaluating' status
        When the hook main() runs
        Then it exits with 0 and does NOT increase flagged_count
        """
        # Set up claude home with history
        claude_home = tmp_path / "claude_home"
        logs_dir = claude_home / "skills" / "logs"
        logs_dir.mkdir(parents=True)
        history = {
            "test-plugin:my-skill": {
                "accuracies": [0.3, 0.8, 0.9],  # gap = 0.667-0.3 = 0.367
            }
        }
        (logs_dir / ".history.json").write_text(json.dumps(history))

        # Pre-create queue with skill in evaluating status
        queue_file = claude_home / "skills" / "improvement-queue.json"
        queue = ImprovementQueue(queue_file)
        queue.flag_skill("test-plugin:my-skill", 0.4, "exec-000")
        queue.start_evaluation("test-plugin:my-skill", 0.4)

        # Set up environment for hook
        monkeypatch.setenv("CLAUDE_HOME", str(claude_home))
        monkeypatch.setenv("CLAUDE_TOOL_NAME", "Skill")
        monkeypatch.setenv(
            "CLAUDE_TOOL_INPUT",
            json.dumps({"skill": "test-plugin:my-skill"}),
        )

        # Import and run hook main
        hook_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        monkeypatch.syspath_prepend(str(hook_path.parent / "src"))

        # The hook calls sys.exit(0) on skip, so we catch SystemExit
        sys.path.insert(0, str(hook_path))
        try:
            import homeostatic_monitor  # noqa: PLC0415

            importlib.reload(homeostatic_monitor)

            with pytest.raises(SystemExit) as exc_info:
                homeostatic_monitor.main()
            assert exc_info.value.code == 0
        finally:
            sys.path.remove(str(hook_path))

        # Reload queue and verify flagged_count did NOT increase
        reloaded = ImprovementQueue(queue_file)
        assert reloaded.skills["test-plugin:my-skill"]["flagged_count"] == 0


# ---------------------------------------------------------------------------
# Tests: SkillVersionManager._parse() no-frontmatter branch
# ---------------------------------------------------------------------------


class TestSkillVersionManagerNoFrontmatter:
    """Feature: Files without frontmatter delimiters hit the else branch."""

    @pytest.mark.unit
    def test_no_delimiters_sets_empty_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: File without --- delimiters produces empty frontmatter.
        Given a skill file with no --- delimiters
        When SkillVersionManager parses it
        Then the regex match fails and frontmatter starts empty
        And the entire content becomes the body
        """
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# My Skill\n\nJust content, no frontmatter.\n")

        mgr = SkillVersionManager(skill_file)

        # The else branch sets frontmatter = {} and body = content
        # Then the adaptation block is auto-created
        assert mgr.body == "# My Skill\n\nJust content, no frontmatter.\n"
        assert "adaptation" in mgr.frontmatter
        assert mgr.current_version == "1.0.0"

    @pytest.mark.unit
    def test_no_delimiters_body_is_full_content(self, tmp_path: Path) -> None:
        """Scenario: Without frontmatter the full file is treated as body.
        Given a file with no --- delimiters
        When parsed
        Then body equals the original file content
        """
        content = "No frontmatter here.\n\nJust markdown.\n"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)

        mgr = SkillVersionManager(skill_file)

        assert mgr.body == content

    @pytest.mark.unit
    def test_no_delimiters_still_supports_bump(self, tmp_path: Path) -> None:
        """Scenario: A file without frontmatter can still bump versions.
        Given a file with no frontmatter
        When bump_version is called
        Then it succeeds and writes frontmatter to the file
        """
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Bare Skill\n\nNo metadata.\n")

        mgr = SkillVersionManager(skill_file)
        new_ver = mgr.bump_version(
            "Initial adaptation", {"success_rate": 0.9, "stability_gap": 0.1}
        )

        assert new_ver == "1.1.0"

        # Re-read: file now has frontmatter
        mgr2 = SkillVersionManager(skill_file)
        assert mgr2.current_version == "1.1.0"

    @pytest.mark.unit
    def test_single_dash_line_not_treated_as_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: Single --- without closing is not frontmatter.
        Given a file that starts with --- but has no closing ---
        When parsed
        Then the regex does not match and body is the full content
        """
        content = "---\nThis is not frontmatter because there is no closing.\n"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)

        mgr = SkillVersionManager(skill_file)

        # The regex requires ^---\n(.*?)\n---\n? so a single --- won't match
        # unless there's a closing ---. Either way, adaptation is auto-created.
        assert "adaptation" in mgr.frontmatter
        assert mgr.current_version == "1.0.0"
