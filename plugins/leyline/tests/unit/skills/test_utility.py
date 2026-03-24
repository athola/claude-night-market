"""Tests for the utility skill hub.

This module validates that the utility skill SKILL.md correctly describes
utility-guided action selection for agent orchestration, based on Liu et al.
arXiv:2603.19896.

Following TDD/BDD principles: tests were written before the implementation
to define the expected behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def utility_skill_path() -> Path:
    """Path to the utility skill hub."""
    return Path(__file__).parents[3] / "skills" / "utility" / "SKILL.md"


@pytest.fixture
def utility_skill_content(utility_skill_path: Path) -> str:
    """Load the utility skill content."""
    return utility_skill_path.read_text()


@pytest.fixture
def utility_skill_frontmatter(utility_skill_content: str) -> dict:
    """Parse YAML frontmatter from the utility skill."""
    # Strip the opening '---' fence and extract content up to closing '---'
    lines = utility_skill_content.splitlines()
    if lines[0].strip() != "---":
        return {}
    end = next(i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---")
    return yaml.safe_load("\n".join(lines[1:end]))


class TestUtilitySkillExists:
    """Feature: Utility skill file is present and readable.

    As a leyline infrastructure consumer
    I want a utility skill hub to exist
    So that agents can reference it for action-selection guidance
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, utility_skill_path: Path) -> None:
        """Scenario: SKILL.md exists at the expected path.

        Given the leyline skills directory
        When looking for the utility skill
        Then SKILL.md should be present
        """
        assert utility_skill_path.exists(), (
            f"SKILL.md not found at {utility_skill_path}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_is_non_empty(self, utility_skill_content: str) -> None:
        """Scenario: SKILL.md has substantial content.

        Given the utility skill file
        When reading its content
        Then it should have at least 80 lines
        """
        lines = utility_skill_content.splitlines()
        assert len(lines) >= 80, f"Expected >= 80 lines, got {len(lines)}"


class TestUtilitySkillFrontmatter:
    """Feature: Frontmatter is valid and complete.

    As a leyline plugin loader
    I want well-formed YAML frontmatter
    So that the skill can be indexed and loaded correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_parses(self, utility_skill_frontmatter: dict) -> None:
        """Scenario: Frontmatter is valid YAML.

        Given the utility SKILL.md
        When parsing the YAML frontmatter
        Then it should produce a non-empty dictionary
        """
        assert utility_skill_frontmatter, "Frontmatter is empty or failed to parse"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_name(self, utility_skill_frontmatter: dict) -> None:
        """Scenario: Frontmatter declares name as 'utility'.

        Given the utility skill frontmatter
        When reading the name field
        Then it should equal 'utility'
        """
        assert utility_skill_frontmatter.get("name") == "utility"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_category(self, utility_skill_frontmatter: dict) -> None:
        """Scenario: Frontmatter category is 'infrastructure'.

        Given the utility skill frontmatter
        When reading the category field
        Then it should equal 'infrastructure'
        """
        assert utility_skill_frontmatter.get("category") == "infrastructure"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_modules_listed(self, utility_skill_frontmatter: dict) -> None:
        """Scenario: Frontmatter lists all 7 modules.

        Given the utility skill frontmatter
        When reading the modules field
        Then it should list exactly 7 module paths
        """
        modules = utility_skill_frontmatter.get("modules", [])
        assert len(modules) == 7, f"Expected 7 modules, got {len(modules)}: {modules}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_provides_infrastructure(
        self, utility_skill_frontmatter: dict
    ) -> None:
        """Scenario: Frontmatter provides infrastructure entries.

        Given the utility skill frontmatter
        When reading the provides.infrastructure field
        Then it should include 'utility-scoring'
        """
        provides = utility_skill_frontmatter.get("provides", {})
        infra = provides.get("infrastructure", [])
        assert "utility-scoring" in infra

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_tags_include_orchestration(
        self, utility_skill_frontmatter: dict
    ) -> None:
        """Scenario: Tags include 'orchestration'.

        Given the utility skill frontmatter
        When reading the tags field
        Then it should include 'orchestration'
        """
        tags = utility_skill_frontmatter.get("tags", [])
        assert "orchestration" in tags

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_progressive_loading(
        self, utility_skill_frontmatter: dict
    ) -> None:
        """Scenario: Progressive loading is enabled.

        Given the utility skill frontmatter
        When reading the progressive_loading field
        Then it should be True
        """
        assert utility_skill_frontmatter.get("progressive_loading") is True


class TestUtilitySkillBody:
    """Feature: Skill body covers all required reference-card sections.

    As an agent using the utility skill
    I want complete, accurate content
    So that I can apply utility-guided orchestration correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_overview(self, utility_skill_content: str) -> None:
        """Scenario: Body has an Overview section.

        Given the utility skill
        When reading the body
        Then it should contain an Overview heading
        """
        assert "## Overview" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_references_paper(self, utility_skill_content: str) -> None:
        """Scenario: Body cites the Liu et al. paper.

        Given the utility skill Overview
        When reading the content
        Then it should reference arXiv:2603.19896
        """
        assert "2603.19896" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_when_to_use(self, utility_skill_content: str) -> None:
        """Scenario: Body includes a 'When to Use' section.

        Given the utility skill
        When reading the body
        Then it should list conditions for use
        """
        assert "## When to Use" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_when_not_to_use(self, utility_skill_content: str) -> None:
        """Scenario: Body includes a 'When NOT to Use' section.

        Given the utility skill
        When reading the body
        Then it should list disqualifying conditions
        """
        assert "## When NOT to Use" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_defines_action_space(self, utility_skill_content: str) -> None:
        """Scenario: Body defines the six-action action space.

        Given the utility skill
        When reading the Action Space section
        Then all six actions should be named
        """
        for action in (
            "respond",
            "retrieve",
            "tool_call",
            "verify",
            "delegate",
            "stop",
        ):
            assert action in utility_skill_content, (
                f"Action '{action}' not found in skill content"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_utility_formula(self, utility_skill_content: str) -> None:
        """Scenario: Body contains the utility formula.

        Given the utility skill
        When reading the Utility Function section
        Then the formula components should all appear
        """
        assert "Gain" in utility_skill_content
        assert "StepCost" in utility_skill_content
        assert "Uncertainty" in utility_skill_content
        assert "Redundancy" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_lambda_defaults(self, utility_skill_content: str) -> None:
        """Scenario: Body documents lambda defaults.

        Given the utility skill
        When reading the lambda table
        Then defaults 1.0, 0.5, and 0.8 should all appear
        """
        assert "1.0" in utility_skill_content
        assert "0.5" in utility_skill_content
        assert "0.8" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_utility_range(self, utility_skill_content: str) -> None:
        """Scenario: Body states the utility range.

        Given the utility skill
        When reading the Utility Function section
        Then the range [-2.3, 1.0] should be documented
        """
        assert "-2.3" in utility_skill_content
        assert "1.0" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_termination_conditions(self, utility_skill_content: str) -> None:
        """Scenario: Body defines termination conditions.

        Given the utility skill
        When reading the Termination Conditions section
        Then all three conditions and the override should appear
        """
        lower = utility_skill_content.lower()
        assert "## Termination Conditions".lower() in lower
        assert (
            "step budget" in lower
            or "step_budget" in lower
            or "10" in utility_skill_content
        )
        assert "floor" in lower or "-0.5" in utility_skill_content
        assert "override" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_quick_start(self, utility_skill_content: str) -> None:
        """Scenario: Body contains a Quick Start section.

        Given the utility skill
        When reading the body
        Then it should include a Quick Start section
        """
        assert "## Quick Start" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_detailed_resources(self, utility_skill_content: str) -> None:
        """Scenario: Body links all seven modules.

        Given the utility skill
        When reading the Detailed Resources section
        Then all seven module filenames should appear
        """
        for module in (
            "state-builder",
            "gain",
            "step-cost",
            "uncertainty",
            "redundancy",
            "action-selector",
            "integration",
        ):
            assert module in utility_skill_content, (
                f"Module '{module}' not referenced in Detailed Resources"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_exit_criteria(self, utility_skill_content: str) -> None:
        """Scenario: Body contains an Exit Criteria checklist.

        Given the utility skill
        When reading the body
        Then it should include an Exit Criteria section with checkboxes
        """
        assert "## Exit Criteria" in utility_skill_content
        assert "- [ ]" in utility_skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_no_toc(self, utility_skill_content: str) -> None:
        """Scenario: Body does NOT include a Table of Contents.

        Given the utility skill spec (reference card, not tutorial)
        When reading the body
        Then there should be no Table of Contents section
        """
        assert "## Table of Contents" not in utility_skill_content
        assert "table of contents" not in utility_skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_body_has_no_troubleshooting(self, utility_skill_content: str) -> None:
        """Scenario: Body does NOT include a Troubleshooting section.

        Given the utility skill spec (reference card, not tutorial)
        When reading the body
        Then there should be no Troubleshooting section
        """
        assert "## Troubleshooting" not in utility_skill_content


class TestUtilitySkillFormatting:
    """Feature: Skill body follows project markdown formatting rules.

    As a reviewer reading git diffs
    I want well-wrapped markdown
    So that diffs are readable and focused
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_prose_lines_not_excessively_long(self, utility_skill_content: str) -> None:
        """Scenario: Prose lines respect the 80-character limit.

        Given the utility skill markdown
        When checking line lengths
        Then no prose line should exceed 100 characters
        (tables, code blocks, and URLs are exempt)
        """
        in_code_block = False
        violations: list[tuple[int, int, str]] = []
        for lineno, line in enumerate(utility_skill_content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
            if in_code_block:
                continue
            # Skip tables, headings, and lines that are mostly a URL
            if stripped.startswith("|") or stripped.startswith("#"):
                continue
            if "http" in stripped and len(stripped.split()) <= 3:
                continue
            if len(line) > 100:
                violations.append((lineno, len(line), line))
        assert not violations, "Lines exceeding 100 chars: " + ", ".join(
            f"line {ln} ({length} chars)" for ln, length, _ in violations
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_headings_are_atx_style(self, utility_skill_content: str) -> None:
        """Scenario: All headings use ATX style (# prefix).

        Given the utility skill markdown
        When checking heading syntax
        Then no setext-style underline headings should appear
        """
        lines = utility_skill_content.splitlines()
        # Skip the YAML frontmatter block (between the two '---' fences)
        in_frontmatter = False
        frontmatter_done = False
        body_lines: list[tuple[int, str]] = []
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                in_frontmatter = False
                frontmatter_done = True
                continue
            if frontmatter_done:
                body_lines.append((i + 1, line))

        for lineno, line in body_lines:
            prev_line = lines[lineno - 2].strip() if lineno >= 2 else ""
            assert not (set(line.strip()) <= {"="} and len(line.strip()) >= 3), (
                f"Setext heading (===) found at line {lineno}"
            )
            assert not (
                set(line.strip()) <= {"-"} and len(line.strip()) >= 3 and prev_line
            ), f"Setext heading (---) found at line {lineno}"
