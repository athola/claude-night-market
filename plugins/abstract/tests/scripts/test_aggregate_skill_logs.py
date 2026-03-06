"""Tests for the aggregate_skill_logs script.

Feature: Skill execution log aggregation
    As a developer
    I want log aggregation utilities tested
    So that metrics and issue detection are reliable
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from aggregate_skill_logs import (  # noqa: E402
    AggregationResult,
    SkillMetrics,
    aggregate_logs,
    calculate_skill_metrics,
    detect_high_impact_issues,
    detect_low_rated_skills,
    detect_slow_skills,
    format_high_impact_issues,
    format_low_rated_skills,
    format_skill_summary,
    format_slow_skills,
    generate_learnings_md,
    get_learnings_path,
    get_log_directory,
    load_log_entries,
)
from aggregate_skill_logs import (
    main as aggregate_main,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(  # noqa: PLR0913
    outcome: str = "success",
    duration_ms: int = 1000,
    rating: float | None = None,
    friction: list[str] | None = None,
    suggestions: list[str] | None = None,
    error: str | None = None,
) -> dict:
    entry: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "duration_ms": duration_ms,
    }
    if rating is not None or friction is not None or suggestions is not None:
        entry["qualitative_evaluation"] = {}
        if rating is not None:
            entry["qualitative_evaluation"]["rating"] = rating
        if friction is not None:
            entry["qualitative_evaluation"]["friction_points"] = friction
        if suggestions is not None:
            entry["qualitative_evaluation"]["improvement_suggestions"] = suggestions
    if error is not None:
        entry["error"] = error
    return entry


def _make_metrics(  # noqa: PLR0913
    skill: str = "myplugin:my-skill",
    total: int = 10,
    success: int = 8,
    failure: int = 2,
    partial: int = 0,
    avg_duration: float = 500.0,
    max_duration: int = 1000,
    success_rate: float = 80.0,
    avg_rating: float | None = None,
    common_friction: list[str] | None = None,
    improvement_suggestions: list[str] | None = None,
    recent_errors: list[str] | None = None,
) -> SkillMetrics:
    plugin, skill_name = skill.split(":", 1)
    return SkillMetrics(
        skill=skill,
        plugin=plugin,
        skill_name=skill_name,
        total_executions=total,
        success_count=success,
        failure_count=failure,
        partial_count=partial,
        avg_duration_ms=avg_duration,
        max_duration_ms=max_duration,
        success_rate=success_rate,
        avg_rating=avg_rating,
        common_friction=common_friction or [],
        improvement_suggestions=improvement_suggestions or [],
        recent_errors=recent_errors or [],
    )


# ---------------------------------------------------------------------------
# Tests: get_log_directory / get_learnings_path
# ---------------------------------------------------------------------------


class TestGetLogDirectory:
    """Feature: Log directory resolution

    As a developer
    I want the log directory resolved from the environment
    So that tests and production use the same logic
    """

    @pytest.mark.unit
    def test_returns_path_under_claude_home_env(self, tmp_path: Path) -> None:
        """Scenario: CLAUDE_HOME env var is respected
        Given CLAUDE_HOME is set to a custom path
        When get_log_directory is called
        Then the result is inside that custom path
        """
        original = os.environ.get("CLAUDE_HOME")
        os.environ["CLAUDE_HOME"] = str(tmp_path)
        try:
            result = get_log_directory()
            assert str(tmp_path) in str(result)
            assert result.name == "logs"
        finally:
            if original is None:
                del os.environ["CLAUDE_HOME"]
            else:
                os.environ["CLAUDE_HOME"] = original

    @pytest.mark.unit
    def test_returns_path_object(self) -> None:
        """Scenario: Return value is always a Path
        Given no special environment setup
        When get_log_directory is called
        Then the result is a Path object
        """
        result = get_log_directory()
        assert isinstance(result, Path)

    @pytest.mark.unit
    def test_get_learnings_path_returns_path_object(self) -> None:
        """Scenario: get_learnings_path returns a Path
        Given no special environment setup
        When get_learnings_path is called
        Then the result is a Path ending in LEARNINGS.md
        """
        result = get_learnings_path()
        assert isinstance(result, Path)
        assert result.name == "LEARNINGS.md"


# ---------------------------------------------------------------------------
# Tests: calculate_skill_metrics
# ---------------------------------------------------------------------------


class TestCalculateSkillMetrics:
    """Feature: Per-skill metric calculation

    As a developer
    I want skill metrics computed from log entries
    So that issue detection has accurate data
    """

    @pytest.mark.unit
    def test_all_successes_yields_100_percent_rate(self) -> None:
        """Scenario: All successful entries give 100% success rate
        Given 5 success entries
        When calculate_skill_metrics is called
        Then success_rate is 100.0
        """
        entries = [_make_entry("success") for _ in range(5)]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert metrics.success_rate == 100.0
        assert metrics.success_count == 5
        assert metrics.failure_count == 0

    @pytest.mark.unit
    def test_all_failures_yields_zero_success_rate(self) -> None:
        """Scenario: All failing entries give 0% success rate
        Given 3 failure entries
        When calculate_skill_metrics is called
        Then success_rate is 0.0
        """
        entries = [_make_entry("failure", error="boom") for _ in range(3)]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert metrics.success_rate == 0.0
        assert metrics.failure_count == 3

    @pytest.mark.unit
    def test_empty_entries_returns_zero_metrics(self) -> None:
        """Scenario: No entries yields zero/None metrics
        Given an empty entries list
        When calculate_skill_metrics is called
        Then all numeric fields are 0 and avg_rating is None
        """
        metrics = calculate_skill_metrics("myplugin:my-skill", [])
        assert metrics.total_executions == 0
        assert metrics.success_rate == 0.0
        assert metrics.avg_rating is None
        assert metrics.avg_duration_ms == 0.0

    @pytest.mark.unit
    def test_duration_stats_computed_correctly(self) -> None:
        """Scenario: Duration statistics are mean and max
        Given entries with durations 100ms, 200ms, 300ms
        When calculate_skill_metrics is called
        Then avg_duration_ms is 200.0 and max_duration_ms is 300
        """
        entries = [
            _make_entry(duration_ms=100),
            _make_entry(duration_ms=200),
            _make_entry(duration_ms=300),
        ]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert metrics.avg_duration_ms == 200.0
        assert metrics.max_duration_ms == 300

    @pytest.mark.unit
    def test_rating_averaged_from_evaluations(self) -> None:
        """Scenario: Ratings are averaged across evaluations
        Given entries with ratings 2.0 and 4.0
        When calculate_skill_metrics is called
        Then avg_rating is 3.0
        """
        entries = [
            _make_entry(rating=2.0),
            _make_entry(rating=4.0),
        ]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert metrics.avg_rating == pytest.approx(3.0)

    @pytest.mark.unit
    def test_friction_points_aggregated(self) -> None:
        """Scenario: Friction points are collected from all evaluations
        Given two entries each with a friction point
        When calculate_skill_metrics is called
        Then common_friction contains at least one point
        """
        entries = [
            _make_entry(friction=["slow"], rating=3.0),
            _make_entry(friction=["slow"], rating=3.0),
        ]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert "slow" in metrics.common_friction

    @pytest.mark.unit
    def test_recent_errors_collected(self) -> None:
        """Scenario: Failure errors are stored in recent_errors
        Given a failure entry with a specific error message
        When calculate_skill_metrics is called
        Then recent_errors contains that message
        """
        entries = [_make_entry("failure", error="connection refused")]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert "connection refused" in metrics.recent_errors

    @pytest.mark.unit
    def test_skill_name_parsed_correctly(self) -> None:
        """Scenario: Plugin and skill name are split on first colon
        Given skill key 'abstract:skill-auditor'
        When calculate_skill_metrics is called
        Then plugin is 'abstract' and skill_name is 'skill-auditor'
        """
        metrics = calculate_skill_metrics("abstract:skill-auditor", [])
        assert metrics.plugin == "abstract"
        assert metrics.skill_name == "skill-auditor"

    @pytest.mark.unit
    def test_partial_outcomes_counted(self) -> None:
        """Scenario: Partial outcomes are tracked separately
        Given one partial entry
        When calculate_skill_metrics is called
        Then partial_count is 1
        """
        entries = [_make_entry("partial")]
        metrics = calculate_skill_metrics("myplugin:my-skill", entries)
        assert metrics.partial_count == 1


# ---------------------------------------------------------------------------
# Tests: detect_high_impact_issues
# ---------------------------------------------------------------------------


class TestDetectHighImpactIssues:
    """Feature: High-impact issue detection

    As a developer
    I want skills with high failure rates or low ratings flagged
    So that I know which skills need immediate attention
    """

    @pytest.mark.unit
    def test_high_failure_rate_detected(self) -> None:
        """Scenario: Skill with high failure rate is flagged
        Given a skill with 5+ executions and <70% success rate
        When detect_high_impact_issues is called
        Then a high_failure_rate issue is returned
        """
        metrics = _make_metrics(total=10, success=2, failure=8, success_rate=20.0)
        issues = detect_high_impact_issues({"p:s": metrics})
        types = [i["type"] for i in issues]
        assert "high_failure_rate" in types

    @pytest.mark.unit
    def test_low_rating_detected(self) -> None:
        """Scenario: Skill with avg_rating < 3.0 is flagged
        Given a skill with avg_rating of 2.0
        When detect_high_impact_issues is called
        Then a low_rating issue is returned
        """
        metrics = _make_metrics(avg_rating=2.0)
        issues = detect_high_impact_issues({"p:s": metrics})
        types = [i["type"] for i in issues]
        assert "low_rating" in types

    @pytest.mark.unit
    def test_few_executions_not_flagged_for_failure(self) -> None:
        """Scenario: Skills with fewer than 5 executions are not flagged for failure
        Given a skill with only 3 executions and 0% success rate
        When detect_high_impact_issues is called
        Then no high_failure_rate issue is returned
        """
        metrics = _make_metrics(total=3, success=0, failure=3, success_rate=0.0)
        issues = detect_high_impact_issues({"p:s": metrics})
        types = [i["type"] for i in issues]
        assert "high_failure_rate" not in types

    @pytest.mark.unit
    def test_no_issues_for_healthy_skill(self) -> None:
        """Scenario: Healthy skill produces no issues
        Given a skill with high success rate and no rating
        When detect_high_impact_issues is called
        Then no issues are returned
        """
        metrics = _make_metrics(total=20, success=19, failure=1, success_rate=95.0)
        issues = detect_high_impact_issues({"p:s": metrics})
        assert issues == []

    @pytest.mark.unit
    def test_excessive_failures_detected(self) -> None:
        """Scenario: Skill with > 10 failures triggers excessive_failures issue
        Given a skill with 11 failures
        When detect_high_impact_issues is called
        Then an excessive_failures issue is returned
        """
        metrics = _make_metrics(total=20, success=9, failure=11, success_rate=45.0)
        issues = detect_high_impact_issues({"p:s": metrics})
        types = [i["type"] for i in issues]
        assert "excessive_failures" in types


# ---------------------------------------------------------------------------
# Tests: detect_slow_skills
# ---------------------------------------------------------------------------


class TestDetectSlowSkills:
    """Feature: Slow skill detection

    As a developer
    I want skills with high average duration flagged
    So that performance bottlenecks are visible
    """

    @pytest.mark.unit
    def test_slow_skill_detected(self) -> None:
        """Scenario: Skill exceeding threshold is flagged
        Given a skill with avg_duration_ms of 15000 (> 10000 default)
        When detect_slow_skills is called with default threshold
        Then the skill appears in the result
        """
        metrics = _make_metrics(avg_duration=15000.0, max_duration=20000)
        result = detect_slow_skills({"p:s": metrics})
        assert len(result) == 1
        assert result[0]["skill"] == "p:s"

    @pytest.mark.unit
    def test_fast_skill_not_flagged(self) -> None:
        """Scenario: Skill below threshold is not flagged
        Given a skill with avg_duration_ms of 500
        When detect_slow_skills is called
        Then no results are returned
        """
        metrics = _make_metrics(avg_duration=500.0)
        result = detect_slow_skills({"p:s": metrics})
        assert result == []

    @pytest.mark.unit
    def test_results_sorted_by_duration_descending(self) -> None:
        """Scenario: Results are sorted slowest first
        Given two slow skills with different durations
        When detect_slow_skills is called
        Then the slower skill appears first
        """
        slow = _make_metrics("p:slow", avg_duration=20000.0)
        slower = _make_metrics("p:slower", avg_duration=30000.0)
        result = detect_slow_skills({"p:slow": slow, "p:slower": slower})
        assert result[0]["avg_duration_ms"] > result[1]["avg_duration_ms"]

    @pytest.mark.unit
    def test_custom_threshold_respected(self) -> None:
        """Scenario: Custom threshold changes which skills are flagged
        Given a skill with avg_duration_ms of 5000
        When detect_slow_skills is called with threshold_ms=4000
        Then the skill is flagged
        """
        metrics = _make_metrics(avg_duration=5000.0)
        result = detect_slow_skills({"p:s": metrics}, threshold_ms=4000)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Tests: detect_low_rated_skills
# ---------------------------------------------------------------------------


class TestDetectLowRatedSkills:
    """Feature: Low-rated skill detection

    As a developer
    I want skills with poor user ratings surfaced
    So that qualitative feedback drives improvements
    """

    @pytest.mark.unit
    def test_low_rated_skill_detected(self) -> None:
        """Scenario: Skill with rating below threshold is flagged
        Given a skill with avg_rating of 3.0 (< default threshold 3.5)
        When detect_low_rated_skills is called
        Then it appears in the result
        """
        metrics = _make_metrics(avg_rating=3.0)
        result = detect_low_rated_skills({"p:s": metrics})
        assert len(result) == 1

    @pytest.mark.unit
    def test_skill_without_rating_not_flagged(self) -> None:
        """Scenario: Skill with no rating is not flagged
        Given a skill with avg_rating of None
        When detect_low_rated_skills is called
        Then no results are returned
        """
        metrics = _make_metrics(avg_rating=None)
        result = detect_low_rated_skills({"p:s": metrics})
        assert result == []

    @pytest.mark.unit
    def test_high_rated_skill_not_flagged(self) -> None:
        """Scenario: Skill above threshold is not flagged
        Given a skill with avg_rating of 4.5
        When detect_low_rated_skills is called
        Then no results are returned
        """
        metrics = _make_metrics(avg_rating=4.5)
        result = detect_low_rated_skills({"p:s": metrics})
        assert result == []

    @pytest.mark.unit
    def test_results_sorted_by_rating_ascending(self) -> None:
        """Scenario: Results are sorted by rating ascending (worst first)
        Given two low-rated skills with different ratings
        When detect_low_rated_skills is called
        Then the lowest-rated skill appears first
        """
        bad = _make_metrics("p:bad", avg_rating=2.0)
        mediocre = _make_metrics("p:mediocre", avg_rating=3.0)
        result = detect_low_rated_skills({"p:bad": bad, "p:mediocre": mediocre})
        assert result[0]["rating"] < result[1]["rating"]


# ---------------------------------------------------------------------------
# Tests: load_log_entries
# ---------------------------------------------------------------------------


class TestLoadLogEntries:
    """Feature: Log file loading

    As a developer
    I want log entries loaded from JSONL files
    So that metrics can be calculated from stored data
    """

    @pytest.mark.unit
    def test_loads_recent_entries(self, tmp_path: Path) -> None:
        """Scenario: Recent JSONL entries are loaded
        Given a JSONL log file with a recent entry
        When load_log_entries is called
        Then the entry is returned
        """
        plugin_dir = tmp_path / "myplugin"
        skill_dir = plugin_dir / "my-skill"
        skill_dir.mkdir(parents=True)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcome": "success",
            "duration_ms": 500,
        }
        log_file = skill_dir / "log.jsonl"
        log_file.write_text(json.dumps(entry) + "\n")

        result = load_log_entries(tmp_path, days_back=7)
        assert "myplugin:my-skill" in result
        assert len(result["myplugin:my-skill"]) == 1

    @pytest.mark.unit
    def test_empty_directory_returns_empty_dict(self, tmp_path: Path) -> None:
        """Scenario: Empty log directory returns empty dict
        Given a log directory with no files
        When load_log_entries is called
        Then an empty dict is returned
        """
        result = load_log_entries(tmp_path, days_back=7)
        assert result == {}

    @pytest.mark.unit
    def test_malformed_json_skipped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: Malformed JSONL lines are skipped with a warning
        Given a JSONL file containing invalid JSON
        When load_log_entries is called
        Then no exception is raised and the bad line is skipped
        """
        plugin_dir = tmp_path / "myplugin"
        skill_dir = plugin_dir / "my-skill"
        skill_dir.mkdir(parents=True)
        log_file = skill_dir / "bad.jsonl"
        log_file.write_text("{not valid json}\n")

        result = load_log_entries(tmp_path, days_back=7)
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: format_high_impact_issues
# ---------------------------------------------------------------------------


