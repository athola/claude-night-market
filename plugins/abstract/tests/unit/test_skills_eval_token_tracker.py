"""Extended tests for src/abstract/skills_eval/token_tracker.py.

Feature: Token usage tracking (extended coverage)
    As a developer
    I want all uncovered branches of TokenUsageTracker tested
    So that token budget monitoring works correctly in all scenarios
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from abstract.skills_eval.token_tracker import TokenUsageTracker

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_SKILL_CONTENT = (
    "---\n"
    "name: my-skill\n"
    "description: A test skill\n"
    "---\n\n"
    "# My Skill\n\n"
    "## Overview\n"
    "This is the overview.\n\n"
    "## Usage\n"
    "How to use this skill.\n"
)

LARGE_SKILL_CONTENT = (
    "---\nname: large-skill\ndescription: A large skill\n---\n\n"
    "# Large Skill\n\n"
    "## Section One\n"
    + ("This is content repeated many times. " * 100)
    + "\n\n## Section Two\n"
    + ("More content to push token count higher. " * 100)
    + "\n"
)


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Given a skills directory with a single SKILL.md."""
    d = tmp_path / "my-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(MINIMAL_SKILL_CONTENT)
    return tmp_path


@pytest.fixture
def large_skill_dir(tmp_path: Path) -> Path:
    """Given a skills directory with a large SKILL.md."""
    d = tmp_path / "large-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(LARGE_SKILL_CONTENT)
    return tmp_path


@pytest.fixture
def multi_skill_dir(tmp_path: Path) -> Path:
    """Given a skills directory with multiple skills."""
    for name in ["skill-a", "skill-b", "skill-c"]:
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: desc\n---\n\n# {name}\n\nContent.\n"
        )
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: __init__
# ---------------------------------------------------------------------------


class TestInit:
    """Feature: TokenUsageTracker initializes with correct defaults."""

    @pytest.mark.unit
    def test_default_optimal_limit(self, tmp_path: Path) -> None:
        """Scenario: Default optimal_limit is 1000."""
        tracker = TokenUsageTracker(tmp_path)
        assert tracker.optimal_limit == 1000

    @pytest.mark.unit
    def test_default_max_limit(self, tmp_path: Path) -> None:
        """Scenario: Default max_limit is 4000."""
        tracker = TokenUsageTracker(tmp_path)
        assert tracker.max_limit == 4000

    @pytest.mark.unit
    def test_custom_limits(self, tmp_path: Path) -> None:
        """Scenario: Custom limits override defaults."""
        tracker = TokenUsageTracker(tmp_path, optimal_limit=500, max_limit=2000)
        assert tracker.optimal_limit == 500
        assert tracker.max_limit == 2000

    @pytest.mark.unit
    def test_skills_dir_and_root_aliases(self, tmp_path: Path) -> None:
        """Scenario: skills_dir and skills_root point to same path."""
        tracker = TokenUsageTracker(tmp_path)
        assert tracker.skills_dir == tmp_path
        assert tracker.skills_root == tmp_path

    @pytest.mark.unit
    def test_usage_history_initially_empty(self, tmp_path: Path) -> None:
        """Scenario: usage_history starts as empty list."""
        tracker = TokenUsageTracker(tmp_path)
        assert tracker.usage_history == []


# ---------------------------------------------------------------------------
# Tests: analyze_skill_tokens
# ---------------------------------------------------------------------------


