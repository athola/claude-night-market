"""Tests for agent-expenditure skill token waste monitoring.

This module tests waste signal detection and Brooks's Law thresholds
for agent dispatch sizing. Following TDD/BDD principles.

Note: agent-expenditure is a markdown-only methodology skill with no Python
source modules. The tests below validate:
  1. Skill file structure (SKILL.md exists, has frontmatter, modules present)
  2. Methodology concepts (ghost agent detection, Brooks's Law thresholds,
     post-dispatch review) using inline logic that mirrors the rules documented
     in the skill markdown files.
Structural and conceptual tests are the appropriate test type for skills that
contain no executable Python code. See GitHub issue #320.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestAgentExpenditureStructure:
    """Feature: Skill file structure is valid and discoverable.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "agent-expenditure"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the agent-expenditure skill directory
        When checking for SKILL.md
        Then the file should exist
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md has valid YAML frontmatter.

        Given the SKILL.md file
        When parsing the file
        Then it should have YAML frontmatter with required fields
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---"), "SKILL.md should start with frontmatter"
        assert content.count("---") >= 2, "SKILL.md should have closing frontmatter"

        # Verify required frontmatter fields
        frontmatter_end = content.index("---", 3)
        frontmatter = content[3:frontmatter_end]
        assert "name:" in frontmatter, "Frontmatter missing 'name' field"
        assert "description:" in frontmatter, "Frontmatter missing 'description' field"
        assert "category:" in frontmatter, "Frontmatter missing 'category' field"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_waste_signals_module_exists(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module is present on disk.

        Given the SKILL.md frontmatter declares modules/waste-signals.md
        When checking the modules directory
        Then the file should exist
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        assert module_path.exists(), f"Module not found: {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_waste_signals_module_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module has valid frontmatter.

        Given the waste-signals.md module file
        When parsing the file
        Then it should have YAML frontmatter with parent_skill
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        content = module_path.read_text()

        assert content.startswith("---"), (
            "waste-signals.md should start with frontmatter"
        )
        frontmatter_end = content.index("---", 3)
        frontmatter = content[3:frontmatter_end]
        assert "parent_skill:" in frontmatter, (
            "waste-signals.md missing 'parent_skill' field"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_all_five_waste_signals(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module documents all 5 signal types.

        Given the waste-signals.md module
        When scanning for waste signal headings
        Then all 5 categories should be present
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        content = module_path.read_text()

        expected_signals = [
            "Ghost Agent",
            "Redundant Reader",
            "Duplicate Worker",
            "Token Hog",
            "Coordination Overhead",
        ]
        for signal in expected_signals:
            assert signal in content, (
                f"Waste signal '{signal}' not documented in waste-signals.md"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_brooks_law_table(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md includes a Brooks's Law threshold table.

        Given the SKILL.md file
        When scanning for the agent count guidance table
        Then all four agent count tiers should be present
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        expected_tiers = ["1-3", "4-5", "6-8", "9+"]
        for tier in expected_tiers:
            assert tier in content, f"Brooks's Law tier '{tier}' not found in SKILL.md"


SKILL_DIR = Path(__file__).parents[3] / "skills" / "agent-expenditure"


def _signal_section(number: int, name: str) -> str:
    text = (SKILL_DIR / "modules" / "waste-signals.md").read_text()
    return text.split(f"## {number}. {name}", 1)[1].split("\n## ", 1)[0]


class TestWasteSignalThresholds:
    """Each waste signal states the number that triggers it."""

    @pytest.mark.unit
    def test_ghost_agent_needs_all_three_criteria(self) -> None:
        """A ghost is costly, thin and unevidenced at once, not any one."""
        section = _signal_section(1, "Ghost Agent")
        assert "(ALL must be true)" in section
        assert "Token expenditure >1.5x median" in section
        assert "Findings count <30% of median" in section
        assert "Findings lack evidence citations" in section

    @pytest.mark.unit
    def test_zero_finding_low_risk_scans_are_not_ghosts(self) -> None:
        """A clean scan of clean code is a valid result, not waste."""
        assert "Zero-finding results from low-risk scans" in _signal_section(
            1, "Ghost Agent"
        )

    @pytest.mark.unit
    def test_duplicate_worker_overlap_threshold_is_50_percent(self) -> None:
        """Overlap past half of another agent's findings is duplication."""
        assert "overlap >50%" in _signal_section(3, "Duplicate Worker")

    @pytest.mark.unit
    def test_token_hog_threshold_is_3x_median(self) -> None:
        """The hog line sits at three times the task-type median."""
        assert "exceeds 3x the median token count" in _signal_section(4, "Token Hog")

    @pytest.mark.unit
    def test_coordination_overhead_needs_more_than_5_agents_and_20_percent(
        self,
    ) -> None:
        """Conflicts count only past five agents and a fifth of runtime."""
        section = _signal_section(5, "Coordination Overhead")
        assert "N > 5 agents" in section
        assert "exceed 20% of total agent" in section


class TestBrooksLawThresholds:
    """The agent-count table pairs each tier with its overhead and guidance."""

    @pytest.mark.unit
    def test_overhead_rises_with_agent_count(self) -> None:
        """Each tier keeps its overhead band and its dispatch guidance."""
        text = (SKILL_DIR / "SKILL.md").read_text()
        rows = {
            cells[0]: cells[1:]
            for line in text.splitlines()
            if line.startswith("| ")
            for cells in [[c.strip() for c in line.strip("|").split("|")]]
        }
        assert rows["1-3"] == ["Negligible", "Dispatch freely"]
        assert rows["4-5"] == ["10-15%", "Acceptable; plan first"]
        assert rows["6-8"] == ["20-30%", "Monitor closely"]
        assert rows["9+"] == ["30%+", "Likely counterproductive"]


class TestPostDispatchReview:
    """The review asks four questions and acts on two "no" answers."""

    @pytest.mark.unit
    def test_checklist_has_four_questions_and_a_reduction_rule(self) -> None:
        """Two or more "no" answers mean fewer agents next time."""
        text = (SKILL_DIR / "SKILL.md").read_text()
        checklist = text.split("## Post-Dispatch Review Checklist", 1)[1].split(
            "\n## ", 1
        )[0]
        questions = [
            ln for ln in checklist.splitlines() if ln[:2] in ("1.", "2.", "3.", "4.")
        ]
        assert len(questions) == 4
        assert "If 2+ questions answer no, reduce agent count" in checklist
