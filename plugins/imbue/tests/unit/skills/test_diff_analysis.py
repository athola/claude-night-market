"""Contract tests for the diff-analysis skill.

The skill is markdown the harness loads: SKILL.md sets the four steps and
loads three modules for categorization, risk and git commands. Each test
pins a claim from those files, and the agreement between them, so removing
or contradicting the claim fails the test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from _markdown_contract import section_to_same_level as _section

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "diff-analysis"
MODULES = SKILL_DIR / "modules"


def _body(path: Path) -> str:
    return path.read_text().split("---\n", 2)[2]


def _bullets(text: str) -> list[str]:
    """Bold labels of the ``- **Label**:`` bullets in a section."""
    return re.findall(r"^- \*\*(.+?)\*\*:", text, re.MULTILINE)


@pytest.fixture(scope="module")
def skill() -> str:
    return _body(SKILL_DIR / "SKILL.md")


@pytest.fixture(scope="module")
def categorization() -> str:
    return _body(MODULES / "semantic-categorization.md")


@pytest.fixture(scope="module")
def risk() -> str:
    return _body(MODULES / "risk-assessment-framework.md")


@pytest.fixture(scope="module")
def git_patterns() -> str:
    return _body(MODULES / "git-diff-patterns.md")


class TestDiffAnalysisSkill:
    """Feature: Diff analysis categorizes changes by type and impact."""

    @pytest.mark.unit
    def test_change_categorization_by_type(
        self, skill: str, categorization: str
    ) -> None:
        """Scenario: Changes are categorized by type correctly.

        Given the categorization step and its module
        When they are read
        Then changes group as additions, modifications, deletions and renames.
        """
        assert "`diff-analysis:changes-categorized`" in skill
        assert "Load `modules/semantic-categorization.md`" in _section(
            skill, "Step 2: Categorize Changes (`diff-analysis:changes-categorized`)"
        )
        assert _bullets(_section(categorization, "Change Categories")) == [
            "Additions",
            "Modifications",
            "Deletions",
            "Renames/Moves",
        ]

    @pytest.mark.unit
    def test_semantic_categorization_of_changes(self, categorization: str) -> None:
        """Scenario: Changes are categorized semantically.

        Given the semantic categories
        When they are read
        Then they are feature, fix, refactor, test, docs and config.
        """
        assert _bullets(_section(categorization, "Semantic Categories")) == [
            "Features",
            "Fixes",
            "Refactors",
            "Tests",
            "Documentation",
            "Configuration",
        ]

    @pytest.mark.unit
    def test_risk_assessment_by_change_type(self, risk: str) -> None:
        """Scenario: Risk levels are assigned based on change characteristics.

        Given the risk levels and scoring method
        When they are read
        Then docs and tests are Low, schema migrations and security are High,
        and an uncertain assessment is raised rather than lowered.
        """
        levels = _section(risk, "Risk Levels")
        assert "**Low**: Internal refactors, documentation updates" in levels
        assert "security modifications, schema migrations" in levels
        assert "(when in doubt, elevate risk)" in _section(
            risk, "Risk Scoring Methodology"
        )

    @pytest.mark.unit
    def test_diff_summary_generation(self, skill: str, risk: str) -> None:
        """Scenario: Diff summary provides detailed overview.

        Given the summary step and the risk output format
        When they are read
        Then the summary carries theme, counted scope, risk and review focus,
        and each risky change names indicators and mitigation.
        """
        step = _section(
            skill, "Step 4: Prepare Summary (`diff-analysis:summary-prepared`)"
        )
        assert (
            "theme, scope with counts, risk level, review focus, dependencies" in step
        )
        assert _bullets(_section(risk, "Output Format")) == [
            "Change",
            "Risk Level",
            "Indicators",
            "Mitigation",
            "Dependencies",
        ]

    @pytest.mark.unit
    def test_baseline_establishment(self, skill: str, git_patterns: str) -> None:
        """Scenario: Baseline is established for comparison.

        Given the baseline step and the git module
        When they are read
        Then the step defines states, boundary and scale, and the module
        finds the comparison point with merge-base.
        """
        step = _section(
            skill, "Step 1: Establish Baseline (`diff-analysis:baseline-established`)"
        )
        assert "what states are being compared, boundary of analysis" in step
        assert "load `modules/git-diff-patterns.md`" in step
        assert "git merge-base HEAD main" in git_patterns

    @pytest.mark.unit
    def test_diff_patterns_recognition(
        self, git_patterns: str, categorization: str
    ) -> None:
        """Scenario: Common diff patterns are recognized.

        Given both modules isolate change types with --diff-filter
        When they are read
        Then they use the same four filters, A, M, D and R.
        """
        pattern = r"--diff-filter=([AMDR]) <baseline>"
        assert re.findall(pattern, git_patterns) == ["A", "M", "D", "R"]
        assert re.findall(pattern, categorization) == ["A", "M", "D", "R"]

    @pytest.mark.unit
    def test_cross_cutting_change_detection(self, categorization: str) -> None:
        """Scenario: Cross-cutting changes are identified.

        Given the cross-cutting section and the workflow
        When they are read
        Then breaking changes needing coordinated updates are flagged,
        and changes in several categories are cross-referenced.
        """
        cross = _section(categorization, "Cross-Cutting Changes")
        assert "Breaking changes that require coordinated updates" in cross
        assert "Refactors that touch multiple modules" in cross
        assert "**Cross-Reference**: Note changes that appear in multiple" in (
            _section(categorization, "Categorization Workflow")
        )

    @pytest.mark.unit
    def test_diff_statistics_calculation(self, git_patterns: str) -> None:
        """Scenario: Diff statistics are calculated accurately.

        Given the baseline commands
        When they are read
        Then totals come from the --stat summary line and a file count.
        """
        baseline = _section(git_patterns, "Baseline Establishment")
        assert "git diff --stat <baseline>..HEAD | tail -1" in baseline
        assert "git diff --name-only <baseline>..HEAD | wc -l" in baseline

    @pytest.mark.unit
    def test_diff_analysis_error_handling(self, categorization: str) -> None:
        """Scenario: Diff analysis handles errors gracefully.

        Given sem may be missing
        When the categorization module is read
        Then it checks for sem before use and names the git fallback.
        """
        assert "if command -v sem &>/dev/null; then" in categorization
        assert "When sem is unavailable, use git's `--diff-filter`" in categorization

    @pytest.mark.unit
    def test_diff_analysis_always_loads_only_the_categorization_module(
        self, skill: str
    ) -> None:
        """Scenario: Diff analysis loads modules on demand.

        Given the skill loads modules progressively
        When it is read
        Then only categorization always loads, risk and git load on demand,
        and every module it names exists.
        """
        meta = yaml.safe_load((SKILL_DIR / "SKILL.md").read_text().split("---\n")[1])
        assert meta["progressive_loading"] is True
        loading = _section(skill, "Progressive Loading")
        always = _section(loading, "Always Load")
        conditional = _section(loading, "Conditional Loading")
        assert re.findall(r"`modules/(.+?)`", always) == ["semantic-categorization.md"]
        assert re.findall(r"`modules/(.+?)`", conditional) == [
            "risk-assessment-framework.md",
            "git-diff-patterns.md",
        ]
        for name in re.findall(r"`modules/(.+?)`", skill):
            assert (MODULES / name).is_file(), name
