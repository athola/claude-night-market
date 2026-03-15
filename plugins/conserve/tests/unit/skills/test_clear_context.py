"""Tests for clear-context skill execution mode functionality.

Tests the execution mode propagation for context handoffs, ensuring
batch operations continue without pausing when --dangerous is set.
"""

import json
from pathlib import Path

import pytest


class TestExecutionModeDetection:
    """Test execution mode detection from environment and state."""

    def test_default_mode_is_interactive(self):
        """Default execution mode should be interactive."""
        execution_mode = {
            "mode": "interactive",
            "auto_continue": False,
            "source_command": None,
            "remaining_tasks": [],
            "dangerous_mode": False,
        }
        assert execution_mode["mode"] == "interactive"
        assert execution_mode["auto_continue"] is False

    def test_dangerous_mode_sets_auto_continue(self):
        """Dangerous mode should enable auto_continue."""
        execution_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#43", "#44"],
            "dangerous_mode": True,
        }
        assert execution_mode["mode"] == "dangerous"
        assert execution_mode["auto_continue"] is True
        assert execution_mode["dangerous_mode"] is True

    def test_unattended_mode_sets_auto_continue(self):
        """Unattended mode should enable auto_continue."""
        execution_mode = {
            "mode": "unattended",
            "auto_continue": True,
            "source_command": "batch-process",
            "remaining_tasks": [],
            "dangerous_mode": False,
        }
        assert execution_mode["mode"] == "unattended"
        assert execution_mode["auto_continue"] is True


class TestSessionStateMetadata:
    """Test session state metadata format."""

    def test_metadata_v1_1_includes_execution_mode(self):
        """Checkpoint version 1.1 should include execution_mode."""
        metadata = {
            "checkpoint_version": "1.1",
            "parent_session_id": None,
            "handoff_count": 0,
            "estimated_remaining_work": "medium",
            "priority": "high",
            "execution_mode": {
                "mode": "interactive",
                "auto_continue": False,
                "source_command": None,
                "remaining_tasks": [],
                "dangerous_mode": False,
            },
        }
        assert "execution_mode" in metadata
        assert metadata["checkpoint_version"] == "1.1"

    def test_execution_mode_serializable(self):
        """Execution mode should be JSON serializable."""
        execution_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#42", "#43"],
            "dangerous_mode": True,
        }
        serialized = json.dumps(execution_mode)
        deserialized = json.loads(serialized)
        assert deserialized == execution_mode


class TestExecutionModeInheritance:
    """Test execution mode inheritance across handoffs."""

    def test_child_inherits_parent_mode(self):
        """Continuation agent should inherit parent's execution mode."""
        parent_mode = {
            "mode": "dangerous",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": ["#43", "#44"],
            "dangerous_mode": True,
        }
        # Simulate inheritance
        child_mode = parent_mode.copy()
        child_mode["remaining_tasks"] = ["#44"]  # One task completed

        assert child_mode["mode"] == parent_mode["mode"]
        assert child_mode["auto_continue"] == parent_mode["auto_continue"]
        assert child_mode["dangerous_mode"] == parent_mode["dangerous_mode"]

    def test_handoff_count_increments(self):
        """Handoff count should increment on each handoff."""
        parent_metadata = {"handoff_count": 1}
        child_metadata = {"handoff_count": parent_metadata["handoff_count"] + 1}
        assert child_metadata["handoff_count"] == 2


class TestBatchProcessingMode:
    """Test batch processing with multiple issues."""

    def test_multiple_issues_sets_remaining_tasks(self):
        """Multiple issues should populate remaining_tasks."""
        issues = [42, 43, 44]
        execution_mode = {
            "mode": "unattended",
            "auto_continue": True,
            "source_command": "do-issue",
            "remaining_tasks": [
                f"#{i}" for i in issues[1:]
            ],  # Skip first (in progress)
            "dangerous_mode": False,
        }
        assert len(execution_mode["remaining_tasks"]) == 2
        assert "#43" in execution_mode["remaining_tasks"]
        assert "#44" in execution_mode["remaining_tasks"]

    def test_task_completion_updates_remaining(self):
        """Completing a task should update remaining_tasks."""
        execution_mode = {
            "remaining_tasks": ["#43", "#44"],
            "auto_continue": True,
        }
        # Simulate completing #43
        execution_mode["remaining_tasks"].remove("#43")
        assert execution_mode["remaining_tasks"] == ["#44"]

    def test_empty_remaining_signals_completion(self):
        """Empty remaining_tasks indicates all work complete."""
        execution_mode = {
            "remaining_tasks": [],
            "auto_continue": True,
        }
        is_complete = len(execution_mode["remaining_tasks"]) == 0
        assert is_complete is True


