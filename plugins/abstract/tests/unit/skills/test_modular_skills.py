"""Tests for modular-skills skill and modular architecture patterns.

This module tests the modular skill design framework including progressive
disclosure, token optimization, and module structure validation.

Following TDD/BDD principles to ensure modularity standards are met.
"""

from pathlib import Path

import pytest


class TestModularSkillsFramework:
    """Feature: Modular-skills provides token-efficient architecture patterns.

    As a skill architect
    I want automated modularity validation
    So that skills remain maintainable and efficient
    """

    @pytest.fixture
    def modular_skills_path(self) -> Path:
        """Path to the modular-skills skill."""
        return Path(__file__).parents[3] / "skills" / "modular-skills" / "SKILL.md"

    @pytest.fixture
    def modular_skills_content(self, modular_skills_path: Path) -> str:
        """Load the modular-skills skill content."""
        return modular_skills_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_has_toc(self, modular_skills_content: str) -> None:
        """Scenario: Modular-skills includes Table of Contents.

        Given the modular-skills skill
        When reading the skill content
        Then it should have a TOC for navigation
        """
        # Assert - TOC exists
        assert (
            "## Table of Contents" in modular_skills_content
            or "table of contents" in modular_skills_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_defines_line_limits(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills defines recommended line limits.

        Given the modular-skills framework
        When reviewing structure guidelines
        Then it should specify maximum line counts for skills
        """
        # Assert - line limits defined
        assert "150" in modular_skills_content or "100" in modular_skills_content
        assert "lines" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_includes_quick_start_commands(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills Quick Start has actual commands.

        Given the modular-skills framework
        When reviewing the Quick Start section
        Then it should include actual commands, not abstract descriptions
        """
        # Assert - concrete commands exist
        assert "```" in modular_skills_content  # Code blocks exist
        # Check for actual commands
        assert (
            "python" in modular_skills_content.lower()
            or "bash" in modular_skills_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_defines_progressive_disclosure(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills defines progressive disclosure patterns.

        Given the modular-skills framework
        When reviewing architecture principles
        Then it should emphasize progressive disclosure
        """
        # Assert - progressive disclosure defined
        assert (
            "progressive" in modular_skills_content.lower()
            or "disclosure" in modular_skills_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_includes_token_optimization(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills includes token optimization guidance.

        Given the modular-skills framework
        When reviewing optimization techniques
        Then it should mention token efficiency
        """
        # Assert - token optimization exists
        assert "token" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_defines_toc_requirements(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills defines TOC requirements for long modules.

        Given the modular-skills framework
        When reviewing quality standards
        Then it should require TOCs for modules >100 lines
        """
        # Assert - TOC requirements exist
        assert (
            "toc" in modular_skills_content.lower()
            or "table of contents" in modular_skills_content.lower()
        )
        assert "100" in modular_skills_content  # Threshold

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_includes_quality_checks(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills includes quality standards section.

        Given the modular-skills framework
        When reviewing validation criteria
        Then it should include quality checks or standards
        """
        # Assert - quality checks exist
        assert (
            "quality" in modular_skills_content.lower()
            or "standards" in modular_skills_content.lower()
            or "compliance" in modular_skills_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_references_analysis_tools(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills references analysis tools.

        Given the modular-skills framework
        When reviewing available tools
        Then it should mention skill-analyzer and token-estimator
        """
        # Assert - analysis tools referenced
        assert (
            "analyzer" in modular_skills_content.lower()
            or "estimator" in modular_skills_content.lower()
        )


class TestModularArchitecturePatterns:
    """Feature: Skills follow modular architecture best practices.

    As a skill developer
    I want validation of modular patterns
    So that skills are maintainable and efficient
    """

    @pytest.fixture
    def modular_skills_path(self) -> Path:
        """Path to the modular-skills skill."""
        return Path(__file__).parents[3] / "skills" / "modular-skills" / "SKILL.md"

    @pytest.fixture
    def modular_skills_content(self, modular_skills_path: Path) -> str:
        """Load the modular-skills skill content."""
        return modular_skills_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_enforces_single_responsibility(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Framework enforces single responsibility per module.

        Given the modular-skills framework
        When reviewing design principles
        Then it should emphasize single responsibility
        """
        # Assert - single responsibility documented
        assert "single responsibility" in modular_skills_content.lower()
        assert "one task" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_prevents_monolithic_files(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Framework prevents monolithic skill files.

        Given the modular-skills framework
        When reviewing structure guidelines
        Then it should encourage splitting large files
        """
        # Assert - anti-monolithic guidance exists
        assert "monolithic" in modular_skills_content.lower()
        assert "150" in modular_skills_content  # Line limit threshold

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_defines_shallow_dependencies(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Framework defines shallow dependency patterns.

        Given the modular-skills framework
        When reviewing dependency guidelines
        Then it should encourage shallow, clear dependencies
        """
        # Assert - dependency guidance exists
        assert "dependenc" in modular_skills_content.lower()
        assert (
            "shallow" in modular_skills_content.lower()
            or "loose coupling" in modular_skills_content.lower()
        )


class TestProgressiveDisclosureEnforcement:
    """Feature: Skills use progressive disclosure for token efficiency.

    As a skill user
    I want essential information first
    So that I can understand quickly without loading everything
    """

    @pytest.fixture
    def modular_skills_path(self) -> Path:
        """Path to the modular-skills skill."""
        return Path(__file__).parents[3] / "skills" / "modular-skills" / "SKILL.md"

    @pytest.fixture
    def modular_skills_content(self, modular_skills_path: Path) -> str:
        """Load the modular-skills skill content."""
        return modular_skills_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_disclosure_starts_with_essentials(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Progressive disclosure starts with essential content.

        Given a modular skill structure
        When reviewing content organization
        Then essentials should come before deep details
        """
        # Assert - progressive disclosure documented
        assert "progressive disclosure" in modular_skills_content.lower()
        assert "essential" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_disclosure_uses_modules(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Progressive disclosure uses modules for deep details.

        Given a modular skill structure
        When reviewing content organization
        Then deep details should be in separate modules
        """
        # Assert - module references exist for deep details
        assert "modules/" in modular_skills_content
        assert "@include" in modular_skills_content or "Load:" in modular_skills_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_disclosure_prevents_context_bloat(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Progressive disclosure prevents context window bloat.

        Given a modular skill structure
        When reviewing token usage
        Then modules should only load when needed
        """
        # Assert - context/token efficiency documented
        assert "token" in modular_skills_content.lower()
        assert "context" in modular_skills_content.lower()


class TestModularSkillsDocumentationQuality:
    """Feature: Modular-skills documentation meets quality standards.

    As a skill architect
    I want clear, verified modular design guidance
    So that I can apply patterns correctly
    """

    @pytest.fixture
    def modular_skills_path(self) -> Path:
        """Path to the modular-skills skill."""
        return Path(__file__).parents[3] / "skills" / "modular-skills" / "SKILL.md"

    @pytest.fixture
    def modular_skills_content(self, modular_skills_path: Path) -> str:
        """Load the modular-skills skill content."""
        return modular_skills_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_docs_include_verification_commands(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Documentation includes verification after examples.

        Given modular-skills code examples
        When reviewing documentation quality
        Then examples should include verification steps
        """
        # Assert - verification commands follow code examples
        assert "```bash" in modular_skills_content
        # Has actual runnable commands
        assert "python" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_docs_avoid_abstract_descriptions(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Documentation avoids abstract Quick Start.

        Given modular-skills Quick Start
        When reviewing content quality
        Then it should have concrete commands, not abstract descriptions
        """
        # Assert - Quick Start has actual commands, not just descriptions
        assert "## Quick Start" in modular_skills_content
        # Contains actual executable commands
        assert "python scripts/" in modular_skills_content
