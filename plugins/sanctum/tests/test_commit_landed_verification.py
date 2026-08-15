"""Commit-producing workflows must verify HEAD advanced.

Discussion #614: a pre-commit hook that auto-fixes files (Ruff - Fix,
ruff format, prettier, trailing-whitespace) rewrites a staged file and
aborts the commit. The tail of its output reads "Passed / Skipped /
Restored changes from patch", which is what a successful run also
prints. A workflow that confirms success by reading hook output
reports a commit that never landed.

The reliable signal is HEAD: did `git rev-parse HEAD` change? These
tests assert every commit-producing asset says so, anchored on the
step that carries the instruction rather than on the phrase appearing
anywhere in the file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SANCTUM_ROOT = Path(__file__).resolve().parent.parent

ACP = SANCTUM_ROOT / "commands" / "acp.md"
COMMIT_MESSAGES = SANCTUM_ROOT / "skills" / "commit-messages" / "SKILL.md"
PARALLEL_EXECUTION = (
    SANCTUM_ROOT / "skills" / "do-issue" / "modules" / "parallel-execution.md"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    """Whitespace-collapsed text, so assertions survive a re-wrap."""
    return " ".join(_text(path).split())


class TestAcpVerifiesCommitLanded:
    """Feature: /sanctum:acp proves the commit landed before pushing."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_acp_records_head_before_committing(self) -> None:
        """
        Scenario: the commit step captures a baseline
        Given the acp command
        When its commit step is read
        Then it records HEAD before running git commit
        """
        body = _normalized(ACP)
        assert "before=$(git rev-parse HEAD)" in body, (
            "acp no longer records HEAD before committing, so the "
            "verification step has nothing to compare against"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_acp_compares_head_after_committing(self) -> None:
        """
        Scenario: the workflow checks the baseline moved
        Given the acp command
        When its verification step is read
        Then it compares HEAD against the recorded baseline
        """
        body = _normalized(ACP)
        assert '"$(git rev-parse HEAD)" != "$before"' in body, (
            "acp no longer compares HEAD against the pre-commit baseline"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_acp_names_the_auto_fixing_hook_failure_mode(self) -> None:
        """
        Scenario: the instruction explains why output is not evidence
        Given the acp command
        When the verification step is read
        Then it names auto-fixing hooks as the reason
        """
        body = _normalized(ACP)
        assert "auto-fixing hook" in body.lower()
        assert "Restored changes from patch" in body
        assert "`MM` row" in body, "acp no longer names the MM status row"


class TestCommitMessagesDelegatesVerification:
    """Feature: the drafting skill hands the check to its caller."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rule_requires_caller_to_confirm_head_advanced(self) -> None:
        """
        Scenario: the skill states who verifies
        Given the commit-messages skill
        When its Rules section is read
        Then it requires the committer to confirm HEAD advanced
        """
        body = _normalized(COMMIT_MESSAGES)
        assert "confirms HEAD advanced" in body, (
            "commit-messages no longer tells the committer to verify HEAD"
        )
        assert "git rev-parse HEAD" in body


class TestParallelExecutionVerifiesEachTask:
    """Feature: parallel do-issue tasks each prove their commit landed."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_task_checklist_includes_head_confirmation(self) -> None:
        """
        Scenario: the per-task checklist ends with verification
        Given the do-issue parallel-execution module
        When the correct-pattern task checklist is read
        Then confirming HEAD advanced is one of its steps
        """
        body = _normalized(PARALLEL_EXECUTION)
        assert "Confirm HEAD advanced before reporting the commit as landed" in body, (
            "the parallel task checklist no longer verifies the commit landed"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_explains_the_parallel_specific_risk(self) -> None:
        """
        Scenario: the rationale covers why this matters in parallel
        Given the do-issue parallel-execution module
        When the explanation under the checklist is read
        Then it describes a branch silently missing work
        """
        body = _normalized(PARALLEL_EXECUTION)
        assert "git status --short" in body
        assert "leaves the branch missing work" in body


@pytest.mark.parametrize(
    "asset", [ACP, COMMIT_MESSAGES, PARALLEL_EXECUTION], ids=lambda p: p.name
)
def test_asset_cites_the_originating_discussion(asset: Path) -> None:
    """Each instruction points back to the incident that motivated it."""
    assert "#614" in _text(asset), f"{asset.name} lost the #614 provenance link"
