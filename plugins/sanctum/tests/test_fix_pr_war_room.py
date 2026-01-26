# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,PLR2004,E501
"""BDD-style tests for War Room checkpoint integration in fix-pr command."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

# ==============================================================================
# War Room Checkpoint Trigger Logic
# ==============================================================================


@dataclass
class ReviewComment:
    """Represents a PR review comment."""

    comment_type: str  # refactor, style, bug, question, breaking
    description: str
    reviewer: str
    severity: str = "medium"


@dataclass
class FixPRTriageResult:
    """Triage results from fix-pr Step 2."""

    comments: list[ReviewComment] = field(default_factory=list)
    scope: str = "medium"  # minor, medium, major
    has_conflicting_feedback: bool = False
    refactor_requests: list[str] = field(default_factory=list)
    requires_breaking_change: bool = False

    @property
    def comment_count(self) -> int:
        return len(self.comments)


def should_trigger_war_room_checkpoint_fix_pr(
    triage: FixPRTriageResult,
) -> tuple[bool, str]:
    """
    Determine if War Room checkpoint should be triggered for fix-pr.

    Uses MODERATE approach:
    - Scope is major (6+ comments), OR
    - Conflicting reviewer feedback, OR
    - Multiple refactoring suggestions (>2), OR
    - Breaking change required

    Returns (should_trigger, reason).
    """
    # Trigger condition 1: Major scope
    if triage.scope == "major" or triage.comment_count >= 6:
        return True, "major_scope"

    # Trigger condition 2: Conflicting feedback
    if triage.has_conflicting_feedback:
        return True, "conflicting_feedback"

    # Trigger condition 3: Multiple refactor requests
    if len(triage.refactor_requests) > 2:
        return True, "multiple_refactors"

    # Trigger condition 4: Breaking change
    if triage.requires_breaking_change:
        return True, "breaking_change"

    return False, "none"


class TestWarRoomCheckpointTriggersFixPR:
    """Tests for War Room checkpoint trigger conditions in fix-pr."""

    def test_triggers_on_major_scope(self) -> None:
        """
        GIVEN major scope (6+ comments)
        WHEN evaluating checkpoint trigger
        THEN returns True with 'major_scope' reason
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("style", "Fix formatting", "reviewer1"),
                ReviewComment("bug", "Handle null case", "reviewer1"),
                ReviewComment("refactor", "Extract method", "reviewer1"),
                ReviewComment("style", "Rename variable", "reviewer2"),
                ReviewComment("bug", "Add validation", "reviewer2"),
                ReviewComment("question", "Why this approach?", "reviewer2"),
            ],
            scope="major",
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is True
        assert reason == "major_scope"

    def test_does_not_trigger_on_minor_scope(self) -> None:
        """
        GIVEN minor scope with clear fixes
        WHEN evaluating checkpoint trigger
        THEN returns False
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("style", "Fix typo", "reviewer1"),
            ],
            scope="minor",
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is False
        assert reason == "none"

    def test_triggers_on_conflicting_feedback(self) -> None:
        """
        GIVEN conflicting reviewer feedback
        WHEN evaluating checkpoint trigger
        THEN returns True with 'conflicting_feedback' reason
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("refactor", "Extract to service", "reviewer1"),
                ReviewComment("refactor", "Keep inline, simpler", "reviewer2"),
            ],
            scope="medium",
            has_conflicting_feedback=True,
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is True
        assert reason == "conflicting_feedback"

    def test_triggers_on_multiple_refactor_requests(self) -> None:
        """
        GIVEN >2 refactor requests
        WHEN evaluating checkpoint trigger
        THEN returns True with 'multiple_refactors' reason
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("refactor", "Extract method A", "reviewer1"),
                ReviewComment("refactor", "Extract method B", "reviewer1"),
                ReviewComment("refactor", "Create new class", "reviewer1"),
            ],
            scope="medium",
            refactor_requests=["Extract A", "Extract B", "New class"],
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is True
        assert reason == "multiple_refactors"

    def test_triggers_on_breaking_change(self) -> None:
        """
        GIVEN reviewer requests breaking change
        WHEN evaluating checkpoint trigger
        THEN returns True with 'breaking_change' reason
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("breaking", "Change API signature", "reviewer1"),
            ],
            scope="medium",
            requires_breaking_change=True,
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is True
        assert reason == "breaking_change"

    def test_medium_scope_without_complexity_does_not_trigger(self) -> None:
        """
        GIVEN medium scope with straightforward fixes
        WHEN evaluating checkpoint trigger
        THEN returns False
        """
        triage = FixPRTriageResult(
            comments=[
                ReviewComment("style", "Fix formatting", "reviewer1"),
                ReviewComment("bug", "Add null check", "reviewer1"),
                ReviewComment("style", "Better naming", "reviewer1"),
            ],
            scope="medium",
            has_conflicting_feedback=False,
            refactor_requests=[],
            requires_breaking_change=False,
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_fix_pr(triage)

        assert should_trigger is False
        assert reason == "none"


class TestFixPRCommandWarRoomIntegration:
    """Tests that fix-pr command documents War Room checkpoint integration."""

    @pytest.fixture
    def actual_fix_pr_content(self) -> str:
        """Load actual fix-pr.md command content."""
        cmd_path = Path(__file__).parents[1] / "commands" / "fix-pr.md"
        return cmd_path.read_text()

    def test_command_has_war_room_checkpoint_section(
        self, actual_fix_pr_content: str
    ) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking for War Room integration
        THEN has a checkpoint section
        """
        assert "War Room Checkpoint" in actual_fix_pr_content

    def test_command_documents_trigger_conditions(
        self, actual_fix_pr_content: str
    ) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking trigger documentation
        THEN documents the moderate trigger conditions
        """
        content_lower = actual_fix_pr_content.lower()
        assert "major" in content_lower
        assert "conflicting" in content_lower
        assert "refactor" in content_lower

    def test_command_documents_after_triage(self, actual_fix_pr_content: str) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking checkpoint timing
        THEN documents checkpoint after Step 2 (Triage)
        """
        assert "Triage" in actual_fix_pr_content
        assert (
            "Step 2" in actual_fix_pr_content
            or "after" in actual_fix_pr_content.lower()
        )

    def test_command_shows_skill_invocation(self, actual_fix_pr_content: str) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking skill invocation
        THEN shows how to invoke war-room-checkpoint skill
        """
        assert "Skill(attune:war-room-checkpoint)" in actual_fix_pr_content

    def test_command_documents_war_room_questions(
        self, actual_fix_pr_content: str
    ) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking War Room guidance
        THEN documents what questions War Room addresses
        """
        content_lower = actual_fix_pr_content.lower()
        assert "reconcile" in content_lower or "conflicting" in content_lower

    def test_command_documents_confidence_threshold(
        self, actual_fix_pr_content: str
    ) -> None:
        """
        GIVEN the actual fix-pr.md command
        WHEN checking auto-continue documentation
        THEN documents confidence threshold
        """
        assert "confidence" in actual_fix_pr_content.lower()
        assert "0.8" in actual_fix_pr_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
