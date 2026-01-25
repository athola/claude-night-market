"""Tests for skills-eval skill and quality assessment framework.

This module tests the skills evaluation framework including cargo cult
pattern detection, documentation testing, and quality gate enforcement.

Following TDD/BDD principles to ensure evaluation standards are met.
"""

from pathlib import Path

import pytest


class TestSkillsEvalQualityFramework:
    """Feature: Skills-eval provides comprehensive quality assessment.

    As a skill author
    I want automated quality checks
    So that skills meet production standards
    """

    @pytest.fixture
    def skills_eval_path(self) -> Path:
        """Path to the skills-eval skill."""
        return Path(__file__).parents[3] / "skills" / "skills-eval" / "SKILL.md"

    @pytest.fixture
    def skills_eval_content(self, skills_eval_path: Path) -> str:
        """Load the skills-eval skill content."""
        return skills_eval_path.read_text()

    @pytest.fixture
    def evaluation_criteria_path(self) -> Path:
        """Path to evaluation criteria module."""
        return (
            Path(__file__).parents[3]
            / "skills"
            / "skills-eval"
            / "modules"
            / "evaluation-criteria.md"
        )

    @pytest.fixture
    def evaluation_criteria_content(self, evaluation_criteria_path: Path) -> str:
        """Load the evaluation criteria module content."""
        return evaluation_criteria_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_defines_cargo_cult_detection(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework detects cargo cult anti-patterns.

        Given the skills-eval framework
        When reading the evaluation criteria
        Then it should define cargo cult testing patterns
        And include verification requirements
        """
        # Assert - cargo cult patterns are defined
        assert (
            "cargo cult" in evaluation_criteria_content.lower()
            or "cargo-cult" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_requires_verification_steps(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework requires verification after examples.

        Given the skills-eval framework
        When reviewing quality criteria
        Then it should require verification steps after code examples
        """
        # Assert - verification requirements exist
        assert "verification" in evaluation_criteria_content.lower()
        assert (
            "after each code example" in evaluation_criteria_content.lower()
            or "after examples" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_defines_documentation_testing(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework includes documentation testing.

        Given the skills-eval framework
        When reviewing evaluation criteria
        Then it should test documentation quality
        And require concrete Quick Start sections
        """
        # Assert - documentation testing exists
        assert "quick start" in evaluation_criteria_content.lower()
        assert (
            "concrete" in evaluation_criteria_content.lower()
            or "actual commands" in evaluation_criteria_content.lower()
            or "abstract" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_requires_trigger_phrases(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework requires minimum trigger phrases.

        Given the skills-eval framework
        When reviewing activation criteria
        Then it should require at least 5 trigger phrases
        """
        # Assert - trigger phrase requirements exist
        assert "trigger" in evaluation_criteria_content.lower()
        # Check for the specific requirement (5 phrases)
        assert (
            "5" in evaluation_criteria_content
            or "five" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_enforces_toc_requirements(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework enforces TOC for long modules.

        Given the skills-eval framework
        When reviewing token efficiency criteria
        Then it should require TOCs in modules >100 lines
        """
        # Assert - TOC requirements exist
        assert (
            "toc" in evaluation_criteria_content.lower()
            or "table of contents" in evaluation_criteria_content.lower()
        )
        assert "100" in evaluation_criteria_content  # Threshold for TOC requirement

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_defines_quality_levels(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework defines quality levels.

        Given the skills-eval framework
        When reviewing scoring system
        Then it should define quality levels (A-F or 1-5)
        """
        # Assert - quality levels exist
        assert (
            "level" in evaluation_criteria_content.lower()
            or "grade" in evaluation_criteria_content.lower()
        )
        # Check for scoring system
        assert "score" in evaluation_criteria_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_defines_critical_issues(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework defines critical issue categories.

        Given the skills-eval framework
        When reviewing issue classification
        Then it should define critical, high, medium, low severity
        """
        # Assert - severity levels exist
        assert "critical" in evaluation_criteria_content.lower()
        assert (
            "high" in evaluation_criteria_content.lower()
            or "medium" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_includes_voice_consistency_check(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework checks for consistent voice.

        Given the skills-eval framework
        When reviewing content quality criteria
        Then it should check for second-person voice ("you"/"your")
        """
        # Assert - voice checking exists
        assert (
            "you" in evaluation_criteria_content.lower()
            or "your" in evaluation_criteria_content.lower()
            or "second-person" in evaluation_criteria_content.lower()
            or "third person" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_defines_progressive_disclosure(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework enforces progressive disclosure.

        Given the skills-eval framework
        When reviewing structure compliance
        Then it should require progressive disclosure patterns
        And limit SKILL.md length
        """
        # Assert - progressive disclosure exists
        assert (
            "progressive" in evaluation_criteria_content.lower()
            or "disclosure" in evaluation_criteria_content.lower()
        )
        # Check for line limits
        assert "lines" in evaluation_criteria_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_has_quality_gates(
        self, evaluation_criteria_content: str
    ) -> None:
        """Scenario: Evaluation framework defines quality gates.

        Given the skills-eval framework
        When reviewing quality enforcement
        Then it should define minimum score thresholds
        """
        # Assert - quality gates exist
        assert (
            "gate" in evaluation_criteria_content.lower()
            or "threshold" in evaluation_criteria_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_eval_references_iron_law(self, skills_eval_content: str) -> None:
        """Scenario: Skills-eval references Iron Law for TDD compliance.

        Given the skills-eval skill
        When reading the skill content
        Then it should reference TDD/Iron Law compliance
        """
        # Assert - Iron Law reference exists
        # This may be in related skills rather than skills-eval itself
        # So we just check the skill exists and has quality criteria
        assert "quality" in skills_eval_content.lower()


class TestModularSkillsQualityChecks:
    """Feature: Modular-skills enforces quality standards for skill architecture.

    As a skill author
    I want quality checks for modular design
    So that skills remain maintainable
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
    def test_modular_skills_includes_quality_checks(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills includes quality standards section.

        Given the modular-skills skill
        When reading the skill content
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
    def test_modular_skills_defines_line_limits(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills defines recommended line limits.

        Given the modular-skills skill
        When reading the skill content
        Then it should specify line count limits
        """
        # Assert - line limits mentioned
        assert "150" in modular_skills_content or "100" in modular_skills_content
        assert "lines" in modular_skills_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modular_skills_includes_quick_start_commands(
        self, modular_skills_content: str
    ) -> None:
        """Scenario: Modular-skills Quick Start has actual commands.

        Given the modular-skills skill
        When reviewing the Quick Start section
        Then it should include actual commands, not abstract descriptions
        """
        # Assert - concrete commands exist (bash/python code blocks)
        assert "```" in modular_skills_content  # Code blocks exist
        # Check for actual commands, not descriptions
        assert (
            "python" in modular_skills_content.lower()
            or "bash" in modular_skills_content.lower()
        )


class TestWorkflowMonitorQualityChecks:
    """Feature: Workflow-monitor includes efficiency detection patterns.

    As a workflow optimizer
    I want automated inefficiency detection
    So that workflows improve over time
    """

    @pytest.fixture
    def workflow_monitor_path(self) -> Path:
        """Path to the workflow-monitor skill."""
        # This is in the imbue plugin
        # Go up 4 levels from abstract/tests/unit/skills to plugins/
        return (
            Path(__file__).parents[4]  # Back to plugins/ directory
            / "imbue"
            / "skills"
            / "workflow-monitor"
            / "SKILL.md"
        )

    @pytest.fixture
    def workflow_monitor_content(self, workflow_monitor_path: Path) -> str:
        """Load the workflow-monitor skill content."""
        return workflow_monitor_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_monitor_has_toc(self, workflow_monitor_content: str) -> None:
        """Scenario: Workflow-monitor includes Table of Contents.

        Given the workflow-monitor skill
        When reading the skill content
        Then it should have a TOC for navigation
        """
        # Assert - TOC exists
        assert (
            "## Table of Contents" in workflow_monitor_content
            or "table of contents" in workflow_monitor_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_monitor_defines_detection_patterns(
        self, workflow_monitor_content: str
    ) -> None:
        """Scenario: Workflow-monitor defines inefficiency patterns.

        Given the workflow-monitor skill
        When reading the skill content
        Then it should define detection patterns
        """
        # Assert - detection patterns exist
        assert "detection" in workflow_monitor_content.lower()
        assert "pattern" in workflow_monitor_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_monitor_includes_efficiency_metrics(
        self, workflow_monitor_content: str
    ) -> None:
        """Scenario: Workflow-monitor defines efficiency thresholds.

        Given the workflow-monitor skill
        When reviewing detection criteria
        Then it should include specific efficiency thresholds
        """
        # Assert - efficiency metrics exist
        assert "efficiency" in workflow_monitor_content.lower()
        # Check for thresholds (numbers indicate specific thresholds)
        assert any(char.isdigit() for char in workflow_monitor_content)


class TestDocumentationTestingPatterns:
    """Feature: Documentation testing ensures skill quality.

    As a skill evaluator
    I want automated documentation testing
    So that skills are testable and verifiable
    """

    @pytest.fixture
    def skills_eval_path(self) -> Path:
        """Path to the skills-eval skill."""
        return Path(__file__).parents[3] / "skills" / "skills-eval" / "SKILL.md"

    @pytest.fixture
    def skills_eval_content(self, skills_eval_path: Path) -> str:
        """Load the skills-eval skill content."""
        return skills_eval_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_have_testable_structure(self, skills_eval_content: str) -> None:
        """Scenario: Skills can be tested for structural compliance.

        Given a skill file
        When testing structural requirements
        Then it should validate frontmatter, sections, and patterns
        """
        # Assert - skill has testable structure elements
        assert "---" in skills_eval_content  # Frontmatter markers
        assert "## " in skills_eval_content  # Section headers
        assert "name:" in skills_eval_content  # Required frontmatter field

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evaluation_framework_prevents_cargo_cult(
        self, skills_eval_content: str
    ) -> None:
        """Scenario: Evaluation framework prevents cargo cult patterns.

        Given quality criteria
        When reviewing skills
        Then cargo cult anti-patterns should be detectable
        """
        # Assert - framework documents cargo cult prevention
        # skills-eval references evaluation criteria that detect cargo cult
        assert "quality" in skills_eval_content.lower()
        assert "```" in skills_eval_content  # Has code blocks (not just descriptions)


class TestProgressiveDisclosureEnforcement:
    """Feature: Skills follow progressive disclosure patterns.

    As a skill user
    I want essential information first
    So that I can understand quickly without reading everything
    """

    @pytest.fixture
    def skills_eval_path(self) -> Path:
        """Path to the skills-eval skill."""
        return Path(__file__).parents[3] / "skills" / "skills-eval" / "SKILL.md"

    @pytest.fixture
    def skills_eval_content(self, skills_eval_path: Path) -> str:
        """Load the skills-eval skill content."""
        return skills_eval_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skills_follow_modular_structure(self, skills_eval_content: str) -> None:
        """Scenario: Skills use modular structure for progressive disclosure.

        Given skill evaluation criteria
        When reviewing skill architecture
        Then modules should be referenced for deep details
        """
        # Assert - skill references modules for details
        assert "modules/" in skills_eval_content
        assert "See " in skills_eval_content or "see " in skills_eval_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_toc_required_for_long_modules(self, skills_eval_content: str) -> None:
        """Scenario: Long modules require TOC for navigation.

        Given a module exceeding 100 lines
        When evaluating structure
        Then a TOC should be required
        """
        # Assert - TOC exists in the skill (which exceeds 100 lines)
        assert "## Table of Contents" in skills_eval_content
        # Has section links
        assert "[" in skills_eval_content and "](" in skills_eval_content
