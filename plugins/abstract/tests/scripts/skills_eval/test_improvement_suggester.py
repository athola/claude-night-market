"""Tests for improvement suggestion functionality."""


import pytest

from abstract.skills_eval import ImprovementSuggester


class TestImprovementSuggester:
    """Test cases for ImprovementSuggester."""

    # Test constants
    EXPECTED_SKILL_COUNT = 2

    @pytest.fixture
    def temp_skill_dir(self, tmp_path):
        """Create a temporary directory with skill files."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        # Create a basic skill with some issues
        skill_content = """---
name: test-skill
description: A test skill
---

# Test Skill

This is a simple skill that needs improvement.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)
        return tmp_path

    def test_suggester_initialization(self, temp_skill_dir):
        """Test suggester initializes correctly."""
        suggester = ImprovementSuggester(temp_skill_dir)
        assert suggester.skill_root == temp_skill_dir
        assert hasattr(suggester, "analyze_skill")

    def test_analyze_basic_skill(self, temp_skill_dir):
        """Test basic skill analysis."""
        suggester = ImprovementSuggester(temp_skill_dir)
        analysis = suggester.analyze_skill("test-skill")

        assert "name" in analysis
        assert "issues" in analysis
        assert "suggestions" in analysis
        assert analysis["name"] == "test-skill"
        assert isinstance(analysis["issues"], list)
        assert isinstance(analysis["suggestions"], list)

    def test_analyze_missing_progressive_disclosure(self, tmp_path):
        """Test analysis catches missing progressive disclosure."""
        skill_dir = tmp_path / "no-progressive-skill"
        skill_dir.mkdir()

        skill_content = """---
name: no-progressive-skill
description: Skill without progressive structure
---

# No Progressive Skill

This skill just has basic content without proper structure.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)

        suggester = ImprovementSuggester(tmp_path)
        analysis = suggester.analyze_skill("no-progressive-skill")

        # Should suggest adding progressive disclosure
        assert any(
            "overview" in suggestion.lower() or "progressive" in suggestion.lower()
            for suggestion in analysis["suggestions"]
        )

    def test_analyze_long_skill_token_optimization(self, tmp_path):
        """Test analysis suggests token optimization for long skills."""
        skill_dir = tmp_path / "long-skill"
        skill_dir.mkdir()

        # Create a very long skill that needs optimization
        long_content = (
            """---
name: long-skill
description: Very long skill
---

# Long Skill

"""
            + "This is a very long skill with lots of content that could be optimized. "
            * 200
        )

        (skill_dir / "SKILL.md").write_text(long_content)

        suggester = ImprovementSuggester(tmp_path)
        analysis = suggester.analyze_skill("long-skill")

        # Should suggest modularization
        assert any(
            "modular" in suggestion.lower() or "token" in suggestion.lower()
            for suggestion in analysis["suggestions"]
        )

    def test_suggest_modularization(self, temp_skill_dir):
        """Test modularization suggestions."""
        suggester = ImprovementSuggester(temp_skill_dir)
        suggestions = suggester.suggest_modularization("test-skill")

        assert isinstance(suggestions, list)
        # Should at least suggest basic modules
        assert len(suggestions) > 0

    def test_suggest_improved_structure(self, temp_skill_dir):
        """Test structure improvement suggestions."""
        suggester = ImprovementSuggester(temp_skill_dir)
        suggestions = suggester.suggest_improved_structure("test-skill")

        assert isinstance(suggestions, list)
        # Should suggest adding missing sections
        structure_suggestions = [s for s in suggestions if "section" in s.lower()]
        assert len(structure_suggestions) > 0

    def test_generate_improvement_plan(self, temp_skill_dir):
        """Test improvement plan generation."""
        suggester = ImprovementSuggester(temp_skill_dir)
        plan = suggester.generate_improvement_plan("test-skill")

        assert "skill_name" in plan
        assert "issues_found" in plan
        assert "improvement_steps" in plan
        assert "priority" in plan
        assert plan["skill_name"] == "test-skill"
        assert isinstance(plan["improvement_steps"], list)

    def test_analyze_multiple_skills(self, tmp_path):
        """Test analysis across multiple skills."""
        # Create multiple skills with different issues
        skills_data = [
            (
                "basic-skill",
                """---
name: basic-skill
description: Basic skill
---

# Basic Skill
Simple content.""",
            ),
            (
                "advanced-skill",
                """---
name: advanced-skill
description: Advanced skill with more content
dependencies: [basic-skill]
---

# Advanced Skill

"""
                + "Detailed content here. " * 100,
            ),
        ]

        for skill_name, content in skills_data:
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(content)

        suggester = ImprovementSuggester(tmp_path)
        all_analyses = suggester.analyze_all_skills()

        assert len(all_analyses) == self.EXPECTED_SKILL_COUNT
        assert all("name" in analysis for analysis in all_analyses)
        assert all("suggestions" in analysis for analysis in all_analyses)

    def test_prioritize_suggestions(self, temp_skill_dir):
        """Test suggestion prioritization."""
        suggester = ImprovementSuggester(temp_skill_dir)

        # Mock suggestions with different priorities
        suggestions = [
            {"text": "Add missing frontmatter", "priority": "high"},
            {"text": "Improve documentation", "priority": "medium"},
            {"text": "Add examples", "priority": "low"},
        ]

        prioritized = suggester.prioritize_suggestions(suggestions)

        # Should be ordered by priority
        assert prioritized[0]["priority"] == "high"
        assert prioritized[-1]["priority"] == "low"