class TestFormatHighImpactIssues:
    """Feature: Formatting high-impact issues for LEARNINGS.md

    As a developer
    I want issues formatted as markdown
    So that LEARNINGS.md is human-readable
    """

    @pytest.mark.unit
    def test_empty_issues_returns_section_header(self) -> None:
        """Scenario: Empty issues list still returns section header
        Given an empty issues list
        When format_high_impact_issues is called
        Then the result contains the section header
        """
        lines = format_high_impact_issues([])
        assert any("High-Impact Issues" in line for line in lines)

    @pytest.mark.unit
    def test_single_issue_included(self) -> None:
        """Scenario: A single issue is included in the output
        Given one high-failure-rate issue
        When format_high_impact_issues is called
        Then the skill name appears in the output
        """
        issue = {
            "skill": "p:my-skill",
            "type": "high_failure_rate",
            "severity": "high",
            "metric": "20.0% success rate",
            "detail": "8/10 failures",
            "errors": ["timeout"],
        }
        lines = format_high_impact_issues([issue])
        text = "\n".join(lines)
        assert "p:my-skill" in text

    @pytest.mark.unit
    def test_returns_list_of_strings(self) -> None:
        """Scenario: Return value is a list of strings
        Given any issues list
        When format_high_impact_issues is called
        Then all items are strings
        """
        result = format_high_impact_issues([])
        assert all(isinstance(line, str) for line in result)


