"""Contract tests for the review-core skill.

review-core is a markdown methodology the model reads and follows, so its
behavior is what the file says. Each test pins a rule, step, or command the
skill states, so deleting that sentence from SKILL.md fails the test. The
evidence-format tests also check that the proof-of-work evidence-logging
module agrees with what review-core asks for.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _markdown_contract import load as _load
from _markdown_contract import section as _section

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SKILL = PLUGIN_ROOT / "skills" / "review-core" / "SKILL.md"
EVIDENCE_LOGGING = (
    PLUGIN_ROOT / "skills" / "proof-of-work" / "modules" / "evidence-logging.md"
)


class TestReviewCoreSkill:
    """Feature: Review core provides structured workflow scaffolding.

    As a review workflow initiator
    I want consistent context establishment and scope inventory
    So that all reviews follow the same structured approach
    """

    @pytest.fixture(scope="class")
    def skill(self) -> tuple[dict, str]:
        return _load(SKILL)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_establishment_captures_git_state(self, skill) -> None:
        """Scenario: Context establishment captures git state.

        Given the review-core skill
        When Step 1 is read
        Then it names the commands that capture directory, branch and status
        And requires a concrete comparison target for later diffs.
        """
        _meta, body = skill
        step = _section(body, "Step 1 – Establish Context")
        assert "Confirm `pwd`, repo, branch, and upstream base" in step
        assert "`git status -sb`" in step
        assert "`git rev-parse --abbrev-ref HEAD`" in step
        assert "comparison target (merge base, release tag)" in step

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_scope_inventory_discovers_project_structure(self, skill) -> None:
        """Scenario: Scope inventory finds all relevant artifacts.

        Given the review-core skill
        When Step 2 is read
        Then it lists source, config, docs, specs and generated assets
        And requires recording how they were enumerated.
        """
        _meta, body = skill
        step = _section(body, "Step 2 – Inventory Scope")
        assert "source files, configs, docs, specs, generated assets" in step
        assert "Record how you enumerated them" in step
        assert "`rg --files -g '*.mk'`" in step

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_scope_inventory_identifies_review_targets(self, skill) -> None:
        """Scenario: Scope inventory identifies targets for review.

        Given the review-core skill
        When Steps 1 and 2 are read
        Then the subject under review is summarized
        And constraints inherited from the plan or issue are captured.
        """
        _meta, body = skill
        context = _section(body, "Step 1 – Establish Context")
        scope = _section(body, "Step 2 – Inventory Scope")
        assert "Summarize the feature/bug/initiative under review" in context
        assert "constraints inherited from the plan/issue" in scope

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_capture_initializes_log(self, skill) -> None:
        """Scenario: Evidence capture initializes structured log.

        Given the review-core skill and the evidence-logging module
        When the progress items and evidence step are read
        Then evidence capture is the third required item with its own step
        And the module defines how the log is initialized.
        """
        _meta, body = skill
        items = _section(body, "Required Progress Items")
        assert "3. `review-core:evidence-captured`" in items
        assert "## Step 3 – Capture Evidence (`review-core:evidence-captured`)" in (
            body
        )
        init = _section(EVIDENCE_LOGGING.read_text(), "Step 1: Initialize Log")
        assert "Session ID or review identifier" in init
        assert "Repository, branch, and commit hash" in init

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_capture_logs_commands(self, skill) -> None:
        """Scenario: Evidence capture logs all commands.

        Given the review-core skill and the evidence-logging module
        When the evidence steps are read
        Then every informing command and output is logged
        And entries use the `[E1]` reference convention.
        """
        _meta, body = skill
        step = _section(body, "Step 3 – Capture Evidence")
        assert "Log every command/output that informs the review" in step
        assert "Keep snippets or line numbers for later reference" in step
        module = EVIDENCE_LOGGING.read_text()
        assert "(e.g., `[E1]`, `[E2]`)" in module
        assert "[E1] Command: git diff --stat HEAD~5..HEAD" in module

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_contingency_planning_missing_tools(self, skill) -> None:
        """Scenario: Contingency planning handles missing tools.

        Given the review-core skill
        When Step 6 is read
        Then an unavailable tool requires documented alternative steps
        And the limitations they introduce.
        """
        _meta, body = skill
        step = _section(body, "Step 6 – Contingency Plan")
        assert "If a required tool or skill is unavailable" in step
        assert "document the alternative steps that will be taken" in step
        assert "any limitations this introduces" in step
        assert "6. `review-core:contingencies-documented`" in _section(
            body, "Required Progress Items"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_review_core_error_handling(self, skill) -> None:
        """Scenario: Review core handles errors gracefully.

        Given the review-core skill
        When the verification step is read
        Then a failed citation is dropped or labeled UNVERIFIED
        And an unavailable verifier falls back to a manual re-read
            that is noted in the contingency section.
        """
        _meta, body = skill
        step = _section(body, "Step 5 – Verify Findings Are Grounded")
        assert "Drop or label `UNVERIFIED` any finding the verifier failed" in step
        assert "If the script is unavailable, fall back to re-reading" in step
        assert "manual fallback in the contingency section" in step
        assert "exit `1` lists each finding" in step