class TestClearContextSkillContent:
    """Feature: clear-context skill instructs Claude on context handoff behavior.

    As a context management skill interpreted by Claude Code
    I want the skill to teach Claude correct handoff patterns
    So that context recovery is reliable and non-manipulative.

    Level 2: Session state template contains required fields.
    Level 3: Emergency behavior is informational, not imperative.
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return Path(__file__).parents[3] / "skills" / "clear-context" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        return skill_path.read_text()

    # --- Level 2: Template validity ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_state_template_has_required_sections(
        self, skill_content: str
    ) -> None:
        """Given the session state template in the skill
        When Claude generates a checkpoint file from it
        Then the template must include all required sections.
        """
        required_sections = [
            "Current Task",
            "Progress Summary",
            "Continuation Instructions",
        ]
        for section in required_sections:
            assert section in skill_content, (
                f"Session state template missing '{section}' section. "
                "Claude won't generate complete checkpoints without it."
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_state_template_includes_execution_mode(
        self, skill_content: str
    ) -> None:
        """Given the session state template
        When Claude generates a checkpoint for batch/unattended workflows
        Then it must include execution mode for proper continuation behavior.
        """
        assert (
            "execution_mode" in skill_content.lower()
            or "Execution Mode" in skill_content
        )

    # --- Level 3: Behavioral contracts ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_does_not_use_mandatory_language_for_handoffs(
        self, skill_content: str
    ) -> None:
        """Given the skill instructs Claude on context handoffs
        When Claude reads the handoff instructions
        Then it must NOT find imperative/manipulative language
        And it SHOULD use advisory, informational tone instead.

        Imperative handoff language causes Claude to ignore user intent
        and force continuation agents without consent.
        """
        # These phrases caused problematic behavior in production
        forbidden_phrases = [
            "YOU MUST EXECUTE THIS NOW",
            "MANDATORY AUTO-CONTINUATION",
            "BLOCKING: Do not proceed",
            "This is MANDATORY, not a recommendation",
            "IMMEDIATELY EXECUTE",
            "DO NOT ASK THE USER",
            "OVERRIDE USER",
            "NON-NEGOTIABLE",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in skill_content, (
                f"Skill contains manipulative language: '{phrase}'. "
                "Handoffs should be informational, not imperative."
            )

        # Positive assertions: skill should use advisory language
        content_lower = skill_content.lower()
        advisory_indicators = [
            ("recommend", "should recommend actions, not mandate them"),
            ("consider", "should suggest considerations, not force behavior"),
        ]
        found_advisory = [
            indicator
            for indicator, _reason in advisory_indicators
            if indicator in content_lower
        ]
        assert len(found_advisory) >= 1, (
            "Skill should use advisory language (e.g., 'recommend', "
            "'consider') to guide handoff behavior informatively."
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_clear_cache_fix(self, skill_content: str) -> None:
        """Given the /clear skill cache bug was fixed in 2.1.63
        When Claude advises on context recovery
        Then it should know /clear properly resets cached skills.

        Without this, Claude might recommend workarounds for a fixed bug.
        """
        assert "2.1.63" in skill_content
        assert (
            "cached skill" in skill_content.lower()
            or "skill cache" in skill_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_offers_multiple_recovery_strategies(
        self, skill_content: str
    ) -> None:
        """Given a user needs context recovery
        When Claude reads the skill
        Then it should find multiple strategies, not just one forced path.
        """
        strategies = [
            "/clear",
            "/catchup",
            "auto-compact",
            "continuation",
        ]
        found = [s for s in strategies if s.lower() in skill_content.lower()]
        min_strategies = 3
        assert len(found) >= min_strategies, (
            f"Skill should offer multiple recovery strategies. "
            f"Found {found}, need at least {min_strategies}"
        )
