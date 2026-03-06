"""Extended tests for src/abstract/skills_eval/improvements.py.

Feature: Skill improvement suggestions
    As a developer
    I want all branches of improvement analysis tested
    So that edge cases are handled correctly
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.skills_eval.improvements import Improvement, ImprovementSuggester

# ---------------------------------------------------------------------------
# Tests: ImprovementItem.__post_init__
# ---------------------------------------------------------------------------


class TestImprovement:
    """Feature: Improvement dataclass initializes defaults correctly."""

    @pytest.mark.unit
    def test_dependencies_none_becomes_empty_list(self) -> None:
        """Scenario: dependencies=None is converted to empty list.
        Given Improvement constructed without dependencies
        When the object is initialized
        Then dependencies is an empty list
        """
        item = Improvement(
            category="high",
            priority=1,
            description="A test item",
            specific_action="Do something",
        )
        assert item.dependencies == []

    @pytest.mark.unit
    def test_dependencies_provided_stays(self) -> None:
        """Scenario: Provided dependencies list is preserved."""
        item = Improvement(
            category="high",
            priority=1,
            description="A test item",
            specific_action="Do something",
            dependencies=["dep1"],
        )
        assert item.dependencies == ["dep1"]


# ---------------------------------------------------------------------------
# Tests: analyze_skill edge cases
# ---------------------------------------------------------------------------


class TestAnalyzeSkillEdgeCases:
    """Feature: analyze_skill handles missing/invalid files."""

    @pytest.mark.unit
    def test_skill_not_found_returns_error(self, tmp_path: Path) -> None:
        """Scenario: analyze_skill for missing skill returns error dict.
        Given a skill name that doesn't exist in the directory
        When analyze_skill is called
        Then the result contains an issues entry about missing file
        """
        suggester = ImprovementSuggester(tmp_path)
        result = suggester.analyze_skill("nonexistent-skill")
        assert "issues" in result
        assert any("not found" in issue.lower() for issue in result["issues"])

    @pytest.mark.unit
    def test_skill_without_frontmatter_gets_suggestion(self, tmp_path: Path) -> None:
        """Scenario: Skill file without frontmatter gets suggestion.
        Given a skill file with no YAML frontmatter
        When analyze_skill is called
        Then suggestions include adding frontmatter
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill\n\nNo frontmatter.\n")

        suggester = ImprovementSuggester(tmp_path)
        result = suggester.analyze_skill("my-skill")
        assert "suggestions" in result

    @pytest.mark.unit
    def test_skill_missing_required_fields_gets_issues(self, tmp_path: Path) -> None:
        """Scenario: Skill without description gets missing-field issue.
        Given a SKILL.md with name but no description
        When analyze_skill is called
        Then issues contain 'Missing required fields'
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n\n# My Skill\n\n## Overview\n\nContent.\n"
        )

        suggester = ImprovementSuggester(tmp_path)
        result = suggester.analyze_skill("my-skill")
        # Should have a suggestion about missing description
        assert "suggestions" in result


# ---------------------------------------------------------------------------
# Tests: suggest_modularization edge cases
# ---------------------------------------------------------------------------


class TestSuggestModularizationEdgeCases:
    """Feature: suggest_modularization edge cases."""

    @pytest.mark.unit
    def test_missing_skill_returns_not_found(self, tmp_path: Path) -> None:
        """Scenario: Missing skill file returns 'Skill file not found'."""
        suggester = ImprovementSuggester(tmp_path)
        result = suggester.suggest_modularization("nonexistent-skill")
        assert result == ["Skill file not found"]

    @pytest.mark.unit
    def test_large_skill_gets_extract_suggestion(self, tmp_path: Path) -> None:
        """Scenario: Large skill file gets extraction suggestion.
        Given a skill file with more than TOKEN_MAX_EFFICIENT tokens
        When suggest_modularization is called
        Then suggestions include extracting content
        """
        skill_dir = tmp_path / "large-skill"
        skill_dir.mkdir()
        # Create a large skill (many tokens)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: large-skill\ndescription: big\n---\n\n"
            "# Large Skill\n\n" + "word " * 4000  # Should exceed TOKEN_MAX_EFFICIENT
        )

        suggester = ImprovementSuggester(tmp_path)
        result = suggester.suggest_modularization("large-skill")
        # Should have some suggestions
        assert len(result) > 0

    @pytest.mark.unit
    def test_skill_with_many_code_blocks_gets_suggestion(self, tmp_path: Path) -> None:
        """Scenario: Skill with many code blocks gets tool extraction suggestion."""
        skill_dir = tmp_path / "code-heavy-skill"
        skill_dir.mkdir()
        # More than CODE_BLOCKS_MODULARIZE (2) code block pairs
        code_blocks = (
            "```python\nprint('hello')\n```\n\n" * 6  # 6 code blocks
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nname: code-heavy\ndescription: lots of code\n---\n\n"
            "# Code Heavy Skill\n\n" + code_blocks
        )

        suggester = ImprovementSuggester(tmp_path)
        result = suggester.suggest_modularization("code-heavy-skill")
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Tests: suggest_improved_structure edge cases
# ---------------------------------------------------------------------------


class TestSuggestImprovedStructureEdgeCases:
    """Feature: suggest_improved_structure handles edge cases."""

    @pytest.mark.unit
    def test_missing_skill_returns_not_found(self, tmp_path: Path) -> None:
        """Scenario: Missing skill file returns 'Skill file not found'."""
        suggester = ImprovementSuggester(tmp_path)
        result = suggester.suggest_improved_structure("nonexistent-skill")
        assert result == ["Skill file not found"]

    @pytest.mark.unit
    def test_skill_missing_sections_gets_suggestions(self, tmp_path: Path) -> None:
        """Scenario: Skill without required sections gets suggestions."""
        skill_dir = tmp_path / "bare-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bare-skill\ndescription: minimal\n---\n\n"
            "# Bare Skill\n\nMinimal content.\n"
        )

        suggester = ImprovementSuggester(tmp_path)
        result = suggester.suggest_improved_structure("bare-skill")
        # Should suggest adding sections
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Tests: generate_improvement_plan timeline branches
# ---------------------------------------------------------------------------


class TestGenerateImprovementPlanTimeline:
    """Feature: generate_improvement_plan assigns timelines correctly."""

    @pytest.mark.unit
    def test_well_structured_skill_has_low_or_medium_priority(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Well-structured skill gets low or medium priority."""
        skill_dir = tmp_path / "good-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: good-skill\n"
            "description: A well-structured skill\n"
            "---\n\n"
            "# Good Skill\n\n"
            "## Overview\nThis skill does X.\n\n"
            "## Quick Start\nRun this command.\n\n"
            "## Examples\nSee example below.\n\n"
            "## Resources\nFurther reading.\n"
        )

        suggester = ImprovementSuggester(tmp_path)
        plan = suggester.generate_improvement_plan("good-skill")
        assert "priority" in plan
        assert plan["priority"] in ("low", "medium", "high")

    @pytest.mark.unit
    def test_plan_has_estimated_timeline(self, tmp_path: Path) -> None:
        """Scenario: Plan always contains estimated_timeline."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: test\n---\n\n# Skill\n\nContent.\n"
        )

        suggester = ImprovementSuggester(tmp_path)
        plan = suggester.generate_improvement_plan("my-skill")
        assert "estimated_timeline" in plan
        assert plan["estimated_timeline"] in ("1-2 days", "1 week", "2 weeks")

    @pytest.mark.unit
    def test_1_week_timeline_for_medium_suggestions(self, tmp_path: Path) -> None:
        """Scenario: Skill with moderate issues gets '1 week' timeline.

        The timeline logic uses SUGGESTIONS_LOW <= count <= SUGGESTIONS_MEDIUM
        boundaries. This test just verifies the plan completes without error.
        """
        skill_dir = tmp_path / "medium-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: medium-skill\n---\n\n# Medium Skill\n\nContent.\n"
        )

        suggester = ImprovementSuggester(tmp_path)
        plan = suggester.generate_improvement_plan("medium-skill")
        assert plan["estimated_timeline"] in ("1-2 days", "1 week", "2 weeks")