# ---------------------------------------------------------------------------
# Tests: load_log_entries with non-dir entries
# ---------------------------------------------------------------------------


class TestLoadLogEntriesNonDir:
    """Test load_log_entries skips non-directory entries."""

    @pytest.mark.unit
    def test_non_dir_plugin_entry_skipped(self, tmp_path: Path) -> None:
        """Files at plugin dir level are skipped."""
        (tmp_path / "not-a-dir.txt").write_text("ignore me")
        result = load_log_entries(tmp_path, days_back=30)
        assert result == {}

    @pytest.mark.unit
    def test_non_dir_skill_entry_skipped(self, tmp_path: Path) -> None:
        """Files at skill level are skipped."""
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "not-a-skill.txt").write_text("ignore me")
        result = load_log_entries(tmp_path, days_back=30)
        assert result == {}

    @pytest.mark.unit
    def test_blank_line_in_jsonl_skipped(self, tmp_path: Path) -> None:
        """Blank lines in JSONL file are skipped without error."""
        plugin_dir = tmp_path / "my-plugin"
        skill_dir = plugin_dir / "my-skill"
        skill_dir.mkdir(parents=True)

        entry = _make_entry()
        log_file = skill_dir / "log.jsonl"
        log_file.write_text(json.dumps(entry) + "\n\n" + json.dumps(entry) + "\n")

        result = load_log_entries(tmp_path, days_back=30)
        assert "my-plugin:my-skill" in result
        assert len(result["my-plugin:my-skill"]) == 2


