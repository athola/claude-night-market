"""Tests for plugin-review skill structure and content.

This module validates the plugin-review SKILL.md defines
the tiered review orchestration, scope detection, module
loading, and verdict system required for plugin quality reviews.

Following BDD principles with Given/When/Then scenarios.
"""

from pathlib import Path

import pytest


class TestPluginReviewSkillStructure:
    """Feature: Plugin review skill provides tiered quality review.

    As a plugin maintainer
    I want a tiered review process
    So that review depth matches the context (branch/PR/release)
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the plugin-review skill."""
        return Path(__file__).parents[3] / "skills" / "plugin-review" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the plugin-review skill content."""
        return skill_path.read_text()

    @pytest.fixture
    def modules_dir(self) -> Path:
        """Path to the plugin-review modules directory."""
        return Path(__file__).parents[3] / "skills" / "plugin-review" / "modules"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Plugin review skill file exists.

        Given the abstract plugin
        When looking for the plugin-review skill
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_modules_directory_exists(self, modules_dir: Path) -> None:
        """Scenario: Modules directory exists for progressive loading.

        Given the plugin-review skill
        When checking for the modules directory
        Then it should exist (for later tier modules)
        """
        assert modules_dir.exists(), f"modules/ directory not found at {modules_dir}"
        assert modules_dir.is_dir()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Skill frontmatter contains required metadata.

        Given the plugin-review SKILL.md
        When parsing the frontmatter
        Then it should have name, description, category, and tags
        """
        assert "name: plugin-review" in skill_content
        assert "category: plugin-management" in skill_content
        assert "tags:" in skill_content
        assert "description:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_declares_dependencies(self, skill_content: str) -> None:
        """Scenario: Skill declares dependencies on eval skills.

        Given the plugin-review skill
        When checking dependencies
        Then it should depend on skills-eval, hooks-eval, and rules-eval
        """
        assert "- skills-eval" in skill_content
        assert "- hooks-eval" in skill_content
        assert "- rules-eval" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_enables_progressive_loading(self, skill_content: str) -> None:
        """Scenario: Skill enables progressive loading.

        Given the plugin-review skill
        When checking the frontmatter
        Then progressive_loading should be true
        """
        assert "progressive_loading: true" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_three_tiers(self, skill_content: str) -> None:
        """Scenario: Skill defines branch, PR, and release tiers.

        Given the plugin-review SKILL.md
        When reading the tier definitions
        Then it should define branch, pr, and release tiers
        """
        assert "## Tiers" in skill_content
        assert "| branch |" in skill_content
        assert "| pr |" in skill_content
        assert "| release |" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_orchestration_steps(self, skill_content: str) -> None:
        """Scenario: Skill defines the orchestration flow.

        Given the plugin-review SKILL.md
        When reading orchestration
        Then it should define detect, plan, execute, report steps
        """
        assert "## Orchestration" in skill_content
        assert "Detect scope" in skill_content
        assert "Plan" in skill_content
        assert "Execute" in skill_content
        assert "Report" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_scope_detection(self, skill_content: str) -> None:
        """Scenario: Skill explains how affected plugins are detected.

        Given the plugin-review SKILL.md
        When reading scope detection
        Then it should reference git diff and plugin-dependencies.json
        """
        assert "## Scope Detection" in skill_content
        assert "git diff" in skill_content
        assert "plugin-dependencies.json" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_module_loading_per_tier(self, skill_content: str) -> None:
        """Scenario: Skill specifies which modules load per tier.

        Given the plugin-review SKILL.md
        When reading module loading rules
        Then each tier should reference its module file
        """
        assert "## Module Loading" in skill_content
        assert "modules/tier-branch.md" in skill_content
        assert "modules/tier-pr.md" in skill_content
        assert "modules/tier-release.md" in skill_content
        assert "modules/dependency-detection.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_verdict_system(self, skill_content: str) -> None:
        """Scenario: Skill defines PASS/WARN/FAIL verdict system.

        Given the plugin-review SKILL.md
        When reading the verdict section
        Then it should define PASS, PASS-WITH-WARNINGS, and FAIL
        """
        assert "## Verdict" in skill_content
        assert "PASS" in skill_content
        assert "PASS-WITH-WARNINGS" in skill_content
        assert "FAIL" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_output_format(self, skill_content: str) -> None:
        """Scenario: Skill defines the review output format.

        Given the plugin-review SKILL.md
        When reading the output format
        Then it should show the per-plugin table template
        """
        assert "## Output Format" in skill_content
        assert "Plugin Review" in skill_content
        assert "verdict" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_lists_tools(self, skill_content: str) -> None:
        """Scenario: Skill frontmatter declares required tools.

        Given the plugin-review SKILL.md
        When checking the tools list
        Then it should list validate_plugin.py and others
        """
        assert "tools:" in skill_content
        assert "- validate_plugin.py" in skill_content
        assert "- skill_analyzer.py" in skill_content
        assert "- generate_dependency_map.py" in skill_content
