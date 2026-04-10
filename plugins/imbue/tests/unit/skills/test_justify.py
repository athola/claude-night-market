"""Tests for justify skill structure and anti-additive-bias methodology.

Validates that the justify SKILL.md defines the audit protocol
for detecting AI additive bias, Iron Law compliance checking,
and minimal-intervention analysis.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestJustifySkillStructure:
    """Feature: Justify skill has valid structure and frontmatter.

    As a developer reviewing AI-generated changes
    I want a well-structured justify skill
    So that I can audit changes for additive bias
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the justify skill."""
        return Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Justify skill file exists.

        Given the imbue plugin skills directory
        When looking for justify
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Skill has complete frontmatter.

        Given the justify skill
        When parsing frontmatter
        Then name, description, version, and category should be present
        """
        assert "name: justify" in skill_content
        assert "version:" in skill_content
        assert "category:" in skill_content
        assert "description:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_depends_on_proof_of_work(self, skill_content: str) -> None:
        """Scenario: Skill declares proof-of-work dependency.

        Given the justify skill
        When checking dependencies
        Then proof-of-work should be listed
        """
        assert "proof-of-work" in skill_content


class TestAdditiveBiasDetection:
    """Feature: Justify detects AI additive bias patterns.

    As a developer
    I want the skill to identify additive bias
    So that I avoid unnecessary code additions
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_additive_bias_scoring(self, skill_content: str) -> None:
        """Scenario: Skill defines additive bias scoring.

        Given the justify skill
        When reviewing the audit protocol
        Then an additive bias score methodology should exist
        """
        assert "Additive Bias Score" in skill_content
        assert "Line ratio" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_anti_patterns(self, skill_content: str) -> None:
        """Scenario: Skill documents anti-patterns to flag.

        Given the justify skill
        When reviewing anti-patterns
        Then test mutation and premature abstraction should be listed
        """
        assert "Test Mutation" in skill_content
        assert "Premature Abstraction" in skill_content
        assert "Shotgun Addition" in skill_content


class TestIronLawCompliance:
    """Feature: Justify enforces Iron Law compliance.

    As a developer following TDD/BDD
    I want the skill to detect test-logic tampering
    So that tests drive implementation, not vice versa
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_iron_law_compliance(self, skill_content: str) -> None:
        """Scenario: Skill includes Iron Law compliance check.

        Given the justify skill
        When reviewing the audit protocol
        Then Iron Law compliance checking should be defined
        """
        assert "Iron Law Compliance" in skill_content
        assert "PASS" in skill_content and "VIOLATION" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_test_logic_tampering(self, skill_content: str) -> None:
        """Scenario: Skill identifies test-logic modification patterns.

        Given the justify skill
        When looking for violation patterns
        Then assertion changes and skip additions should be flagged
        """
        assert (
            "Assertion values changed" in skill_content
            or "assertion" in skill_content.lower()
        )
        assert "skip" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_requires_justification_for_test_changes(self, skill_content: str) -> None:
        """Scenario: Test changes require explicit justification.

        Given the justify skill
        When a test file is modified
        Then explicit justification should be required
        """
        assert "requirement" in skill_content.lower()
        assert "justification" in skill_content.lower()


class TestMinimalInterventionAnalysis:
    """Feature: Justify promotes minimal intervention.

    As a developer
    I want the skill to weight simpler approaches
    So that merge risk is minimized
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_minimal_intervention_analysis(self, skill_content: str) -> None:
        """Scenario: Skill defines minimal intervention analysis.

        Given the justify skill
        When reviewing the analysis steps
        Then minimal intervention questions should be present
        """
        assert "Minimal Intervention" in skill_content
        assert "minimal" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weights_fewer_lines_changed(self, skill_content: str) -> None:
        """Scenario: Skill weights fewer lines changed as preferred.

        Given the justify skill decision weights
        When evaluating competing approaches
        Then fewer lines changed should have HIGH weight
        """
        assert "Fewer lines changed" in skill_content
        assert "Decision Weights" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_subtraction_test(self, skill_content: str) -> None:
        """Scenario: Skill includes a subtraction test.

        Given the justify skill
        When reviewing approach evaluation
        Then a subtraction-first preference should be documented
        """
        assert "Subtraction" in skill_content
        assert "removing" in skill_content.lower()