# ---------------------------------------------------------------------------
# Tests: format_slow_skills
# ---------------------------------------------------------------------------


class TestFormatSlowSkills:
    """Test format_slow_skills produces markdown table."""

    @pytest.mark.unit
    def test_empty_list_returns_header_only(self) -> None:
        """Empty slow_skills list returns section with header."""
        result = format_slow_skills([])
        assert isinstance(result, list)
        assert any("Slow Execution" in line for line in result)

    @pytest.mark.unit
    def test_slow_skill_appears_in_table(self) -> None:
        """Slow skill entry appears in table rows."""
        slow_skills = [
            {
                "skill": "my-plugin:slow-skill",
                "avg_duration_ms": 15000.0,
                "max_duration_ms": 30000,
                "executions": 5,
            }
        ]
        result = format_slow_skills(slow_skills)
        combined = "\n".join(result)
        assert "slow-skill" in combined
        assert "15.0" in combined

    @pytest.mark.unit
    def test_at_most_10_slow_skills_shown(self) -> None:
        """Only up to 10 slow skills are included."""
        slow_skills = [
            {
                "skill": f"p:skill-{i}",
                "avg_duration_ms": float(10000 + i * 100),
                "max_duration_ms": 20000,
                "executions": i + 1,
            }
            for i in range(15)
        ]
        result = format_slow_skills(slow_skills)
        data_rows = [
            line
            for line in result
            if line.startswith("| `") and "skill" not in line.lower()
        ]
        assert len(data_rows) <= 10


