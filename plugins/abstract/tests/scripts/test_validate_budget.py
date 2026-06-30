"""Tests for validate_budget.py — BudgetReport construct/print path.

The PLR0913 refactor packed eight individual scalar parameters into
a single frozen BudgetReport dataclass. These tests exercise the
print_budget_report() function end-to-end so that each field is
asserted to reach the output — not merely that the dataclass
constructs without error.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from validate_budget import (
    OVERHEAD_PER_COMPONENT,
    BudgetReport,
    Component,
    print_budget_report,
)


@pytest.fixture()
def verbose_component() -> Component:
    """A single Component whose description exceeds the 160-char limit."""
    return Component(
        name="fat-skill",
        type="skill",
        plugin="heavy",
        desc_length=220,
        file_path="/heavy/skills/fat-skill/SKILL.md",
    )


class TestPrintBudgetReport:
    """Feature: print_budget_report() unpacks BudgetReport fields into output.

    As a plugin maintainer
    I want budget validation to print an accurate summary
    So that I can identify which component descriptions exceed the limit.
    """

    def test_success_path_shows_headroom(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: Budget well within limit produces passing confirmation.

        Given a BudgetReport where failed=False, warn_only=False, verbose=[]
        When print_budget_report is called
        Then stdout contains the headroom confirmation and "Budget check passed!".
        """
        report = BudgetReport(
            total_chars=10_000,
            total_with_overhead=15_000,
            visible_estimate=50,
            verbose_count=0,
            failed=False,
            warn_only=False,
            verbose=[],
            component_count=5,
        )

        print_budget_report(report)

        out = capsys.readouterr().out
        assert "Budget check passed!" in out
        assert "chars headroom" in out

    def test_failed_path_shows_exceeded_message(
        self, capsys: pytest.CaptureFixture[str], verbose_component: Component
    ) -> None:
        """Scenario: Budget exceeded triggers the error output block.

        Given a BudgetReport where failed=True
        When print_budget_report is called
        Then stdout contains "BUDGET EXCEEDED" and the "Top offenders" header.
        And the verbose component name appears in the offenders list.
        """
        report = BudgetReport(
            total_chars=200_000,
            total_with_overhead=200_000,
            visible_estimate=30,
            verbose_count=1,
            failed=True,
            warn_only=False,
            verbose=[verbose_component],
            component_count=10,
        )

        print_budget_report(report)

        out = capsys.readouterr().out
        assert "BUDGET EXCEEDED" in out
        assert "Top offenders" in out
        assert "heavy/fat-skill" in out

    def test_warn_only_path_shows_approaching_warning(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: Budget approaching limit shows warning block.

        Given a BudgetReport where warn_only=True and failed=False
        When print_budget_report is called
        Then stdout contains the "WARNING: Approaching budget limit" line.
        And the overall result still shows a passing status.
        """
        report = BudgetReport(
            total_chars=82_000,
            total_with_overhead=82_000,
            visible_estimate=100,
            verbose_count=0,
            failed=False,
            warn_only=True,
            verbose=[],
            component_count=20,
        )

        print_budget_report(report)

        out = capsys.readouterr().out
        assert "WARNING: Approaching budget limit" in out
        assert "Budget check passed (with warnings)" in out

    def test_verbose_components_listed_with_char_count(
        self,
        capsys: pytest.CaptureFixture[str],
        verbose_component: Component,
    ) -> None:
        """Scenario: Verbose descriptions appear with their char counts.

        Given a BudgetReport with one verbose Component (desc_length > 160)
        When print_budget_report is called
        Then stdout lists the component using "plugin/name: N chars" format.
        And the char count matches the Component.desc_length value.
        """
        report = BudgetReport(
            total_chars=10_000,
            total_with_overhead=12_000,
            visible_estimate=50,
            verbose_count=1,
            failed=False,
            warn_only=False,
            verbose=[verbose_component],
            component_count=5,
        )

        print_budget_report(report)

        out = capsys.readouterr().out
        assert "descriptions exceed" in out
        assert "heavy/fat-skill" in out
        assert "220 chars" in out

    def test_component_count_drives_overhead_line(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: The Components header reflects component_count from the dataclass.

        Given a BudgetReport with component_count=3
        When print_budget_report is called
        Then stdout shows "Components: 3" with the expected overhead chars.
        And the overhead value matches component_count * OVERHEAD_PER_COMPONENT.
        """
        expected_overhead = 3 * OVERHEAD_PER_COMPONENT
        report = BudgetReport(
            total_chars=5_000,
            total_with_overhead=5_327,
            visible_estimate=15,
            verbose_count=0,
            failed=False,
            warn_only=False,
            verbose=[],
            component_count=3,
        )

        print_budget_report(report)

        out = capsys.readouterr().out
        assert "Components: 3" in out
        assert f"{expected_overhead:,} chars overhead" in out
