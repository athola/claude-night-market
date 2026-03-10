"""Tests for quality gate orchestration logic."""

from __future__ import annotations

from pathlib import Path

from conventions import (
    Convention,
    Finding,
    calculate_verdict,
    conventions_for_step,
    filter_steps,
)

# ── Step routing tests ──────────────────────────────────


class TestConventionsForStep:
    """Feature: Convention filtering by pipeline step

    As the egregore orchestrator
    I want conventions filtered to the current step
    So that only relevant checks run at each stage
    """

    def test_code_review_gets_all_conventions(self) -> None:
        """Scenario: code-review step runs all conventions
        Given the full codex is loaded
        When filtering for the "code-review" step
        Then all conventions C1-C5 are included
        """
        convs = _make_conventions(["C1", "C2", "C3", "C4", "C5"])
        result = conventions_for_step("code-review", convs)
        ids = [c.id for c in result]
        assert set(ids) == {"C1", "C2", "C3", "C4", "C5"}

    def test_unbloat_gets_no_conventions(self) -> None:
        """Scenario: unbloat step has no convention checks
        Given the full codex
        When filtering for "unbloat"
        Then no conventions are returned
        """
        convs = _make_conventions(["C1", "C2", "C3", "C4", "C5"])
        result = conventions_for_step("unbloat", convs)
        assert result == []

    def test_update_docs_gets_c5_only(self) -> None:
        """Scenario: update-docs step checks doc consolidation
        Given the full codex
        When filtering for "update-docs"
        Then only C5 is returned
        """
        convs = _make_conventions(["C1", "C2", "C3", "C4", "C5"])
        result = conventions_for_step("update-docs", convs)
        ids = [c.id for c in result]
        assert ids == ["C5"]

    def test_unknown_step_gets_no_conventions(self) -> None:
        """Scenario: unknown steps get no conventions
        Given the full codex
        When filtering for an unknown step
        Then no conventions are returned
        """
        convs = _make_conventions(["C1", "C2"])
        result = conventions_for_step("unknown-step", convs)
        assert result == []


# ── Verdict calculation tests ───────────────────────────


class TestCalculateVerdict:
    """Feature: Review verdict calculation

    As the egregore orchestrator
    I want clear verdicts from quality checks
    So that pipeline flow is deterministic
    """

    def test_no_findings_is_pass(self) -> None:
        """Scenario: No findings means pass
        Given an empty findings list
        When calculating the verdict
        Then verdict is "pass"
        """
        verdict = calculate_verdict([])
        assert verdict.status == "pass"
        assert verdict.blocking_count == 0
        assert verdict.warning_count == 0

    def test_only_warnings_is_pass_with_warnings(self) -> None:
        """Scenario: Only warnings means pass-with-warnings
        Given findings with only "warning" severity
        When calculating the verdict
        Then verdict is "pass-with-warnings"
        """
        findings = [
            _make_finding("C4", severity="warning"),
            _make_finding("C5", severity="warning"),
        ]
        verdict = calculate_verdict(findings)
        assert verdict.status == "pass-with-warnings"
        assert verdict.warning_count == 2
        assert verdict.blocking_count == 0

    def test_blocking_findings_is_fix_required(self) -> None:
        """Scenario: Blocking findings means fix-required
        Given findings with at least one "blocking" severity
        When calculating the verdict
        Then verdict is "fix-required"
        """
        findings = [
            _make_finding("C1", severity="blocking"),
            _make_finding("C4", severity="warning"),
        ]
        verdict = calculate_verdict(findings)
        assert verdict.status == "fix-required"
        assert verdict.blocking_count == 1
        assert verdict.warning_count == 1

    def test_verdict_summary_message(self) -> None:
        """Scenario: Verdict has human-readable summary
        Given mixed findings
        When calculating the verdict
        Then summary describes the counts
        """
        findings = [
            _make_finding("C1", severity="blocking"),
            _make_finding("C3", severity="blocking"),
            _make_finding("C4", severity="warning"),
        ]
        verdict = calculate_verdict(findings)
        assert "2 blocking" in verdict.summary
        assert "1 warning" in verdict.summary

    def test_verdict_to_dict(self) -> None:
        """Scenario: Verdict serializes to manifest decision
        Given a calculated verdict
        When converting to dict
        Then it has step, chose, and why fields
        """
        verdict = calculate_verdict([])
        d = verdict.to_decision("code-review")
        assert d["step"] == "code-review"
        assert d["chose"] == "pass"
        assert "why" in d


# ── Quality config filtering tests ──────────────────────


class TestFilterSteps:
    """Feature: Per-work-item quality configuration

    As the egregore orchestrator
    I want to skip or select quality steps per work item
    So that the pipeline is configurable
    """

    ALL_STEPS = [
        "code-review",
        "unbloat",
        "code-refinement",
        "update-tests",
        "update-docs",
    ]

    def test_empty_config_runs_all_steps(self) -> None:
        """Scenario: No quality_config means all steps
        Given an empty quality config
        When filtering steps
        Then all 5 steps are returned
        """
        result = filter_steps(self.ALL_STEPS, {})
        assert result == self.ALL_STEPS

    def test_skip_removes_specified_steps(self) -> None:
        """Scenario: skip list removes steps
        Given quality_config with skip: ["unbloat"]
        When filtering steps
        Then unbloat is excluded
        """
        config = {"skip": ["unbloat"]}
        result = filter_steps(self.ALL_STEPS, config)
        assert "unbloat" not in result
        assert len(result) == 4

    def test_only_keeps_specified_steps(self) -> None:
        """Scenario: only list selects steps
        Given quality_config with only: ["code-review"]
        When filtering steps
        Then only code-review runs
        """
        config = {"only": ["code-review", "update-docs"]}
        result = filter_steps(self.ALL_STEPS, config)
        assert result == ["code-review", "update-docs"]

    def test_only_takes_precedence_over_skip(self) -> None:
        """Scenario: only overrides skip
        Given both only and skip in config
        When filtering
        Then only is used, skip is ignored
        """
        config = {
            "only": ["code-review"],
            "skip": ["code-review"],
        }
        result = filter_steps(self.ALL_STEPS, config)
        assert result == ["code-review"]

    def test_preserves_step_order(self) -> None:
        """Scenario: filtered steps maintain pipeline order
        Given quality_config with only in arbitrary order
        When filtering
        Then steps are in pipeline order
        """
        config = {"only": ["update-docs", "code-review"]}
        result = filter_steps(self.ALL_STEPS, config)
        assert result == ["code-review", "update-docs"]


# ── Helpers ─────────────────────────────────────────────


def _make_conventions(ids: list[str]) -> list[Convention]:
    """Create minimal Convention objects for testing."""
    return [
        Convention(
            id=cid,
            name=f"conv-{cid}",
            description="test",
            check_type="grep",
            severity="blocking",
            enabled=True,
        )
        for cid in ids
    ]


def _make_finding(
    convention_id: str,
    severity: str = "blocking",
) -> Finding:
    """Create a minimal Finding for testing."""
    return Finding(
        convention_id=convention_id,
        convention_name=f"conv-{convention_id}",
        file=Path("test.py"),
        line=1,
        message="test finding",
        severity=severity,
    )