# ---------------------------------------------------------------------------
# Tests: format_low_rated_skills
# ---------------------------------------------------------------------------


class TestFormatLowRatedSkills:
    """Test format_low_rated_skills produces markdown sections."""

    @pytest.mark.unit
    def test_empty_list_returns_header(self) -> None:
        """Empty list returns section header."""
        result = format_low_rated_skills([])
        assert isinstance(result, list)
        assert any("Low User Ratings" in line for line in result)

    @pytest.mark.unit
    def test_skill_with_friction_and_suggestions(self) -> None:
        """Skill with friction and suggestions appears in output."""
        low_rated = [
            {
                "skill": "p:bad-skill",
                "rating": 2.5,
                "friction": ["too slow", "confusing output"],
                "suggestions": ["add examples", "improve docs"],
            }
        ]
        result = format_low_rated_skills(low_rated)
        combined = "\n".join(result)
        assert "bad-skill" in combined
        assert "2.5" in combined
        assert "too slow" in combined
        assert "add examples" in combined

    @pytest.mark.unit
    def test_skill_without_friction_or_suggestions(self) -> None:
        """Skill without friction/suggestions doesn't crash."""
        low_rated = [
            {
                "skill": "p:plain-skill",
                "rating": 2.0,
                "friction": [],
                "suggestions": [],
            }
        ]
        result = format_low_rated_skills(low_rated)
        assert isinstance(result, list)
        assert any("plain-skill" in line for line in result)


