"""Content assertion tests for test-review skill modules.

Tests the content-assertion-quality module using the L1 taxonomy
defined in leyline:testing-quality-standards.
"""

from pathlib import Path

import pytest


class TestContentAssertionQualityModuleContent:
    """Feature: Content assertion quality module adds depth scoring.

    As a test reviewer evaluating plugin test suites
    I want a scoring dimension for content assertion depth
    So that I can identify when execution markdown tests are too shallow.

    Level 1: Structural presence checks.
    """

    @pytest.fixture
    def module_path(self) -> Path:
        return (
            Path(__file__).parents[2]
            / "skills"
            / "test-review"
            / "modules"
            / "content-assertion-quality.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        return module_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists_with_substance(self, module_path: Path) -> None:
        """Given the content assertion quality module
        Then it must exist with substantial content."""
        assert module_path.exists()
        content = module_path.read_text()
        assert len(content.splitlines()) >= 30, "Module should be substantial"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_scoring_scale(self, module_content: str) -> None:
        """Given the module adds a scoring dimension
        Then it must define a numeric scale."""
        assert "score" in module_content.lower() or "scoring" in module_content.lower()
        # Should have specific score values
        assert any(str(n) in module_content for n in range(1, 6))

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_covers_all_three_levels(self, module_content: str) -> None:
        """Given the module maps to the L1/L2/L3 taxonomy
        Then it must reference all three levels."""
        assert "L1" in module_content
        assert "L2" in module_content
        assert "L3" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_when_to_flag(self, module_content: str) -> None:
        """Given reviewers need actionable guidance
        Then the module must define when to flag gaps."""
        assert "flag" in module_content.lower() or "gap" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_anti_patterns(self, module_content: str) -> None:
        """Given content tests can be done wrong
        Then the module must document anti-patterns."""
        assert (
            "anti-pattern" in module_content.lower()
            or "avoid" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_references_leyline_taxonomy(self, module_content: str) -> None:
        """Given this module implements the leyline taxonomy
        Then it must reference the canonical definition."""
        assert "content-assertion-levels" in module_content


class TestInvariantEncodingContent:
    """Feature: Test review checks invariant-encoding test quality.

    As a test reviewer
    I want the skill to detect when invariant-encoding tests are
    weakened or removed
    So that design decisions are not silently eroded

    This test class itself encodes the invariant that all review
    skills must present the three-option framework. If this test
    breaks, present the 3 options to a human before removing it.
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return Path(__file__).parents[2] / "skills" / "test-review" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_invariant_encoding_concept(self, skill_content: str) -> None:
        """Given the test-review skill
        Then it must define what invariant-encoding tests are."""
        assert "Invariant-Encoding Tests" in skill_content
        assert "load-bearing" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_checks_for_invariant_erosion(self, skill_content: str) -> None:
        """Given the test-review skill
        Then it must check for invariant erosion patterns."""
        assert "invariant erosion" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_lists_red_flag_patterns(self, skill_content: str) -> None:
        """Given the test-review skill
        Then it must list red flag patterns for invariant tests."""
        assert "pytest.mark.skip" in skill_content
        assert "Assertion changed" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_presents_three_options(self, skill_content: str) -> None:
        """Given the test-review skill detects invariant erosion
        Then it must present preserve/layer/revise options."""
        assert "Preserve" in skill_content
        assert "Layer" in skill_content
        assert "Revise" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_flags_invariant_erosion_as_blocking(
        self, skill_content: str
    ) -> None:
        """Given invariant erosion is detected
        Then it must be flagged as BLOCKING."""
        assert "BLOCKING" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_invariant_todowrite_item(self, skill_content: str) -> None:
        """Given the test-review workflow tracks invariant checks
        Then a TodoWrite item for invariant preservation must exist."""
        assert "test-review:invariant-preservation" in skill_content
