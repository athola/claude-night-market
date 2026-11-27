"""Tests for latent-space-engineering skill instruction framing and style transfer.

This module tests the three core techniques: emotional framing, style gene
transfer, and competitive review patterns. Following TDD/BDD principles.

Note: latent-space-engineering is a markdown-only methodology skill with no
Python source modules. The tests below validate:
  1. Skill file structure (SKILL.md exists, has frontmatter, modules present)
  2. Methodology concepts (emotional framing, style gene transfer, competitive
     review) using inline logic that mirrors the rules documented in the skill
     markdown files.
Structural and conceptual tests are the appropriate test type for skills that
contain no executable Python code. See GitHub issue #320.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestLatentSpaceEngineeringStructure:
    """Feature: Skill file structure is valid and discoverable.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "latent-space-engineering"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the latent-space-engineering skill directory
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
    def test_all_modules_exist(self, skill_dir: Path) -> None:
        """Scenario: All declared modules are present on disk.

        Given the SKILL.md frontmatter declares module dependencies
        When checking the modules directory
        Then each declared module file should exist
        """
        expected_modules = [
            "modules/emotional-framing.md",
            "modules/style-gene-transfer.md",
            "modules/competitive-review.md",
        ]
        for module_path in expected_modules:
            full_path = skill_dir / module_path
            assert full_path.exists(), f"Module not found: {full_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modules_have_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: Each module file has valid frontmatter.

        Given the module markdown files
        When parsing each file
        Then each should have YAML frontmatter with parent_skill
        """
        modules_dir = skill_dir / "modules"
        for md_file in sorted(modules_dir.glob("*.md")):
            content = md_file.read_text()
            assert content.startswith("---"), (
                f"{md_file.name} should start with frontmatter"
            )
            frontmatter_end = content.index("---", 3)
            frontmatter = content[3:frontmatter_end]
            assert "parent_skill:" in frontmatter, (
                f"{md_file.name} missing 'parent_skill' field"
            )


MODULES = Path(__file__).parents[3] / "skills" / "latent-space-engineering" / "modules"


def _module(name: str) -> str:
    return (MODULES / name).read_text()


def _table_rows(text: str, header: str) -> list[list[str]]:
    """Return the body rows of the markdown table under ``header``."""
    section = text.split(header, 1)[1]
    rows = []
    for line in section.splitlines()[1:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not set("".join(cells)) <= set("-: "):
            rows.append(cells)
    return rows[1:]  # drop the header row


class TestEmotionalFraming:
    """The module names the threat patterns to replace and the exception."""

    @pytest.mark.unit
    def test_every_threat_pattern_carries_an_urgency_marker(self) -> None:
        rows = _table_rows(_module("emotional-framing.md"), "## Anti-Patterns")
        markers = ("MUST", "CRITICAL", "WARNING", "NEVER", "LAST CHANCE")
        assert len(rows) == 5
        for pattern, problem in rows:
            assert any(m in pattern for m in markers), pattern
            assert problem

    @pytest.mark.unit
    def test_no_confident_pattern_carries_an_urgency_marker(self) -> None:
        rows = _table_rows(_module("emotional-framing.md"), "## Preferred Patterns")
        assert len(rows) == 5
        for pattern, _why in rows:
            assert not any(m in pattern for m in ("MUST", "NEVER", "CRITICAL")), pattern

    @pytest.mark.unit
    def test_urgency_stays_for_genuine_safety_constraints(self) -> None:
        text = _module("emotional-framing.md")
        exception = text.split("## When Urgency IS Appropriate", 1)[1]
        for constraint in ("Security boundaries", "Data loss prevention"):
            assert constraint in exception


class TestStyleGeneTransfer:
    """The module bounds exemplar size and says when not to transfer."""

    @pytest.mark.unit
    def test_size_table_marks_past_200_lines_as_wasteful(self) -> None:
        rows = _table_rows(_module("style-gene-transfer.md"), "## Size Guidelines")
        by_size = {size: cost for size, _effect, cost in rows}
        assert by_size["200+ lines"] == "Wasteful"
        assert by_size["100-200 lines"] == "High"

    @pytest.mark.unit
    def test_skip_conditions_cover_greenfield_rigid_and_oversized(self) -> None:
        text = _module("style-gene-transfer.md")
        skip = text.split("## When NOT To Use", 1)[1].split("\n## ", 1)[0]
        for condition in ("Greenfield", "exceeds 200 lines", "rigidly specified"):
            assert condition in skip


class TestCompetitiveReview:
    """The module switches framing at three agents and guards the incentive."""

    @pytest.mark.unit
    def test_framing_switches_from_collaborative_to_competitive_at_three(
        self,
    ) -> None:
        text = _module("competitive-review.md")
        assert "## For 3+ Agents (Competitive)" in text
        assert "## For 2 Agents (Collaborative)" in text
        assert "fewer than 3 agents" in text

    @pytest.mark.unit
    def test_competition_is_weighted_by_severity_not_count(self) -> None:
        text = _module("competitive-review.md")
        guard = text.split("## Avoiding Perverse Incentives", 1)[1].split("\n## ", 1)[0]
        assert "Require evidence citations for each finding" in guard
        assert "Weight findings by severity, not count" in guard