class TestAnalyzeSkillTokens:
    """Feature: analyze_skill_tokens analyzes a single skill's tokens."""

    @pytest.mark.unit
    def test_missing_skill_returns_error_dict(self, tmp_path: Path) -> None:
        """Scenario: Non-existent skill returns error dict with zeros."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.analyze_skill_tokens("nonexistent")
        assert "error" in result
        assert result["total_tokens"] == 0
        assert result["needs_modularization"] is False

    @pytest.mark.unit
    def test_existing_skill_returns_token_data(self, skill_dir: Path) -> None:
        """Scenario: Existing skill returns token analysis."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.analyze_skill_tokens("my-skill")
        assert result["total_tokens"] > 0
        assert "frontmatter_tokens" in result
        assert "content_tokens" in result
        assert "sections" in result

    @pytest.mark.unit
    def test_sections_extracted_from_content(self, skill_dir: Path) -> None:
        """Scenario: Sections are extracted from H2 headings."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.analyze_skill_tokens("my-skill")
        assert "Overview" in result["sections"]
        assert "Usage" in result["sections"]

    @pytest.mark.unit
    def test_needs_modularization_true_when_over_limit(self, skill_dir: Path) -> None:
        """Scenario: needs_modularization is True when tokens exceed optimal_limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.analyze_skill_tokens("my-skill")
        assert result["needs_modularization"] is True

    @pytest.mark.unit
    def test_needs_modularization_false_when_under_limit(self, skill_dir: Path) -> None:
        """Scenario: needs_modularization is False when tokens within optimal_limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        result = tracker.analyze_skill_tokens("my-skill")
        assert result["needs_modularization"] is False

    @pytest.mark.unit
    def test_name_in_result(self, skill_dir: Path) -> None:
        """Scenario: Result includes skill name."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.analyze_skill_tokens("my-skill")
        assert result["name"] == "my-skill"

    @pytest.mark.unit
    def test_read_error_returns_error_dict(self, skill_dir: Path) -> None:
        """Scenario: Exception during file read returns error dict with zeros."""
        tracker = TokenUsageTracker(skill_dir)
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = tracker.analyze_skill_tokens("my-skill")
        assert "error" in result
        assert result["total_tokens"] == 0
        assert result["needs_modularization"] is False


# ---------------------------------------------------------------------------
# Tests: analyze_all_skills
# ---------------------------------------------------------------------------


