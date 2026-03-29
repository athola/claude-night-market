"""Tests for token usage tracking functionality."""

import json

import pytest

from abstract.skills_eval import TokenUsageTracker

# Constants
EXPECTED_SKILL_COUNT = 3


class TestTokenUsageTracker:
    """Test cases for TokenUsageTracker."""

    @pytest.fixture
    def sample_skills_dir(self, tmp_path):
        """Create a temporary directory with skill files."""
        skills_data = {
            "small-skill": """---
name: small-skill
description: A small skill
category: testing
---

# Small Skill

## Overview
This is a small skill with minimal content.

## Quick Start
Use it simply.

## Detailed Resources
Not much here.
""",
            "medium-skill": """---
name: medium-skill
description: A medium-sized skill
category: intermediate
dependencies: [small-skill]
---

# Medium Skill

## Overview
This skill has more content.

## Quick Start
Follow these steps to use the skill.

1. Step one
2. Step two
3. Step three

## Detailed Resources
More detailed information about the skill and its usage.

## Examples
Here are some examples of how to use this skill effectively.
""",
            "large-skill": """---
name: large-skill
description: A detailed skill with extensive content
category: advanced
dependencies: [medium-skill]
---

# Large detailed Skill

## Overview
This skill contains extensive content covering multiple aspects of the topic.

## Quick Start
To get started with this skill, follow these detailed instructions:

1. First, you need to understand the basic concepts
2. Then, configure your environment properly
3. Next, learn the fundamental operations
4. After that, explore advanced features
5. Finally, integrate with other tools

## Detailed Resources

### Configuration Options
This section covers all the configuration options available:
- Option 1 with detailed explanation
- Option 2 with examples and use cases
- Option 3 with best practices
- Option 4 with troubleshooting tips

### Advanced Usage Patterns
"""
            + "Detailed content for advanced usage patterns. " * 100
            + """

### Integration Examples
Multiple examples showing how to integrate this skill with other tools and workflows.

### Troubleshooting Guide
detailed troubleshooting guide covering common issues and their solutions.
""",
        }

        for skill_name, content in skills_data.items():
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(content)

        return tmp_path

    def test_tracker_initialization(self, sample_skills_dir) -> None:
        """Test tracker initializes correctly."""
        tracker = TokenUsageTracker(sample_skills_dir)
        assert tracker.skills_root == sample_skills_dir
        assert hasattr(tracker, "analyze_skill_tokens")

    def test_analyze_small_skill_tokens(self, sample_skills_dir) -> None:
        """Test token analysis for a small skill."""
        tracker = TokenUsageTracker(sample_skills_dir)
        analysis = tracker.analyze_skill_tokens("small-skill")

        assert "name" in analysis
        assert "total_tokens" in analysis
        assert "frontmatter_tokens" in analysis
        assert "content_tokens" in analysis
        assert "sections" in analysis
        assert analysis["name"] == "small-skill"
        assert analysis["total_tokens"] > 0
        assert analysis["frontmatter_tokens"] > 0
        assert analysis["content_tokens"] > 0

    def test_analyze_medium_skill_tokens(self, sample_skills_dir) -> None:
        """Test token analysis for a medium skill."""
        tracker = TokenUsageTracker(sample_skills_dir)
        analysis = tracker.analyze_skill_tokens("medium-skill")

        # Medium skill should have more tokens than small skill
        small_analysis = tracker.analyze_skill_tokens("small-skill")
        assert analysis["total_tokens"] > small_analysis["total_tokens"]

        # Should detect multiple sections
        assert len(analysis["sections"]) > len(small_analysis["sections"])

    def test_analyze_large_skill_tokens(self, sample_skills_dir) -> None:
        """Test token analysis for a large skill."""
        tracker = TokenUsageTracker(sample_skills_dir)
        analysis = tracker.analyze_skill_tokens("large-skill")

        # Large skill should have significantly more tokens
        medium_analysis = tracker.analyze_skill_tokens("medium-skill")
        assert analysis["total_tokens"] > medium_analysis["total_tokens"]

        # Should identify it as potentially needing modularization
        assert analysis["needs_modularization"]

    def test_analyze_all_skills(self, sample_skills_dir) -> None:
        """Test detailed token analysis across all skills."""
        tracker = TokenUsageTracker(sample_skills_dir)
        all_analysis = tracker.analyze_all_skills()

        assert "total_skills" in all_analysis
        assert "skills" in all_analysis
        assert "summary" in all_analysis
        assert all_analysis["total_skills"] == EXPECTED_SKILL_COUNT
        assert len(all_analysis["skills"]) == EXPECTED_SKILL_COUNT

        # Should include all skill names
        skill_names = [skill["name"] for skill in all_analysis["skills"]]
        assert "small-skill" in skill_names
        assert "medium-skill" in skill_names
        assert "large-skill" in skill_names

    def test_calculate_token_efficiency(self, sample_skills_dir) -> None:
        """Test token efficiency calculations."""
        tracker = TokenUsageTracker(sample_skills_dir)
        efficiency = tracker.calculate_token_efficiency()

        assert "overall_efficiency" in efficiency
        assert "skill_efficiencies" in efficiency
        assert "optimization_opportunities" in efficiency

        # Should identify optimization opportunities
        assert len(efficiency["optimization_opportunities"]) > 0
        # Large skill should be flagged for optimization
        large_skill_optimization = [
            opt
            for opt in efficiency["optimization_opportunities"]
            if "large-skill" in opt.get("skill", "")
        ]
        assert len(large_skill_optimization) > 0

    def test_suggest_modularization(self, sample_skills_dir) -> None:
        """Test modularization suggestions."""
        tracker = TokenUsageTracker(sample_skills_dir)
        suggestions = tracker.suggest_modularization()

        assert isinstance(suggestions, list)
        # Should suggest modularizing the large skill
        large_suggestions = [
            s for s in suggestions if "large-skill" in s.get("skill", "")
        ]
        assert len(large_suggestions) > 0

        # Suggestions should include specific modules
        for suggestion in large_suggestions:
            if suggestion.get("skill") == "large-skill":
                assert "suggested_modules" in suggestion
                assert len(suggestion["suggested_modules"]) > 0

    def test_track_usage_over_time(self, sample_skills_dir, tmp_path) -> None:
        """Test tracking token usage over time."""
        tracker = TokenUsageTracker(sample_skills_dir)

        # Initial analysis
        initial_analysis = tracker.analyze_all_skills()

        # Simulate time passage and create usage record
        usage_record = {
            "timestamp": "2024-01-01T12:00:00Z",
            "total_tokens": initial_analysis["summary"]["total_tokens"],
            "skills_used": ["small-skill", "medium-skill"],
        }

        # Track usage
        tracker.record_usage(usage_record)

        # Should have usage history
        assert len(tracker.usage_history) > 0

    def test_generate_usage_report(self, sample_skills_dir) -> None:
        """Test detailed usage report generation."""
        tracker = TokenUsageTracker(sample_skills_dir)
        analysis = tracker.analyze_all_skills()
        report = tracker.generate_usage_report(analysis)

        assert "Token Usage Report" in report
        assert "Total Skills" in report
        assert "Summary Statistics" in report
        assert "small-skill" in report
        assert "large-skill" in report

    def test_identify_optimization_opportunities(self, sample_skills_dir) -> None:
        """Test identification of token optimization opportunities."""
        tracker = TokenUsageTracker(sample_skills_dir)
        opportunities = tracker.identify_optimization_opportunities()

        assert isinstance(opportunities, list)

        # Should identify opportunities for large skills
        large_opportunities = [
            opt for opt in opportunities if opt.get("skill") == "large-skill"
        ]
        assert len(large_opportunities) > 0

        # Opportunities should have actionable suggestions
        for opportunity in large_opportunities:
            assert "type" in opportunity
            assert "potential_savings" in opportunity
            assert "action" in opportunity

    def test_calculate_dependency_token_impact(self, sample_skills_dir) -> None:
        """Test calculation of token impact from dependencies."""
        tracker = TokenUsageTracker(sample_skills_dir)
        impact_analysis = tracker.calculate_dependency_impact()

        assert "skills" in impact_analysis
        assert "dependency_chains" in impact_analysis

        # Should calculate cumulative token impact
        for skill_data in impact_analysis["skills"]:
            assert "direct_tokens" in skill_data
            assert "dependency_tokens" in skill_data
            assert "total_impact" in skill_data

    def test_export_token_analysis(self, sample_skills_dir, tmp_path) -> None:
        """Test exporting token analysis data."""
        tracker = TokenUsageTracker(sample_skills_dir)
        analysis = tracker.analyze_all_skills()

        export_file = tmp_path / "token_analysis.json"
        tracker.export_analysis(analysis, export_file)

        assert export_file.exists()

        # Verify exported data
        with open(export_file) as f:
            exported_data = json.load(f)

        assert "total_skills" in exported_data
        assert "skills" in exported_data
        assert "summary" in exported_data

    def test_compare_token_usage(self, sample_skills_dir) -> None:
        """Test comparison of token usage between skills."""
        tracker = TokenUsageTracker(sample_skills_dir)
        comparison = tracker.compare_skills(
            ["small-skill", "medium-skill", "large-skill"],
        )

        assert "comparison_table" in comparison
        assert "analysis" in comparison
        assert "recommendations" in comparison

        # Should show token usage progression
        assert len(comparison["comparison_table"]) == EXPECTED_SKILL_COUNT

    def test_monitor_token_budgets(self, sample_skills_dir) -> None:
        """Test token budget monitoring."""
        tracker = TokenUsageTracker(sample_skills_dir)

        # Set a small budget
        budget = 1000
        budget_report = tracker.monitor_budgets(budget)

        assert "budget" in budget_report
        assert "usage" in budget_report
        assert "exceeded" in budget_report
        assert "recommendations" in budget_report

        # With the sample content, budget should be exceeded
        assert budget_report["exceeded"]
        assert len(budget_report["recommendations"]) > 0
