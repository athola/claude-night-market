# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,PLR2004,E501
"""BDD-style tests for War Room checkpoint integration in pr-review command."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

# ==============================================================================
# War Room Checkpoint Trigger Logic
# ==============================================================================


@dataclass
class ReviewFinding:
    """Represents a finding from PR review."""

    finding_type: str  # blocking, non-blocking, architecture, scope, adr
    description: str
    severity: str = "medium"  # low, medium, high


@dataclass
class PRReviewAnalysis:
    """Analysis results from PR review phases 1-4."""

    findings: list[ReviewFinding] = field(default_factory=list)
    scope_mode: str = "standard"
    has_architecture_changes: bool = False
    has_adr_violations: bool = False
    changed_files: list[str] = field(default_factory=list)

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.finding_type == "blocking")

    @property
    def out_of_scope_count(self) -> int:
        return sum(1 for f in self.findings if f.finding_type == "scope")


def should_trigger_war_room_checkpoint_pr_review(
    analysis: PRReviewAnalysis,
) -> tuple[bool, str]:
    """
    Determine if War Room checkpoint should be triggered for PR review.

    Uses MODERATE approach:
    - >3 blocking issues, OR
    - Architecture changes detected, OR
    - ADR non-compliance, OR
    - Scope-mode=strict with out-of-scope findings

    Returns (should_trigger, reason).
    """
    # Trigger condition 1: >3 blocking issues
    if analysis.blocking_count > 3:
        return True, "many_blocking_issues"

    # Trigger condition 2: Architecture changes
    if analysis.has_architecture_changes:
        return True, "architecture_changes"

    # Trigger condition 3: ADR violations
    if analysis.has_adr_violations:
        return True, "adr_violations"

    # Trigger condition 4: Strict mode with out-of-scope
    if analysis.scope_mode == "strict" and analysis.out_of_scope_count > 0:
        return True, "strict_scope_violations"

    return False, "none"


class TestWarRoomCheckpointTriggersPRReview:
    """Tests for War Room checkpoint trigger conditions in pr-review."""

    def test_triggers_on_many_blocking_issues(self) -> None:
        """
        GIVEN >3 blocking issues
        WHEN evaluating checkpoint trigger
        THEN returns True with 'many_blocking_issues' reason
        """
        analysis = PRReviewAnalysis(
            findings=[
                ReviewFinding("blocking", "Missing error handling"),
                ReviewFinding("blocking", "No input validation"),
                ReviewFinding("blocking", "Security vulnerability"),
                ReviewFinding("blocking", "Breaking API change"),
            ]
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is True
        assert reason == "many_blocking_issues"

    def test_does_not_trigger_on_few_blocking_issues(self) -> None:
        """
        GIVEN <= 3 blocking issues and no other triggers
        WHEN evaluating checkpoint trigger
        THEN returns False
        """
        analysis = PRReviewAnalysis(
            findings=[
                ReviewFinding("blocking", "Missing test"),
                ReviewFinding("blocking", "Typo in error message"),
                ReviewFinding("non-blocking", "Could use better naming"),
            ]
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is False
        assert reason == "none"

    def test_triggers_on_architecture_changes(self) -> None:
        """
        GIVEN PR with architecture changes
        WHEN evaluating checkpoint trigger
        THEN returns True with 'architecture_changes' reason
        """
        analysis = PRReviewAnalysis(
            findings=[ReviewFinding("blocking", "New service needs ADR")],
            has_architecture_changes=True,
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is True
        assert reason == "architecture_changes"

    def test_triggers_on_adr_violations(self) -> None:
        """
        GIVEN PR violating ADRs
        WHEN evaluating checkpoint trigger
        THEN returns True with 'adr_violations' reason
        """
        analysis = PRReviewAnalysis(
            findings=[ReviewFinding("blocking", "Violates ADR-003")],
            has_adr_violations=True,
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is True
        assert reason == "adr_violations"

    def test_triggers_on_strict_mode_with_scope_issues(self) -> None:
        """
        GIVEN strict scope mode with out-of-scope findings
        WHEN evaluating checkpoint trigger
        THEN returns True with 'strict_scope_violations' reason
        """
        analysis = PRReviewAnalysis(
            findings=[
                ReviewFinding("scope", "Unrelated refactoring"),
                ReviewFinding("blocking", "Missing test"),
            ],
            scope_mode="strict",
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is True
        assert reason == "strict_scope_violations"

    def test_does_not_trigger_standard_mode_with_scope_issues(self) -> None:
        """
        GIVEN standard scope mode with out-of-scope findings
        WHEN evaluating checkpoint trigger
        THEN returns False (only strict mode triggers)
        """
        analysis = PRReviewAnalysis(
            findings=[
                ReviewFinding("scope", "Unrelated refactoring"),
            ],
            scope_mode="standard",
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is False
        assert reason == "none"

    def test_clean_pr_does_not_trigger(self) -> None:
        """
        GIVEN clean PR with no blocking issues
        WHEN evaluating checkpoint trigger
        THEN returns False
        """
        analysis = PRReviewAnalysis(
            findings=[
                ReviewFinding("non-blocking", "Consider better naming"),
            ]
        )
        should_trigger, reason = should_trigger_war_room_checkpoint_pr_review(analysis)

        assert should_trigger is False
        assert reason == "none"


class TestPRReviewCommandWarRoomIntegration:
    """Tests that pr-review command documents War Room checkpoint integration."""

    @pytest.fixture
    def actual_pr_review_content(self) -> str:
        """Load actual pr-review.md command content."""
        cmd_path = Path(__file__).parents[1] / "commands" / "pr-review.md"
        return cmd_path.read_text()

    def test_command_has_war_room_checkpoint_section(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking for War Room integration
        THEN has a checkpoint section
        """
        assert "War Room Checkpoint" in actual_pr_review_content

    def test_command_documents_trigger_conditions(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking trigger documentation
        THEN documents the moderate trigger conditions
        """
        content_lower = actual_pr_review_content.lower()
        assert "blocking" in content_lower
        assert "architecture" in content_lower
        assert "adr" in content_lower

    def test_command_documents_scope_mode_interaction(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking scope mode documentation
        THEN documents strict mode interaction with checkpoint
        """
        assert "strict" in actual_pr_review_content.lower()
        assert "scope" in actual_pr_review_content.lower()

    def test_command_shows_skill_invocation(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking skill invocation
        THEN shows how to invoke war-room-checkpoint skill
        """
        assert "Skill(attune:war-room-checkpoint)" in actual_pr_review_content

    def test_command_documents_war_room_questions(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking War Room guidance
        THEN documents what questions War Room addresses
        """
        content_lower = actual_pr_review_content.lower()
        assert "split" in content_lower or "smaller" in content_lower
        assert "blocking" in content_lower

    def test_command_documents_rs_score_modes(
        self, actual_pr_review_content: str
    ) -> None:
        """
        GIVEN the actual pr-review.md command
        WHEN checking mode documentation
        THEN documents RS score thresholds
        """
        assert "Express" in actual_pr_review_content
        assert "Lightweight" in actual_pr_review_content
        assert "Full Council" in actual_pr_review_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