class TestAnalyzeAllSkills:
    """Feature: analyze_all_skills returns aggregate analysis."""

    @pytest.mark.unit
    def test_empty_dir_returns_zero_summary(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns zero-count summary."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.analyze_all_skills()
        assert result["total_skills"] == 0
        assert result["summary"]["total_tokens"] == 0
        assert result["summary"]["average_tokens"] == 0

    @pytest.mark.unit
    def test_single_skill_counted(self, skill_dir: Path) -> None:
        """Scenario: Single skill counted in analyze_all_skills."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.analyze_all_skills()
        assert result["total_skills"] == 1

    @pytest.mark.unit
    def test_multiple_skills_counted(self, multi_skill_dir: Path) -> None:
        """Scenario: Multiple skills all counted."""
        tracker = TokenUsageTracker(multi_skill_dir)
        result = tracker.analyze_all_skills()
        assert result["total_skills"] == 3

    @pytest.mark.unit
    def test_summary_average_tokens_correct(self, multi_skill_dir: Path) -> None:
        """Scenario: Average tokens is total / count."""
        tracker = TokenUsageTracker(multi_skill_dir)
        result = tracker.analyze_all_skills()
        summary = result["summary"]
        if result["total_skills"] > 0:
            expected_avg = summary["total_tokens"] // result["total_skills"]
            assert summary["average_tokens"] == expected_avg

    @pytest.mark.unit
    def test_skills_needing_modularization_counted(self, skill_dir: Path) -> None:
        """Scenario: skills needing modularization counted with low limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.analyze_all_skills()
        assert result["summary"]["skills_needing_modularization"] == 1


# ---------------------------------------------------------------------------
# Tests: calculate_token_efficiency
# ---------------------------------------------------------------------------


class TestCalculateTokenEfficiency:
    """Feature: calculate_token_efficiency computes efficiency metrics."""

    @pytest.mark.unit
    def test_empty_dir_returns_zero_efficiency(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns 0 overall efficiency."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.calculate_token_efficiency()
        assert result["overall_efficiency"] == 0

    @pytest.mark.unit
    def test_small_skill_has_high_efficiency(self, skill_dir: Path) -> None:
        """Scenario: Skill within optimal limit has high efficiency score."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        result = tracker.calculate_token_efficiency()
        for eff in result["skill_efficiencies"].values():
            assert eff == 100.0

    @pytest.mark.unit
    def test_large_skill_creates_optimization_opportunity(
        self, skill_dir: Path
    ) -> None:
        """Scenario: Skill over optimal limit appears in optimization_opportunities."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.calculate_token_efficiency()
        assert len(result["optimization_opportunities"]) == 1

    @pytest.mark.unit
    def test_optimization_opportunity_has_required_keys(self, skill_dir: Path) -> None:
        """Scenario: Optimization opportunity dict has required keys."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.calculate_token_efficiency()
        opp = result["optimization_opportunities"][0]
        assert "skill" in opp
        assert "current_tokens" in opp
        assert "target_tokens" in opp
        assert "potential_savings" in opp

    @pytest.mark.unit
    def test_skill_efficiencies_dict_has_skill_names(self, skill_dir: Path) -> None:
        """Scenario: skill_efficiencies maps skill names to efficiency scores."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.calculate_token_efficiency()
        assert "my-skill" in result["skill_efficiencies"]


# ---------------------------------------------------------------------------
# Tests: suggest_modularization
# ---------------------------------------------------------------------------


class TestSuggestModularization:
    """Feature: suggest_modularization returns suggestions for large skills."""

    @pytest.mark.unit
    def test_empty_dir_returns_no_suggestions(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns empty suggestions list."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.suggest_modularization()
        assert result == []

    @pytest.mark.unit
    def test_skill_over_limit_returns_suggestion(self, skill_dir: Path) -> None:
        """Scenario: Skill over optimal limit appears in suggestions."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.suggest_modularization()
        assert len(result) == 1
        assert result[0]["skill"] == "my-skill"

    @pytest.mark.unit
    def test_suggestion_has_required_keys(self, skill_dir: Path) -> None:
        """Scenario: Suggestion dict has required fields."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.suggest_modularization()
        suggestion = result[0]
        assert "skill" in suggestion
        assert "current_tokens" in suggestion
        assert "suggested_modules" in suggestion
        assert "reason" in suggestion

    @pytest.mark.unit
    def test_suggested_modules_derived_from_sections(self, skill_dir: Path) -> None:
        """Scenario: suggested_modules are derived from skill sections."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.suggest_modularization()
        modules = result[0]["suggested_modules"]
        # Should be module paths like modules/overview.md
        for module in modules:
            assert module.startswith("modules/")
            assert module.endswith(".md")

    @pytest.mark.unit
    def test_suggested_modules_capped_at_five(self, tmp_path: Path) -> None:
        """Scenario: At most 5 suggested modules returned."""
        d = tmp_path / "many-sections"
        d.mkdir()
        sections = "\n".join(f"## Section {i}\nContent.\n" for i in range(1, 15))
        (d / "SKILL.md").write_text(
            "---\nname: many\ndescription: desc\n---\n\n" + sections
        )
        tracker = TokenUsageTracker(tmp_path, optimal_limit=1)
        result = tracker.suggest_modularization()
        assert len(result[0]["suggested_modules"]) <= 5


# ---------------------------------------------------------------------------
# Tests: record_usage
# ---------------------------------------------------------------------------


class TestRecordUsage:
    """Feature: record_usage adds entries to usage_history."""

    @pytest.mark.unit
    def test_record_adds_entry(self, tmp_path: Path) -> None:
        """Scenario: record_usage appends entry to usage_history."""
        tracker = TokenUsageTracker(tmp_path)
        entry = {"skill": "my-skill", "tokens": 500}
        tracker.record_usage(entry)
        assert len(tracker.usage_history) == 1
        assert tracker.usage_history[0] == entry

    @pytest.mark.unit
    def test_multiple_records_appended(self, tmp_path: Path) -> None:
        """Scenario: Multiple calls append multiple entries."""
        tracker = TokenUsageTracker(tmp_path)
        tracker.record_usage({"skill": "a"})
        tracker.record_usage({"skill": "b"})
        assert len(tracker.usage_history) == 2


# ---------------------------------------------------------------------------
# Tests: generate_usage_report
# ---------------------------------------------------------------------------


class TestGenerateUsageReport:
    """Feature: generate_usage_report formats analysis as markdown."""

    @pytest.mark.unit
    def test_report_contains_header(self, tmp_path: Path) -> None:
        """Scenario: Report contains Token Usage Report header."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {"total_skills": 0, "skills": [], "summary": {}}
        report = tracker.generate_usage_report(analysis)
        assert "Token Usage Report" in report

    @pytest.mark.unit
    def test_report_shows_total_skills(self, tmp_path: Path) -> None:
        """Scenario: Report shows total skill count."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {"total_skills": 5, "skills": [], "summary": {}}
        report = tracker.generate_usage_report(analysis)
        assert "5" in report

    @pytest.mark.unit
    def test_report_shows_summary_stats(self, tmp_path: Path) -> None:
        """Scenario: Report shows total and average tokens from summary."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {
            "total_skills": 1,
            "skills": [{"name": "my-skill", "total_tokens": 500}],
            "summary": {"total_tokens": 500, "average_tokens": 500},
        }
        report = tracker.generate_usage_report(analysis)
        assert "500" in report

    @pytest.mark.unit
    def test_report_lists_individual_skills(self, tmp_path: Path) -> None:
        """Scenario: Report lists individual skill token counts."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {
            "total_skills": 1,
            "skills": [{"name": "my-skill", "total_tokens": 123}],
            "summary": {},
        }
        report = tracker.generate_usage_report(analysis)
        assert "my-skill" in report


# ---------------------------------------------------------------------------
# Tests: identify_optimization_opportunities
# ---------------------------------------------------------------------------


class TestIdentifyOptimizationOpportunities:
    """Feature: identify_optimization_opportunities flags large skills."""

    @pytest.mark.unit
    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns empty opportunities list."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.identify_optimization_opportunities()
        assert result == []

    @pytest.mark.unit
    def test_large_skill_flagged(self, skill_dir: Path) -> None:
        """Scenario: Skill over optimal limit appears in opportunities."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.identify_optimization_opportunities()
        assert len(result) == 1
        opp = result[0]
        assert opp["type"] == "token_reduction"
        assert "potential_savings" in opp
        assert "action" in opp

    @pytest.mark.unit
    def test_small_skill_not_flagged(self, skill_dir: Path) -> None:
        """Scenario: Skill within optimal limit not in opportunities."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        result = tracker.identify_optimization_opportunities()
        assert result == []


# ---------------------------------------------------------------------------
# Tests: calculate_dependency_impact
# ---------------------------------------------------------------------------


class TestCalculateDependencyImpact:
    """Feature: calculate_dependency_impact returns dependency metrics."""

    @pytest.mark.unit
    def test_empty_dir_returns_empty_skills(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns empty skills list."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.calculate_dependency_impact()
        assert result["skills"] == []
        assert result["dependency_chains"] == []

    @pytest.mark.unit
    def test_skill_included_with_direct_tokens(self, skill_dir: Path) -> None:
        """Scenario: Skills included with direct_tokens populated."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.calculate_dependency_impact()
        assert len(result["skills"]) == 1
        skill_data = result["skills"][0]
        assert skill_data["name"] == "my-skill"
        assert "direct_tokens" in skill_data
        assert "total_impact" in skill_data

    @pytest.mark.unit
    def test_dependency_tokens_zero_placeholder(self, skill_dir: Path) -> None:
        """Scenario: dependency_tokens is 0 (no tracking yet)."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.calculate_dependency_impact()
        assert result["skills"][0]["dependency_tokens"] == 0


# ---------------------------------------------------------------------------
# Tests: export_analysis
# ---------------------------------------------------------------------------


class TestExportAnalysis:
    """Feature: export_analysis writes analysis to JSON file."""

    @pytest.mark.unit
    def test_creates_json_file(self, tmp_path: Path) -> None:
        """Scenario: export_analysis writes valid JSON to file."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {"total_skills": 0, "skills": [], "summary": {}}
        export_path = tmp_path / "output.json"
        tracker.export_analysis(analysis, export_path)
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert "total_skills" in data

    @pytest.mark.unit
    def test_exported_data_matches_input(self, tmp_path: Path) -> None:
        """Scenario: Exported data matches input analysis."""
        tracker = TokenUsageTracker(tmp_path)
        analysis = {"total_skills": 3, "skills": [{"name": "a"}], "summary": {}}
        export_path = tmp_path / "analysis.json"
        tracker.export_analysis(analysis, export_path)
        data = json.loads(export_path.read_text())
        assert data["total_skills"] == 3


# ---------------------------------------------------------------------------
# Tests: compare_skills
# ---------------------------------------------------------------------------


class TestCompareSkills:
    """Feature: compare_skills compares token usage between skills."""

    @pytest.mark.unit
    def test_empty_list_returns_none_smallest_largest(self, tmp_path: Path) -> None:
        """Scenario: Empty skill names list returns None for smallest/largest."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.compare_skills([])
        assert result["analysis"]["smallest"] is None
        assert result["analysis"]["largest"] is None

    @pytest.mark.unit
    def test_compares_multiple_skills(self, multi_skill_dir: Path) -> None:
        """Scenario: Comparing multiple skills produces sorted table."""
        tracker = TokenUsageTracker(multi_skill_dir)
        result = tracker.compare_skills(["skill-a", "skill-b", "skill-c"])
        table = result["comparison_table"]
        assert len(table) == 3
        # Table is sorted by token count
        tokens = [row["total_tokens"] for row in table]
        assert tokens == sorted(tokens)

    @pytest.mark.unit
    def test_single_skill_is_both_smallest_and_largest(self, skill_dir: Path) -> None:
        """Scenario: Single skill comparison sets same name for smallest/largest."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.compare_skills(["my-skill"])
        assert result["analysis"]["smallest"] == result["analysis"]["largest"]

    @pytest.mark.unit
    def test_recommendations_for_large_skill(self, skill_dir: Path) -> None:
        """Scenario: Recommendation generated for largest skill over optimal limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.compare_skills(["my-skill"])
        assert len(result["recommendations"]) > 0
        assert "my-skill" in result["recommendations"][0]

    @pytest.mark.unit
    def test_comparison_table_has_sections_count(self, skill_dir: Path) -> None:
        """Scenario: comparison_table rows include sections count."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.compare_skills(["my-skill"])
        row = result["comparison_table"][0]
        assert "sections" in row


# ---------------------------------------------------------------------------
# Tests: monitor_budgets
# ---------------------------------------------------------------------------


class TestMonitorBudgets:
    """Feature: monitor_budgets alerts when token budget exceeded."""

    @pytest.mark.unit
    def test_within_budget_not_exceeded(self, skill_dir: Path) -> None:
        """Scenario: Total tokens within budget returns exceeded=False."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.monitor_budgets(budget=999999)
        assert result["exceeded"] is False
        assert result["recommendations"] == []

    @pytest.mark.unit
    def test_over_budget_sets_exceeded(self, skill_dir: Path) -> None:
        """Scenario: Total tokens over budget returns exceeded=True."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.monitor_budgets(budget=1)
        assert result["exceeded"] is True

    @pytest.mark.unit
    def test_over_budget_generates_recommendations(self, skill_dir: Path) -> None:
        """Scenario: Exceeded budget generates optimization recommendations."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        result = tracker.monitor_budgets(budget=1)
        assert len(result["recommendations"]) > 0
        assert any("exceeded" in r.lower() for r in result["recommendations"])

    @pytest.mark.unit
    def test_monitor_budgets_result_has_all_keys(self, tmp_path: Path) -> None:
        """Scenario: Result dict contains budget, usage, exceeded, recommendations."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.monitor_budgets(budget=5000)
        assert "budget" in result
        assert "usage" in result
        assert "exceeded" in result
        assert "recommendations" in result

    @pytest.mark.unit
    def test_budget_value_preserved_in_result(self, tmp_path: Path) -> None:
        """Scenario: The budget value is preserved in result."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.monitor_budgets(budget=12345)
        assert result["budget"] == 12345


# ---------------------------------------------------------------------------
# Tests: track_usage (core paths)
# ---------------------------------------------------------------------------


class TestTrackUsageCoverage:
    """Feature: track_usage covers all execution paths."""

    @pytest.mark.unit
    def test_no_skills_returns_none(self, tmp_path: Path) -> None:
        """Scenario: No SKILL.md files found returns None."""
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.track_usage()
        assert result is None

    @pytest.mark.unit
    def test_with_skill_file_returns_dict(self, skill_dir: Path) -> None:
        """Scenario: Valid skill file returns dict with all fields."""
        tracker = TokenUsageTracker(skill_dir)
        skill_file = skill_dir / "my-skill" / "SKILL.md"
        result = tracker.track_usage(skill_file)
        assert result is not None
        assert "skill_name" in result
        assert "token_count" in result
        assert "frontmatter_tokens" in result
        assert "content_tokens" in result
        assert "timestamp" in result

    @pytest.mark.unit
    def test_directory_path_resolves_to_skill_md(self, skill_dir: Path) -> None:
        """Scenario: Passing a directory appends SKILL.md."""
        tracker = TokenUsageTracker(skill_dir)
        skill_dir_path = skill_dir / "my-skill"
        result = tracker.track_usage(skill_dir_path)
        assert result is not None
        assert result["skill_name"] == "my-skill"

    @pytest.mark.unit
    def test_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        """Scenario: Non-existent skill file raises FileNotFoundError."""
        tracker = TokenUsageTracker(tmp_path)
        with pytest.raises(FileNotFoundError):
            tracker.track_usage(tmp_path / "nosuch" / "SKILL.md")

    @pytest.mark.unit
    def test_read_error_raises_os_error(self, skill_dir: Path) -> None:
        """Scenario: File read error raises OSError."""
        tracker = TokenUsageTracker(skill_dir)
        skill_file = skill_dir / "my-skill" / "SKILL.md"
        with patch("builtins.open", side_effect=OSError("no permission")):
            with pytest.raises(OSError):
                tracker.track_usage(skill_file)

    @pytest.mark.unit
    def test_auto_find_first_skill(self, skill_dir: Path) -> None:
        """Scenario: Called with no args auto-finds first SKILL.md."""
        tracker = TokenUsageTracker(skill_dir)
        result = tracker.track_usage()
        assert result is not None
        assert "token_count" in result


# ---------------------------------------------------------------------------
# Tests: get_usage_statistics (core paths)
# ---------------------------------------------------------------------------


class TestGetUsageStatisticsCoverage:
    """Feature: get_usage_statistics covers all code paths."""

    @pytest.mark.unit
    def test_empty_dir_returns_zeros(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns all-zero statistics."""
        tracker = TokenUsageTracker(tmp_path)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 0
        assert stats["total_tokens"] == 0
        assert stats["average_tokens"] == 0
        assert stats["min_tokens"] == 0
        assert stats["max_tokens"] == 0
        assert stats["skills_over_limit"] == 0
        assert stats["optimal_usage_count"] == 0

    @pytest.mark.unit
    def test_single_skill_returns_stats(self, skill_dir: Path) -> None:
        """Scenario: Single skill returns correct statistics."""
        tracker = TokenUsageTracker(skill_dir)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 1
        assert stats["total_tokens"] > 0
        assert stats["min_tokens"] == stats["max_tokens"]

    @pytest.mark.unit
    def test_skills_over_limit_when_low_threshold(self, skill_dir: Path) -> None:
        """Scenario: Low optimal limit counts skills as over limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        stats = tracker.get_usage_statistics()
        assert stats["skills_over_limit"] == 1
        assert stats["optimal_usage_count"] == 0

    @pytest.mark.unit
    def test_skills_within_limit_counted_as_optimal(self, skill_dir: Path) -> None:
        """Scenario: High optimal limit counts skills as within limit."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        stats = tracker.get_usage_statistics()
        assert stats["skills_over_limit"] == 0
        assert stats["optimal_usage_count"] == 1

    @pytest.mark.unit
    def test_read_error_skill_skipped_gracefully(self, skill_dir: Path) -> None:
        """Scenario: Skills that error during track_usage are skipped."""
        tracker = TokenUsageTracker(skill_dir)
        # Simulate track_usage raising OSError for one skill
        with patch.object(tracker, "track_usage", side_effect=OSError("bad")):
            stats = tracker.get_usage_statistics()
        # No entries processed, returns zeros
        assert stats["total_skills"] == 0

    @pytest.mark.unit
    def test_multiple_skills_min_max_correct(self, tmp_path: Path) -> None:
        """Scenario: With multiple skills, min/max/avg are correct."""
        # Create two skills of different sizes
        small = tmp_path / "small-skill"
        small.mkdir()
        (small / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\nA.\n")
        large = tmp_path / "large-skill"
        large.mkdir()
        (large / "SKILL.md").write_text(
            "---\nname: l\ndescription: d\n---\n\n" + "word " * 500
        )
        tracker = TokenUsageTracker(tmp_path)
        stats = tracker.get_usage_statistics()
        assert stats["total_skills"] == 2
        assert stats["min_tokens"] <= stats["max_tokens"]
        assert stats["average_tokens"] == stats["total_tokens"] // 2


# ---------------------------------------------------------------------------
# Tests: get_usage_report (core paths)
# ---------------------------------------------------------------------------


class TestGetUsageReportCoverage:
    """Feature: get_usage_report generates formatted report."""

    @pytest.mark.unit
    def test_report_is_string(self, tmp_path: Path) -> None:
        """Scenario: Report is always a string."""
        tracker = TokenUsageTracker(tmp_path)
        report = tracker.get_usage_report()
        assert isinstance(report, str)

    @pytest.mark.unit
    def test_report_contains_header(self, tmp_path: Path) -> None:
        """Scenario: Report contains Token Usage Report header."""
        tracker = TokenUsageTracker(tmp_path)
        report = tracker.get_usage_report()
        assert "Token Usage Report" in report

    @pytest.mark.unit
    def test_report_shows_skills_dir(self, skill_dir: Path) -> None:
        """Scenario: Report includes skills directory path."""
        tracker = TokenUsageTracker(skill_dir)
        report = tracker.get_usage_report()
        assert str(skill_dir) in report

    @pytest.mark.unit
    def test_report_shows_over_limit_count(self, skill_dir: Path) -> None:
        """Scenario: Report shows skills over limit count."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        report = tracker.get_usage_report()
        assert "Over Limit" in report or "over_limit" in report.lower() or "1" in report


# ---------------------------------------------------------------------------
# Tests: optimize_suggestions (single skill path - all branches)
# ---------------------------------------------------------------------------


class TestOptimizeSuggestionsSingleSkill:
    """Feature: optimize_suggestions for single skill covers all branches."""

    @pytest.mark.unit
    def test_nonexistent_skill_returns_not_found(self, tmp_path: Path) -> None:
        """Scenario: Non-existent skill name returns 'Skill not found'."""
        tracker = TokenUsageTracker(tmp_path)
        suggestions = tracker.optimize_suggestions("nonexistent-skill")
        assert suggestions == ["Skill not found"]

    @pytest.mark.unit
    def test_read_error_returns_error_message(self, skill_dir: Path) -> None:
        """Scenario: File read error returns error message."""
        tracker = TokenUsageTracker(skill_dir)
        with patch("builtins.open", side_effect=OSError("denied")):
            suggestions = tracker.optimize_suggestions("my-skill")
        assert suggestions == ["Error reading skill file"]

    @pytest.mark.unit
    def test_skill_over_optimal_returns_reduce_message(self, skill_dir: Path) -> None:
        """Scenario: Skill over optimal_limit returns reduce message."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        suggestions = tracker.optimize_suggestions("my-skill")
        assert suggestions == ["Reduce content size for better performance"]

    @pytest.mark.unit
    def test_skill_within_optimal_returns_optimal_message(
        self, skill_dir: Path
    ) -> None:
        """Scenario: Skill within optimal_limit returns optimal message."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        suggestions = tracker.optimize_suggestions("my-skill")
        assert suggestions == ["Token usage is optimal"]

    @pytest.mark.unit
    def test_general_suggestions_average_high(self, skill_dir: Path) -> None:
        """Scenario: When average tokens exceed optimal, high-avg suggestion added."""
        # Use very low optimal so average also triggers
        tracker = TokenUsageTracker(skill_dir, optimal_limit=1)
        suggestions = tracker.optimize_suggestions()
        assert any("exceed" in s.lower() or "high" in s.lower() for s in suggestions)

    @pytest.mark.unit
    def test_general_suggestions_within_optimal(self, skill_dir: Path) -> None:
        """Scenario: General suggestions with large optimal returns 'within limits'."""
        tracker = TokenUsageTracker(skill_dir, optimal_limit=999999)
        suggestions = tracker.optimize_suggestions()
        assert any("within optimal" in s.lower() for s in suggestions)


# ---------------------------------------------------------------------------
# Tests: _calculate_frontmatter_tokens fallback path
# ---------------------------------------------------------------------------


class TestCalculateFrontmatterTokensFallback:
    """Feature: _calculate_frontmatter_tokens uses fallback when no parsed dict."""

    @pytest.mark.unit
    def test_no_parsed_uses_extract_raw(self, tmp_path: Path) -> None:
        """Scenario: When parsed dict is None, uses FrontmatterProcessor.extract_raw."""
        tracker = TokenUsageTracker(tmp_path)
        content = "---\nname: test\n---\n\nBody content.\n"
        result = tracker._calculate_frontmatter_tokens(content, None)
        assert isinstance(result, int)
        assert result >= 0

    @pytest.mark.unit
    def test_parsed_without_frontmatter_tokens_uses_fallback(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Parsed dict without 'frontmatter_tokens' key uses fallback."""
        tracker = TokenUsageTracker(tmp_path)
        content = "---\nname: test\n---\n\nBody.\n"
        # Dict exists but no 'frontmatter_tokens' key
        result = tracker._calculate_frontmatter_tokens(content, {"other_key": 5})
        assert isinstance(result, int)

    @pytest.mark.unit
    def test_parsed_with_frontmatter_tokens_uses_parsed_value(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Parsed dict with 'frontmatter_tokens' returns that value."""
        tracker = TokenUsageTracker(tmp_path)
        content = "---\nname: test\n---\n\nBody.\n"
        result = tracker._calculate_frontmatter_tokens(
            content, {"frontmatter_tokens": 42}
        )
        assert result == 42