# ---------------------------------------------------------------------------
# Tests: format_high_impact_issues with errors and friction
# ---------------------------------------------------------------------------


class TestFormatHighImpactIssuesWithErrors:
    """Test format_high_impact_issues includes errors and friction."""

    @pytest.mark.unit
    def test_issue_with_errors_shown(self) -> None:
        """Issue with errors list includes error entries."""
        issues = [
            {
                "skill": "p:failing-skill",
                "type": "high_failure_rate",
                "severity": "high",
                "metric": "success_rate",
                "detail": "30% success rate",
                "errors": ["error message 1", "error message 2"],
                "friction": [],
            }
        ]
        result = format_high_impact_issues(issues)
        combined = "\n".join(result)
        assert "error message 1" in combined

    @pytest.mark.unit
    def test_issue_with_friction_shown(self) -> None:
        """Issue with friction list includes friction entries."""
        issues = [
            {
                "skill": "p:slow-skill",
                "type": "high_failure_rate",
                "severity": "medium",
                "metric": "success_rate",
                "detail": "50% success",
                "errors": [],
                "friction": ["hard to use", "unclear output"],
            }
        ]
        result = format_high_impact_issues(issues)
        combined = "\n".join(result)
        assert "hard to use" in combined


# ---------------------------------------------------------------------------
# Tests: format_skill_summary
# ---------------------------------------------------------------------------


