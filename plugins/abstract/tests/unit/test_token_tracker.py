"""Extended tests for src/abstract/skills_eval/token_tracker.py.

Feature: Token usage tracking
    As a developer
    I want token tracking utilities tested
    So that skill token budgets are properly monitored
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.skills_eval.token_tracker import TokenUsageTracker

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def skills_dir_with_skill(tmp_path: Path) -> Path:
    """Given a skills directory with a single SKILL.md file."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: my-skill\n"
        "description: A test skill\n"
        "---\n"
        "\n"
        "# My Skill\n"
        "\n"
        "## Overview\n"
        "This is the overview section.\n"
        "\n"
        "## Usage\n"
        "How to use this skill.\n"
    )
    return tmp_path


@pytest.fixture
def skills_dir_large_skill(tmp_path: Path) -> Path:
    """Given a skills directory with a large SKILL.md file."""
    skill_dir = tmp_path / "large-skill"
    skill_dir.mkdir()
    # Create content large enough to exceed DEFAULT_OPTIMAL_LIMIT (1000 tokens)
    content = (
        "---\nname: large-skill\ndescription: Large skill\n---\n\n"
        + "# Large Skill\n\n"
        + "## Section\n"
        + ("This is content line with many words repeated many times. " * 50)
        + "\n"
    )
    (skill_dir / "SKILL.md").write_text(content)
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: track_usage
# ---------------------------------------------------------------------------


