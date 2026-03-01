"""Tests for testing-quality-standards skill and quality metrics.

This module tests the testing quality standards framework including coverage
thresholds, anti-patterns, and quality metrics.

Following TDD/BDD principles to ensure testing standards are validated.
"""

from pathlib import Path

import pytest


class TestTestingQualityStandards:
    """Feature: Testing-quality-standards provides quality metrics.

    As a testing framework designer
    I want validated quality standards
    So that testing practices are consistent and effective
    """

    @pytest.fixture
    def quality_standards_path(self) -> Path:
        """Path to the testing-quality-standards skill."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "SKILL.md"
        )

    @pytest.fixture
    def quality_standards_content(self, quality_standards_path: Path) -> str:
        """Load the testing-quality-standards skill content."""
        return quality_standards_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_defines_coverage_thresholds(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards define coverage thresholds.

        Given the testing-quality-standards skill
        When reviewing coverage criteria
        Then it should define specific coverage percentage thresholds
        """
        # Assert - coverage thresholds defined
        assert "coverage" in quality_standards_content.lower()
        # Should have specific numbers
        assert any(char.isdigit() for char in quality_standards_content)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_defines_quality_metrics(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards define quality metrics categories.

        Given the testing-quality-standards skill
        When reviewing quality assessment
        Then it should categorize quality metrics
        """
        # Assert - quality metrics exist
        assert (
            "metric" in quality_standards_content.lower()
            or "quality" in quality_standards_content.lower()
        )
        # Should have categories
        assert (
            "structure" in quality_standards_content.lower()
            or "coverage" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_references_anti_patterns(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards reference anti-patterns module.

        Given the testing-quality-standards skill
        When reviewing best practices
        Then it should reference anti-patterns documentation
        """
        # Assert - anti-patterns referenced
        assert (
            "anti-pattern" in quality_standards_content.lower()
            or "anti pattern" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_includes_best_practices(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards include best practices.

        Given the testing-quality-standards skill
        When reviewing quality guidance
        Then it should reference best practices documentation
        """
        # Assert - best practices referenced
        assert "best practice" in quality_standards_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_defines_maintainability_criteria(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards define maintainability metrics.

        Given the testing-quality-standards skill
        When reviewing quality categories
        Then it should include maintainability criteria (DRY, fixtures, mocking)
        """
        # Assert - maintainability criteria exist
        assert "maintain" in quality_standards_content.lower()
        assert (
            "dry" in quality_standards_content.lower()
            or "mock" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_defines_reliability_criteria(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards define reliability metrics.

        Given the testing-quality-standards skill
        When reviewing quality categories
        Then it should include reliability criteria (flaky tests, determinism)
        """
        # Assert - reliability criteria exist
        assert (
            "reliability" in quality_standards_content.lower()
            or "flaky" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_includes_verification_steps(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards include verification examples.

        Given the testing-quality-standards skill
        When reviewing code examples
        Then examples should include verification steps
        """
        # Assert - verification steps exist
        assert (
            "verification" in quality_standards_content.lower()
            or "verify" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_defines_integration_points(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards reference plugin integration.

        Given the testing-quality-standards skill
        When reviewing ecosystem integration
        Then it should list which skills reference these standards
        """
        # Assert - integration documented
        assert "integration" in quality_standards_content.lower()
        assert (
            "pensive" in quality_standards_content.lower()
            or "parseltongue" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_standards_includes_troubleshooting(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Testing standards include troubleshooting guidance.

        Given the testing-quality-standards skill
        When reviewing documentation completeness
        Then it should include common issues and solutions
        """
        # Assert - troubleshooting exists
        assert (
            "troubleshoot" in quality_standards_content.lower()
            or "common issue" in quality_standards_content.lower()
        )


class TestCoverageThresholdsValidation:
    """Feature: Coverage thresholds are defined and validated.

    As a quality gate enforcer
    I want specific coverage thresholds
    So that code quality is measurable
    """

    @pytest.fixture
    def quality_standards_path(self) -> Path:
        """Path to the testing-quality-standards skill."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "SKILL.md"
        )

    @pytest.fixture
    def quality_standards_content(self, quality_standards_path: Path) -> str:
        """Load the testing-quality-standards skill content."""
        return quality_standards_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_coverage_thresholds_are_specific(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Coverage thresholds use specific percentages.

        Given the testing quality standards
        When reviewing coverage requirements
        Then thresholds should be specific (60%, 80%, 90%, 95%+)
        """
        # Assert - specific percentage thresholds exist
        assert "%" in quality_standards_content
        # Has specific numbers indicating thresholds
        assert any(
            num in quality_standards_content for num in ["60", "70", "80", "90", "95"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_coverage_thresholds_define_use_cases(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Coverage thresholds map to use cases.

        Given the testing quality standards
        When reviewing threshold application
        Then each threshold should have a defined use case
        """
        # Assert - thresholds have context/use cases
        assert "coverage" in quality_standards_content.lower()
        # Multiple coverage levels mentioned
        content_lower = quality_standards_content.lower()
        assert (
            "critical" in content_lower
            or "edge" in content_lower
            or "path" in content_lower
        )


class TestAntiPatternsDocumentation:
    """Feature: Anti-patterns are documented to prevent cargo cult.

    As a testing practitioner
    I want documented anti-patterns
    So that I can avoid common testing mistakes
    """

    @pytest.fixture
    def quality_standards_path(self) -> Path:
        """Path to the testing-quality-standards skill."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "SKILL.md"
        )

    @pytest.fixture
    def quality_standards_content(self, quality_standards_path: Path) -> str:
        """Load the testing-quality-standards skill content."""
        return quality_standards_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_anti_patterns_module_exists(self, quality_standards_content: str) -> None:
        """Scenario: Anti-patterns module is referenced.

        Given the testing quality standards
        When reviewing documentation structure
        Then anti-patterns should be documented in a separate module
        """
        # Assert - anti-patterns referenced
        assert (
            "anti-pattern" in quality_standards_content.lower()
            or "anti pattern" in quality_standards_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_anti_patterns_include_before_after(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Anti-patterns include before/after examples.

        Given the testing quality standards
        When reviewing anti-pattern documentation
        Then examples should show bad vs good patterns
        """
        # Assert - before/after or bad/good pattern examples
        content_lower = quality_standards_content.lower()
        assert (
            "example" in content_lower
            or "```" in quality_standards_content  # Code examples
        )


class TestQualityMetricsCompleteness:
    """Feature: Quality metrics cover all aspects of test quality.

    As a testing framework designer
    I want comprehensive quality metrics
    So that all aspects of test quality are measured
    """

    @pytest.fixture
    def quality_standards_path(self) -> Path:
        """Path to the testing-quality-standards skill."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "SKILL.md"
        )

    @pytest.fixture
    def quality_standards_content(self, quality_standards_path: Path) -> str:
        """Load the testing-quality-standards skill content."""
        return quality_standards_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_metrics_cover_structure(self, quality_standards_content: str) -> None:
        """Scenario: Quality metrics include structure criteria.

        Given the testing quality standards
        When reviewing quality categories
        Then structure metrics should exist (organization, names, setup/teardown)
        """
        # Assert - structure metrics documented
        assert "structure" in quality_standards_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_metrics_cover_coverage(self, quality_standards_content: str) -> None:
        """Scenario: Quality metrics include coverage criteria.

        Given the testing quality standards
        When reviewing quality categories
        Then coverage metrics should exist (critical paths, edge cases, errors)
        """
        # Assert - coverage metrics documented
        assert "coverage" in quality_standards_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_metrics_cover_maintainability(
        self, quality_standards_content: str
    ) -> None:
        """Scenario: Quality metrics include maintainability criteria.

        Given the testing quality standards
        When reviewing quality categories
        Then maintainability metrics should exist (DRY, fixtures, assertions)
        """
        # Assert - maintainability metrics documented
        assert "maintain" in quality_standards_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_metrics_cover_reliability(self, quality_standards_content: str) -> None:
        """Scenario: Quality metrics include reliability criteria.

        Given the testing quality standards
        When reviewing quality categories
        Then reliability metrics should exist (flakiness, determinism, speed)
        """
        # Assert - reliability metrics documented
        assert (
            "reliability" in quality_standards_content.lower()
            or "flaky" in quality_standards_content.lower()
        )


class TestContentAssertionLevelsModuleContent:
    """Feature: Content assertion levels module defines the L1/L2/L3 taxonomy.

    As a testing workflow that encounters execution markdown changes
    I want a canonical definition of content assertion levels
    So that I know which tests to write for each content type.

    Level 1: Structural presence (keyword checks).
    Level 2: Code example validity (Python/JSON/YAML parsing).
    """

    @pytest.fixture
    def module_path(self) -> Path:
        return (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "modules"
            / "content-assertion-levels.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        return module_path.read_text()

    # --- L1: Structural presence ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists_with_substance(self, module_path: Path) -> None:
        """Given the content assertion levels module
        Then it must exist with substantial content."""
        assert module_path.exists()
        content = module_path.read_text()
        assert len(content.splitlines()) >= 50, "Module should be substantial"

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "required_section",
        [
            "Level 1",
            "Level 2",
            "Level 3",
        ],
    )
    def test_module_defines_all_three_levels(
        self, module_content: str, required_section: str
    ) -> None:
        """Given the content assertion levels module
        Then it must define all three assertion levels."""
        assert required_section in module_content, (
            f"Missing '{required_section}' definition"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_when_to_apply(self, module_content: str) -> None:
        """Given the module guides test authors
        Then it must explain when to apply each level."""
        assert "when to apply" in module_content.lower() or (
            "content type" in module_content.lower()
            and "minimum level" in module_content.lower()
        ), "Must explain when each level applies"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_references_exemplar_tests(self, module_content: str) -> None:
        """Given the module provides guidance
        Then it must reference real test exemplars."""
        assert (
            "test_" in module_content.lower() or "exemplar" in module_content.lower()
        ), "Must reference exemplar test classes"

    # --- L2: Code block validity ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_python_code_blocks_are_syntactically_valid(
        self, module_content: str
    ) -> None:
        """Given Python code blocks in the module
        When Claude copies them as test scaffolding
        Then every block must be valid Python syntax."""
        import ast
        import re

        # Anchor closing fence to line start to avoid matching
        # triple backticks inside code block string literals
        python_blocks = re.findall(
            r"```python\n(.*?)\n```",
            module_content,
            re.DOTALL | re.MULTILINE,
        )
        assert len(python_blocks) >= 1, "Module should contain Python examples"
        for i, block in enumerate(python_blocks):
            try:
                ast.parse(block)
            except SyntaxError as exc:
                pytest.fail(f"Python block #{i + 1} has invalid syntax: {exc}")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_references_this_module(self) -> None:
        """Given the SKILL.md provides the entry point
        Then it must reference the content-assertion-levels module."""
        skill_path = (
            Path(__file__).parents[3]
            / "skills"
            / "testing-quality-standards"
            / "SKILL.md"
        )
        skill_content = skill_path.read_text()
        assert "content-assertion-levels" in skill_content, (
            "SKILL.md must reference this module"
        )