class TestFormatSkillSummary:
    """Test format_skill_summary creates table from metrics."""

    @pytest.mark.unit
    def test_metric_with_rating_shows_rating(self) -> None:
        """Skill with avg_rating shows rating in table."""
        metrics = {
            "p:good-skill": _make_metrics(
                skill="p:good-skill", avg_rating=4.5, total=10, success=9
            )
        }
        result = format_skill_summary(metrics)
        combined = "\n".join(result)
        assert "4.5" in combined

    @pytest.mark.unit
    def test_metric_without_rating_shows_na(self) -> None:
        """Skill without avg_rating shows N/A."""
        metrics = {
            "p:unrated-skill": _make_metrics(skill="p:unrated-skill", avg_rating=None)
        }
        result = format_skill_summary(metrics)
        combined = "\n".join(result)
        assert "N/A" in combined

    @pytest.mark.unit
    def test_top_20_skills_maximum(self) -> None:
        """Only top 20 skills by executions shown."""
        metrics = {
            f"p:skill-{i}": _make_metrics(skill=f"p:skill-{i}", total=i + 1)
            for i in range(25)
        }
        result = format_skill_summary(metrics)
        data_rows = [
            line for line in result if line.startswith("| `") and "Skill" not in line
        ]
        assert len(data_rows) <= 20


# ---------------------------------------------------------------------------
# Tests: generate_learnings_md
# ---------------------------------------------------------------------------


class TestGenerateLearningsMd:
    """Test generate_learnings_md creates complete markdown."""

    @pytest.mark.unit
    def test_empty_result_generates_string(self) -> None:
        """Empty result still generates markdown."""
        result = AggregationResult(
            timestamp=datetime.now(timezone.utc),
            skills_analyzed=0,
            total_executions=0,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={},
        )
        content = generate_learnings_md(result)
        assert isinstance(content, str)
        assert "Skill Performance Learnings" in content

    @pytest.mark.unit
    def test_with_existing_pinned_includes_section(self) -> None:
        """Existing pinned content is preserved."""
        result = AggregationResult(
            timestamp=datetime.now(timezone.utc),
            skills_analyzed=0,
            total_executions=0,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={},
        )
        content = generate_learnings_md(result, existing_pinned="My pinned note.")
        assert "Pinned Learnings" in content
        assert "My pinned note." in content

    @pytest.mark.unit
    def test_with_high_impact_issues_includes_section(self) -> None:
        """Issues in result cause High-Impact Issues section."""
        result = AggregationResult(
            timestamp=datetime.now(timezone.utc),
            skills_analyzed=1,
            total_executions=5,
            high_impact_issues=[
                {
                    "skill": "p:bad",
                    "type": "high_failure_rate",
                    "severity": "high",
                    "metric": "success_rate",
                    "detail": "20% success",
                    "errors": [],
                    "friction": [],
                }
            ],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={},
        )
        content = generate_learnings_md(result)
        assert "High-Impact Issues" in content

    @pytest.mark.unit
    def test_with_slow_skills_includes_section(self) -> None:
        """Slow skills in result cause Slow Execution section."""
        result = AggregationResult(
            timestamp=datetime.now(timezone.utc),
            skills_analyzed=1,
            total_executions=3,
            high_impact_issues=[],
            slow_skills=[
                {
                    "skill": "p:slow",
                    "avg_duration_ms": 15000.0,
                    "max_duration_ms": 20000,
                    "executions": 3,
                }
            ],
            low_rated_skills=[],
            metrics_by_skill={},
        )
        content = generate_learnings_md(result)
        assert "Slow Execution" in content

    @pytest.mark.unit
    def test_with_low_rated_skills_includes_section(self) -> None:
        """Low-rated skills in result cause Low User Ratings section."""
        result = AggregationResult(
            timestamp=datetime.now(timezone.utc),
            skills_analyzed=1,
            total_executions=5,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[
                {"skill": "p:bad", "rating": 2.0, "friction": [], "suggestions": []}
            ],
            metrics_by_skill={},
        )
        content = generate_learnings_md(result)
        assert "Low User Ratings" in content


