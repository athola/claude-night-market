"""Contract tests for the mcp-code-execution skill document.

The hub is executed by the model from `skills/mcp-code-execution/
SKILL.md`. These tests read that file and its modules: the progress
items, the step each names, the module roster, and the exit criteria.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "mcp-code-execution"
EXPECTED_ITEMS = [
    "mcp-code-execution:assess-workflow",
    "mcp-code-execution:route-to-modules",
    "mcp-code-execution:coordinate-mecw",
    "mcp-code-execution:synthesize-results",
]


@pytest.fixture(scope="module")
def skill_text() -> str:
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def _section(skill_text: str, heading_prefix: str) -> str:
    body = skill_text.split(heading_prefix, 1)[1]
    return body.split("\n## ", 1)[0]


@pytest.mark.unit
class TestProgressItems:
    """Document contract: progress items."""

    def test_required_progress_items_are_the_four_hub_steps(
        self, skill_text: str
    ) -> None:
        """Scenario: required progress items are the four hub steps."""
        listed = re.findall(
            r"^\d\. `(mcp-code-execution:[\w-]+)`$",
            _section(skill_text, "## Required Progress Items"),
            re.M,
        )
        assert listed == EXPECTED_ITEMS

    def test_each_progress_item_has_a_matching_step_heading(
        self, skill_text: str
    ) -> None:
        """Scenario: each progress item has a matching step heading."""
        headings = re.findall(r"^## Step \d .* \(`([\w:-]+)`\)$", skill_text, re.M)
        assert headings == EXPECTED_ITEMS


@pytest.mark.unit
class TestModuleRoster:
    """Document contract: module roster."""

    def test_every_linked_module_file_exists(self, skill_text: str) -> None:
        """Scenario: every linked module file exists."""
        linked = re.findall(r"See `(modules/[\w-]+\.md)`", skill_text)
        assert linked
        missing = [name for name in linked if not (SKILL_DIR / name).is_file()]
        assert missing == []

    def test_frontmatter_modules_each_have_a_module_file(self, skill_text: str) -> None:
        """Scenario: frontmatter modules each have a module file."""
        frontmatter = skill_text.split("---")[1]
        declared = re.findall(r"^  - (mcp-[\w-]+)$", frontmatter, re.M)
        assert sorted(declared) == ["mcp-patterns", "mcp-subagents", "mcp-validation"]
        missing = [
            name
            for name in declared
            if not (SKILL_DIR / "modules" / f"{name}.md").is_file()
        ]
        assert missing == []

    def test_hub_depends_on_context_optimization_and_token_conservation(
        self, skill_text: str
    ) -> None:
        """Scenario: hub depends on context optimization and token conservation."""
        frontmatter = skill_text.split("---")[1]
        assert "  - context-optimization" in frontmatter
        assert "  - token-conservation" in frontmatter


@pytest.mark.unit
class TestHubBehavior:
    """Document contract: hub behavior."""

    def test_mecw_risk_assessment_is_delegated_to_the_validation_module(
        self, skill_text: str
    ) -> None:
        """Scenario: mecw risk assessment is delegated to the validation module."""
        assert (
            "Delegate to mcp-validation module for detailed risk analysis" in skill_text
        )

    def test_emergency_response_delegates_routes_compresses_and_summarizes(
        self, skill_text: str
    ) -> None:
        """Scenario: emergency response delegates routes compresses and summarizes."""
        emergency = _section(skill_text, "## Emergency Protocols")
        assert "Delegates immediately to mcp-validation" in emergency
        assert "Route to mcp-subagents" in emergency
        assert "Apply compression through mcp-patterns" in emergency
        assert "Return minimal summary to preserve context" in emergency

    def test_success_metrics_set_the_fifty_percent_context_rule(
        self, skill_text: str
    ) -> None:
        """Scenario: success metrics set the fifty percent context rule."""
        metrics = _section(skill_text, "## Success Metrics")
        assert "100% adherence to 50% context rule" in metrics


@pytest.mark.unit
class TestExitCriteria:
    """Document contract: exit criteria."""

    def test_exit_criteria_are_four_unchecked_boxes(self, skill_text: str) -> None:
        """Scenario: exit criteria are four unchecked boxes."""
        criteria = _section(skill_text, "## Exit Criteria")
        assert len(re.findall(r"^- \[ \] ", criteria, re.M)) == 4

    def test_synthesis_returns_the_four_documented_keys(self, skill_text: str) -> None:
        """Scenario: synthesis returns the four documented keys."""
        criteria = " ".join(_section(skill_text, "## Exit Criteria").split())
        assert (
            "`status`, `token_savings`, `mecw_compliance`, `hallucination_risk`"
            in criteria
        )

    def test_savings_threshold_is_eighty_percent(self, skill_text: str) -> None:
        """Scenario: savings threshold is eighty percent."""
        criteria = " ".join(_section(skill_text, "## Exit Criteria").split())
        assert "greater than 80% compared to running the same workflow" in criteria