class TestTrackUsage:
    """Feature: track_usage tracks token usage for a single skill."""

    @pytest.mark.unit
    def test_track_usage_returns_dict(self, skills_dir_with_skill: Path) -> None:
        """Scenario: track_usage returns a dict with token information.
        Given a skills directory with a skill
        When track_usage is called with the skill file
        Then a dict with token_count is returned
        """
        tracker = TokenUsageTracker(skills_dir_with_skill)
        skill_file = skills_dir_with_skill / "my-skill" / "SKILL.md"
        result = tracker.track_usage(skill_file)
        assert result is not None
        assert "token_count" in result
        assert "frontmatter_tokens" in result
        assert "content_tokens" in result
        assert "skill_name" in result

    @pytest.mark.unit
    def test_track_usage_no_skills_returns_none(self, tmp_path: Path) -> None:
        """Scenario: track_usage with empty dir returns None.
        Given a skills directory with no skill files
        When track_usage is called with no path
        Then None is returned
        """
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.track_usage()
        assert result is None

    @pytest.mark.unit
    def test_track_usage_with_dir_path_reads_skill_md(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: track_usage accepts skill directory path.
        Given a path to the skill directory (not SKILL.md)
        When track_usage is called with the directory
        Then it reads SKILL.md from the directory
        """
        tracker = TokenUsageTracker(skills_dir_with_skill)
        skill_dir = skills_dir_with_skill / "my-skill"
        result = tracker.track_usage(skill_dir)
        assert result is not None
        assert result["skill_name"] == "my-skill"

    @pytest.mark.unit
    def test_track_usage_missing_file_raises(self, tmp_path: Path) -> None:
        """Scenario: Missing skill file raises FileNotFoundError."""
        tracker = TokenUsageTracker(tmp_path)
        missing = tmp_path / "nosuchskill" / "SKILL.md"
        with pytest.raises(FileNotFoundError):
            tracker.track_usage(missing)

    @pytest.mark.unit
    def test_track_usage_no_path_finds_first_skill(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: No path argument finds first skill file."""
        tracker = TokenUsageTracker(skills_dir_with_skill)
        result = tracker.track_usage()
        assert result is not None
        assert "token_count" in result


# ---------------------------------------------------------------------------
# Tests: get_usage_statistics
# ---------------------------------------------------------------------------


class TestGetUsageStatistics:
    """Feature: get_usage_statistics returns aggregate stats."""

    @pytest.mark.unit
    def test_empty_dir_returns_zero_stats(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns all-zero statistics.
        Given a skills directory with no skills
        When get_usage_statistics is called
        Then all counts are zero
        """
        tracker = TokenUsageTracker(tmp_path)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 0
        assert stats["total_tokens"] == 0
        assert stats["skills_over_limit"] == 0
        assert stats["optimal_usage_count"] == 0

    @pytest.mark.unit
    def test_with_skill_returns_nonzero_stats(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: Directory with skill returns non-zero statistics.
        Given a skills directory with a skill
        When get_usage_statistics is called
        Then total_skills is 1 and total_tokens > 0
        """
        tracker = TokenUsageTracker(skills_dir_with_skill)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 1
        assert stats["total_tokens"] > 0
        assert "average_tokens" in stats
        assert "min_tokens" in stats
        assert "max_tokens" in stats

    @pytest.mark.unit
    def test_skills_over_limit_classification(
        self, skills_dir_large_skill: Path
    ) -> None:
        """Scenario: Skills exceeding optimal limit are counted.
        Given a large skill file exceeding optimal token limit
        When get_usage_statistics is called
        Then skills_over_limit or optimal_usage_count reflects correct classification
        """
        tracker = TokenUsageTracker(skills_dir_large_skill, optimal_limit=10)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 1
        # With very low optimal_limit, the skill should be over limit
        assert stats["skills_over_limit"] == 1
        assert stats["optimal_usage_count"] == 0


# ---------------------------------------------------------------------------
# Tests: get_usage_report
# ---------------------------------------------------------------------------


class TestGetUsageReport:
    """Feature: get_usage_report generates formatted report."""

    @pytest.mark.unit
    def test_report_contains_header(self, tmp_path: Path) -> None:
        """Scenario: Report contains 'Token Usage Report' header."""
        tracker = TokenUsageTracker(tmp_path)
        report = tracker.get_usage_report()
        assert "Token Usage Report" in report

    @pytest.mark.unit
    def test_report_contains_summary(self, tmp_path: Path) -> None:
        """Scenario: Report contains summary section."""
        tracker = TokenUsageTracker(tmp_path)
        report = tracker.get_usage_report()
        assert "Total Skills" in report

    @pytest.mark.unit
    def test_report_is_string(self, skills_dir_with_skill: Path) -> None:
        """Scenario: Report is a string regardless of content."""
        tracker = TokenUsageTracker(skills_dir_with_skill)
        report = tracker.get_usage_report()
        assert isinstance(report, str)


# ---------------------------------------------------------------------------
# Tests: optimize_suggestions
# ---------------------------------------------------------------------------


class TestOptimizeSuggestions:
    """Feature: optimize_suggestions generates optimization hints."""

    @pytest.mark.unit
    def test_no_skills_returns_general_suggestions(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns general suggestions list."""
        tracker = TokenUsageTracker(tmp_path)
        suggestions = tracker.optimize_suggestions()
        assert isinstance(suggestions, list)

    @pytest.mark.unit
    def test_within_limit_returns_optimal_message(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: Skills within limits return positive message.
        Given small skills within optimal token limit
        When optimize_suggestions called with no skill_name
        Then a message about optimal limits is included
        """
        tracker = TokenUsageTracker(skills_dir_with_skill, optimal_limit=100000)
        suggestions = tracker.optimize_suggestions()
        assert any("optimal" in s.lower() for s in suggestions)

    @pytest.mark.unit
    def test_single_skill_name_not_found_returns_not_found(
        self, tmp_path: Path
    ) -> None:
        """Scenario: optimize_suggestions for non-existent skill returns message."""
        tracker = TokenUsageTracker(tmp_path)
        suggestions = tracker.optimize_suggestions("nonexistent-skill")
        assert any("not found" in s.lower() for s in suggestions)

    @pytest.mark.unit
    def test_single_skill_within_limit_returns_optimal(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: Single small skill within limit returns optimal message."""
        tracker = TokenUsageTracker(skills_dir_with_skill, optimal_limit=100000)
        suggestions = tracker.optimize_suggestions("my-skill")
        assert any("optimal" in s.lower() for s in suggestions)

    @pytest.mark.unit
    def test_single_skill_over_limit_returns_reduction_message(
        self, skills_dir_with_skill: Path
    ) -> None:
        """Scenario: Large skill over limit returns reduction suggestion."""
        tracker = TokenUsageTracker(skills_dir_with_skill, optimal_limit=1)
        suggestions = tracker.optimize_suggestions("my-skill")
        assert len(suggestions) > 0

    @pytest.mark.unit
    def test_over_limit_suggests_modularization(
        self, skills_dir_large_skill: Path
    ) -> None:
        """Scenario: Over-limit skills get modularization suggestions."""
        tracker = TokenUsageTracker(skills_dir_large_skill, optimal_limit=10)
        suggestions = tracker.optimize_suggestions()
        assert len(suggestions) > 0