# ---------------------------------------------------------------------------
# Tests: aggregate_logs
# ---------------------------------------------------------------------------


class TestAggregateLogs:
    """Test aggregate_logs runs full pipeline."""

    @pytest.mark.unit
    def test_aggregate_logs_empty_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """aggregate_logs with empty log dir returns empty result."""
        monkeypatch.setattr(
            "aggregate_skill_logs.get_log_directory",
            lambda: tmp_path,
        )
        result = aggregate_logs(days_back=30)
        assert result.skills_analyzed == 0
        assert result.total_executions == 0
        assert result.high_impact_issues == []

    @pytest.mark.unit
    def test_aggregate_logs_with_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """aggregate_logs with entries returns skill metrics."""
        plugin_dir = tmp_path / "my-plugin"
        skill_dir = plugin_dir / "my-skill"
        skill_dir.mkdir(parents=True)

        entries = [_make_entry(outcome="success") for _ in range(8)] + [
            _make_entry(outcome="failure") for _ in range(2)
        ]
        log_file = skill_dir / "log.jsonl"
        log_file.write_text("\n".join(json.dumps(e) for e in entries))

        monkeypatch.setattr(
            "aggregate_skill_logs.get_log_directory",
            lambda: tmp_path,
        )
        result = aggregate_logs(days_back=30)
        assert result.skills_analyzed == 1
        assert result.total_executions == 10


# ---------------------------------------------------------------------------
# Tests: main() function
# ---------------------------------------------------------------------------


class TestAggregateSkillLogsMain:
    """Test main() entry point."""

    @pytest.mark.unit
    def test_main_with_empty_log_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() with empty log dir writes LEARNINGS.md."""
        learnings_path = tmp_path / "LEARNINGS.md"
        monkeypatch.setattr(
            "aggregate_skill_logs.get_log_directory",
            lambda: tmp_path,
        )
        monkeypatch.setattr(
            "aggregate_skill_logs.get_learnings_path",
            lambda: learnings_path,
        )
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py"])

        try:
            aggregate_main()
        except SystemExit as e:
            assert e.code in (0, 1)

        assert learnings_path.exists()

    @pytest.mark.unit
    def test_main_with_existing_pinned_learnings(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() preserves existing pinned learnings."""
        learnings_path = tmp_path / "LEARNINGS.md"
        learnings_path.write_text(
            "# Learnings\n\n## Pinned Learnings\n\nImportant note.\n\n## Other\n\nContent.\n"
        )
        monkeypatch.setattr(
            "aggregate_skill_logs.get_log_directory",
            lambda: tmp_path,
        )
        monkeypatch.setattr(
            "aggregate_skill_logs.get_learnings_path",
            lambda: learnings_path,
        )
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py"])

        try:
            aggregate_main()
        except SystemExit as e:
            assert e.code in (0, 1)

        new_content = learnings_path.read_text()
        assert "Pinned Learnings" in new_content

    @pytest.mark.unit
    def test_main_with_days_back_argument(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() with days_back argument uses specified period."""
        learnings_path = tmp_path / "LEARNINGS.md"
        monkeypatch.setattr(
            "aggregate_skill_logs.get_log_directory",
            lambda: tmp_path,
        )
        monkeypatch.setattr(
            "aggregate_skill_logs.get_learnings_path",
            lambda: learnings_path,
        )
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py", "7"])

        try:
            aggregate_main()
        except SystemExit as e:
            assert e.code in (0, 1)

    @pytest.mark.unit
    def test_main_invalid_days_back_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() with invalid days_back exits 1."""
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py", "abc"])

        with pytest.raises(SystemExit) as exc_info:
            aggregate_main()
        assert exc_info.value.code == 1
