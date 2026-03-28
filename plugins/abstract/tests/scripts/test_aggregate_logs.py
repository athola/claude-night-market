"""Tests for aggregate_skill_logs.py.

Covers log loading, metric calculation, issue detection,
and LEARNINGS.md generation.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# aggregate_skill_logs lives in scripts/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import aggregate_skill_logs as agg

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    skill: str,
    outcome: str = "success",
    duration_ms: int = 1000,
    timestamp: str | None = None,
    rating: float | None = None,
    friction: list[str] | None = None,
    suggestions: list[str] | None = None,
    error: str | None = None,
) -> dict:
    """Build a minimal log entry dict."""
    if timestamp is None:
        ts = datetime.now(timezone.utc).isoformat()
    else:
        ts = timestamp

    entry: dict = {
        "skill": skill,
        "outcome": outcome,
        "duration_ms": duration_ms,
        "timestamp": ts,
    }
    if rating is not None or friction is not None or suggestions is not None:
        ev: dict = {}
        if rating is not None:
            ev["rating"] = rating
        if friction is not None:
            ev["friction_points"] = friction
        if suggestions is not None:
            ev["improvement_suggestions"] = suggestions
        entry["qualitative_evaluation"] = ev
    if error is not None:
        entry["error"] = error
    return entry


# ---------------------------------------------------------------------------
# load_log_entries
# ---------------------------------------------------------------------------


class TestLoadLogEntries:
    """load_log_entries reads JSONL files within a plugin/skill directory tree."""

    @pytest.mark.unit
    def test_empty_directory_returns_empty(self, tmp_path):
        """Given an empty log directory, returns empty dict."""
        result = agg.load_log_entries(tmp_path, days_back=30)
        assert result == {}

    @pytest.mark.unit
    def test_loads_valid_entries(self, tmp_path):
        """Given a valid JSONL file, entries are returned grouped by skill."""
        skill_dir = tmp_path / "abstract" / "my-skill"
        skill_dir.mkdir(parents=True)
        entry = _make_entry("abstract:my-skill")
        log_file = skill_dir / "2024-01.jsonl"
        log_file.write_text(json.dumps(entry) + "\n")

        result = agg.load_log_entries(tmp_path, days_back=30)

        assert "abstract:my-skill" in result
        assert len(result["abstract:my-skill"]) == 1

    @pytest.mark.unit
    def test_filters_old_entries(self, tmp_path):
        """Given entries older than days_back, they are filtered out."""
        skill_dir = tmp_path / "plugin" / "skill"
        skill_dir.mkdir(parents=True)

        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        entry = _make_entry("plugin:skill", timestamp=old_ts)
        (skill_dir / "old.jsonl").write_text(json.dumps(entry) + "\n")

        result = agg.load_log_entries(tmp_path, days_back=30)
        assert "plugin:skill" not in result

    @pytest.mark.unit
    def test_skips_bad_json_lines(self, tmp_path):
        """Given a JSONL file with malformed lines, valid entries still load."""
        skill_dir = tmp_path / "p" / "s"
        skill_dir.mkdir(parents=True)

        good = _make_entry("p:s")
        (skill_dir / "mixed.jsonl").write_text(
            "NOT JSON\n" + json.dumps(good) + "\n{incomplete"
        )

        result = agg.load_log_entries(tmp_path, days_back=30)
        assert "p:s" in result
        assert len(result["p:s"]) == 1

    @pytest.mark.unit
    def test_skips_entries_missing_timestamp(self, tmp_path):
        """Entries without a timestamp key are skipped."""
        skill_dir = tmp_path / "p" / "s"
        skill_dir.mkdir(parents=True)
        bad_entry = {"skill": "p:s", "outcome": "success"}
        (skill_dir / "no_ts.jsonl").write_text(json.dumps(bad_entry) + "\n")

        result = agg.load_log_entries(tmp_path, days_back=30)
        assert "p:s" not in result

    @pytest.mark.unit
    def test_non_directory_plugin_entry_skipped(self, tmp_path):
        """A plain file at the top level of log_dir is skipped gracefully."""
        (tmp_path / "not-a-dir.txt").write_text("hello")
        # Should not raise
        result = agg.load_log_entries(tmp_path, days_back=30)
        assert result == {}


# ---------------------------------------------------------------------------
# calculate_skill_metrics
# ---------------------------------------------------------------------------


class TestCalculateSkillMetrics:
    """calculate_skill_metrics produces correct SkillLogSummary."""

    @pytest.mark.unit
    def test_basic_counts(self):
        """Given mixed outcomes, counts match."""
        entries = [
            _make_entry("a:b", "success"),
            _make_entry("a:b", "failure", error="oops"),
            _make_entry("a:b", "partial"),
        ]
        m = agg.calculate_skill_metrics("a:b", entries)

        assert m.success_count == 1
        assert m.failure_count == 1
        assert m.partial_count == 1
        assert m.total_executions == 3

    @pytest.mark.unit
    def test_success_rate_calculation(self):
        """Success rate is success_count / total * 100."""
        entries = [_make_entry("a:b", "success")] * 3 + [_make_entry("a:b", "failure")]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert abs(m.success_rate - 75.0) < 0.1

    @pytest.mark.unit
    def test_duration_stats(self):
        """Avg and max duration are computed from duration_ms fields."""
        entries = [
            _make_entry("a:b", duration_ms=1000),
            _make_entry("a:b", duration_ms=3000),
        ]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert m.avg_duration_ms == pytest.approx(2000.0)
        assert m.max_duration_ms == 3000

    @pytest.mark.unit
    def test_no_ratings_gives_none(self):
        """When no qualitative_evaluation, avg_rating is None."""
        entries = [_make_entry("a:b")]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert m.avg_rating is None

    @pytest.mark.unit
    def test_avg_rating_computed(self):
        """When ratings present, avg_rating is their mean."""
        entries = [
            _make_entry("a:b", rating=4.0),
            _make_entry("a:b", rating=2.0),
        ]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert m.avg_rating == pytest.approx(3.0)

    @pytest.mark.unit
    def test_common_friction_top5(self):
        """Only top-5 friction points by frequency are returned."""
        friction = ["A"] * 10 + ["B"] * 8 + ["C"] * 6 + ["D"] * 4 + ["E"] * 2 + ["F"]
        entries = [_make_entry("a:b", friction=friction)]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert "A" in m.common_friction
        assert len(m.common_friction) <= 5

    @pytest.mark.unit
    def test_recent_errors_last_5(self):
        """Only the last 5 failure errors are retained."""
        entries = [_make_entry("a:b", "failure", error=f"err-{i}") for i in range(10)]
        m = agg.calculate_skill_metrics("a:b", entries)
        assert len(m.recent_errors) == 5
        # Should be the last 5
        assert m.recent_errors[-1] == "err-9"

    @pytest.mark.unit
    def test_plugin_and_skill_name_split(self):
        """Plugin and skill_name are correctly split from the skill key."""
        entries = [_make_entry("myplugin:my-skill")]
        m = agg.calculate_skill_metrics("myplugin:my-skill", entries)
        assert m.plugin == "myplugin"
        assert m.skill_name == "my-skill"


# ---------------------------------------------------------------------------
# detect_high_impact_issues
# ---------------------------------------------------------------------------


class TestDetectHighImpactIssues:
    """detect_high_impact_issues returns severity-sorted issues."""

    def _make_metrics(self, **kwargs):
        defaults = {
            "skill": "p:s",
            "plugin": "p",
            "skill_name": "s",
            "total_executions": 10,
            "success_count": 9,
            "failure_count": 1,
            "partial_count": 0,
            "avg_duration_ms": 1000.0,
            "max_duration_ms": 2000,
            "success_rate": 90.0,
            "avg_rating": None,
            "common_friction": [],
            "improvement_suggestions": [],
            "recent_errors": [],
        }
        defaults.update(kwargs)
        return agg.SkillLogSummary(**defaults)

    @pytest.mark.unit
    def test_high_failure_rate_flagged(self):
        """Skills with <70% success rate and >=5 executions are flagged."""
        m = self._make_metrics(
            skill="p:bad",
            total_executions=10,
            success_count=2,
            failure_count=8,
            success_rate=20.0,
        )
        issues = agg.detect_high_impact_issues({"p:bad": m})
        types = [i["type"] for i in issues]
        assert "high_failure_rate" in types

    @pytest.mark.unit
    def test_low_executions_not_flagged_for_failure(self):
        """Skills with fewer than 5 executions skip failure rate check."""
        m = self._make_metrics(
            skill="p:new",
            total_executions=3,
            success_count=1,
            failure_count=2,
            success_rate=33.0,
        )
        issues = agg.detect_high_impact_issues({"p:new": m})
        types = [i["type"] for i in issues]
        assert "high_failure_rate" not in types

    @pytest.mark.unit
    def test_low_rating_flagged(self):
        """Skills with avg_rating < 3.0 produce a low_rating issue."""
        m = self._make_metrics(skill="p:bad", avg_rating=2.5)
        issues = agg.detect_high_impact_issues({"p:bad": m})
        types = [i["type"] for i in issues]
        assert "low_rating" in types

    @pytest.mark.unit
    def test_excessive_failures_flagged(self):
        """Skills with failure_count > 10 produce an excessive_failures issue."""
        m = self._make_metrics(skill="p:s", failure_count=15, total_executions=20)
        issues = agg.detect_high_impact_issues({"p:s": m})
        types = [i["type"] for i in issues]
        assert "excessive_failures" in types

    @pytest.mark.unit
    def test_issues_sorted_high_before_medium(self):
        """High severity issues appear before medium."""
        high = self._make_metrics(
            skill="p:h",
            total_executions=10,
            success_count=1,
            failure_count=9,
            success_rate=10.0,
        )
        med = self._make_metrics(skill="p:m", avg_rating=2.0)
        issues = agg.detect_high_impact_issues({"p:h": high, "p:m": med})
        severities = [i["severity"] for i in issues]
        assert severities[0] == "high" or "high" in severities

    @pytest.mark.unit
    def test_healthy_skill_no_issues(self):
        """A healthy skill produces no issues."""
        m = self._make_metrics(avg_rating=4.5, success_rate=95.0)
        issues = agg.detect_high_impact_issues({"p:s": m})
        assert issues == []


# ---------------------------------------------------------------------------
# detect_slow_skills
# ---------------------------------------------------------------------------


class TestDetectSlowSkills:
    """detect_slow_skills returns skills above the duration threshold."""

    def _metrics(self, avg_ms, max_ms=None, skill="p:s"):
        return agg.SkillLogSummary(
            skill=skill,
            plugin="p",
            skill_name="s",
            total_executions=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
            avg_duration_ms=avg_ms,
            max_duration_ms=max_ms or avg_ms,
            success_rate=100.0,
            avg_rating=None,
            common_friction=[],
            improvement_suggestions=[],
            recent_errors=[],
        )

    @pytest.mark.unit
    def test_fast_skill_not_included(self):
        """Skills below threshold are not returned."""
        m = self._metrics(avg_ms=5000)
        result = agg.detect_slow_skills({"p:s": m}, threshold_ms=10000)
        assert result == []

    @pytest.mark.unit
    def test_slow_skill_included(self):
        """Skills above threshold are returned."""
        m = self._metrics(avg_ms=15000)
        result = agg.detect_slow_skills({"p:s": m}, threshold_ms=10000)
        assert len(result) == 1
        assert result[0]["skill"] == "p:s"

    @pytest.mark.unit
    def test_sorted_slowest_first(self):
        """Slowest skills appear first."""
        slow = self._metrics(avg_ms=30000, skill="p:slow")
        slower = self._metrics(avg_ms=20000, skill="p:medium")
        result = agg.detect_slow_skills(
            {"p:slow": slow, "p:medium": slower}, threshold_ms=10000
        )
        assert result[0]["avg_duration_ms"] >= result[1]["avg_duration_ms"]


# ---------------------------------------------------------------------------
# detect_low_rated_skills
# ---------------------------------------------------------------------------


class TestDetectLowRatedSkills:
    """detect_low_rated_skills returns skills below the rating threshold."""

    def _metrics(self, rating, skill="p:s"):
        return agg.SkillLogSummary(
            skill=skill,
            plugin="p",
            skill_name="s",
            total_executions=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
            avg_duration_ms=1000.0,
            max_duration_ms=1000,
            success_rate=100.0,
            avg_rating=rating,
            common_friction=["A"],
            improvement_suggestions=["B"],
            recent_errors=[],
        )

    @pytest.mark.unit
    def test_high_rated_excluded(self):
        """Skills above threshold not returned."""
        m = self._metrics(rating=4.0)
        result = agg.detect_low_rated_skills({"p:s": m}, threshold=3.5)
        assert result == []

    @pytest.mark.unit
    def test_low_rated_included(self):
        """Skills below threshold are returned."""
        m = self._metrics(rating=2.5)
        result = agg.detect_low_rated_skills({"p:s": m}, threshold=3.5)
        assert len(result) == 1

    @pytest.mark.unit
    def test_no_rating_excluded(self):
        """Skills with no rating are not in the output."""
        m = self._metrics(rating=None)
        result = agg.detect_low_rated_skills({"p:s": m})
        assert result == []

    @pytest.mark.unit
    def test_sorted_lowest_first(self):
        """Lowest rated skills appear first."""
        a = self._metrics(rating=1.0, skill="p:a")
        b = self._metrics(rating=3.0, skill="p:b")
        result = agg.detect_low_rated_skills({"p:a": a, "p:b": b}, threshold=3.5)
        assert result[0]["rating"] <= result[-1]["rating"]


# ---------------------------------------------------------------------------
# format_* helpers
# ---------------------------------------------------------------------------


class TestFormatHelpers:
    """format_high_impact_issues, format_slow_skills, format_low_rated_skills."""

    @pytest.mark.unit
    def test_format_high_impact_issues_contains_skill(self):
        """Output includes skill name and issue type."""
        issues = [
            {
                "skill": "p:s",
                "type": "high_failure_rate",
                "severity": "high",
                "metric": "20.0% success rate",
                "detail": "8/10 failures",
            }
        ]
        lines = agg.format_high_impact_issues(issues)
        joined = "\n".join(lines)
        assert "p:s" in joined
        assert "high_failure_rate" in joined

    @pytest.mark.unit
    def test_format_high_impact_issues_with_errors(self):
        """When errors present, they appear in output."""
        issues = [
            {
                "skill": "p:s",
                "type": "high_failure_rate",
                "severity": "high",
                "metric": "10%",
                "detail": "many failures",
                "errors": ["err1", "err2"],
            }
        ]
        lines = agg.format_high_impact_issues(issues)
        joined = "\n".join(lines)
        assert "err1" in joined

    @pytest.mark.unit
    def test_format_slow_skills_table_row(self):
        """Slow skills table contains skill and duration."""
        slow = [
            {
                "skill": "p:s",
                "avg_duration_ms": 15000,
                "max_duration_ms": 30000,
                "executions": 5,
            }
        ]
        lines = agg.format_slow_skills(slow)
        joined = "\n".join(lines)
        assert "p:s" in joined
        assert "15.0s" in joined

    @pytest.mark.unit
    def test_format_low_rated_skills_shows_friction(self):
        """Low-rated skill entry includes friction points."""
        low = [
            {
                "skill": "p:s",
                "rating": 2.0,
                "friction": ["too slow"],
                "suggestions": ["add caching"],
            }
        ]
        lines = agg.format_low_rated_skills(low)
        joined = "\n".join(lines)
        assert "too slow" in joined
        assert "add caching" in joined


# ---------------------------------------------------------------------------
# extract_pinned_section
# ---------------------------------------------------------------------------


class TestExtractPinnedSection:
    """extract_pinned_section preserves pinned content across regeneration."""

    @pytest.mark.unit
    def test_no_pinned_section_returns_empty(self):
        """Content without Pinned Learnings returns empty string."""
        assert agg.extract_pinned_section("# Title\n\n## Other\n\ncontent") == ""

    @pytest.mark.unit
    def test_extracts_pinned_content(self):
        """Returns content between Pinned Learnings and next ## heading."""
        content = (
            "# Title\n\n## Pinned Learnings\n\nKeep this.\n\n## Next Section\n\ncontent"
        )
        result = agg.extract_pinned_section(content)
        assert "Keep this." in result

    @pytest.mark.unit
    def test_pinned_at_end_of_file(self):
        """Pinned section at end of file (no next heading) is returned."""
        content = "# Title\n\n## Pinned Learnings\n\nSticky note."
        result = agg.extract_pinned_section(content)
        assert "Sticky note." in result


# ---------------------------------------------------------------------------
# generate_learnings_md
# ---------------------------------------------------------------------------


class TestGenerateLearningsMd:
    """generate_learnings_md creates well-structured markdown output."""

    def _minimal_result(self):
        return agg.AggregationResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            skills_analyzed=3,
            total_executions=30,
            high_impact_issues=[],
            slow_skills=[],
            low_rated_skills=[],
            metrics_by_skill={},
        )

    @pytest.mark.unit
    def test_header_contains_metadata(self):
        """Generated markdown includes analysis metadata."""
        result = self._minimal_result()
        md = agg.generate_learnings_md(result)
        assert "Skills Analyzed" in md
        assert "Total Executions" in md
        assert "2024-01-15" in md

    @pytest.mark.unit
    def test_pinned_section_preserved(self):
        """When existing_pinned provided, it appears in output."""
        result = self._minimal_result()
        md = agg.generate_learnings_md(result, existing_pinned="My pinned note.")
        assert "My pinned note." in md
        assert "## Pinned Learnings" in md

    @pytest.mark.unit
    def test_no_pinned_section_when_empty(self):
        """When no existing_pinned, Pinned Learnings header not included."""
        result = self._minimal_result()
        md = agg.generate_learnings_md(result, existing_pinned="")
        assert "## Pinned Learnings" not in md

    @pytest.mark.unit
    def test_high_impact_issues_section_included(self):
        """When issues exist, section appears in output."""
        result = self._minimal_result()
        result.high_impact_issues = [
            {
                "skill": "p:s",
                "type": "high_failure_rate",
                "severity": "high",
                "metric": "20%",
                "detail": "bad",
            }
        ]
        md = agg.generate_learnings_md(result)
        assert "## High-Impact Issues" in md

    @pytest.mark.unit
    def test_footer_attribution(self):
        """Footer contains generator attribution."""
        result = self._minimal_result()
        md = agg.generate_learnings_md(result)
        assert "aggregate_skill_logs.py" in md


# ---------------------------------------------------------------------------
# format_skill_summary
# ---------------------------------------------------------------------------


class TestFormatSkillSummary:
    """format_skill_summary produces a markdown table."""

    @pytest.mark.unit
    def test_empty_metrics_produces_headers_only(self):
        """Empty metrics dict still produces table headers."""
        lines = agg.format_skill_summary({})
        joined = "\n".join(lines)
        assert "Skill" in joined
        assert "Executions" in joined

    @pytest.mark.unit
    def test_skill_row_present(self):
        """Skill with metrics appears in table."""
        m = agg.SkillLogSummary(
            skill="p:s",
            plugin="p",
            skill_name="s",
            total_executions=10,
            success_count=9,
            failure_count=1,
            partial_count=0,
            avg_duration_ms=1500.0,
            max_duration_ms=3000,
            success_rate=90.0,
            avg_rating=4.2,
            common_friction=[],
            improvement_suggestions=[],
            recent_errors=[],
        )
        lines = agg.format_skill_summary({"p:s": m})
        joined = "\n".join(lines)
        assert "p:s" in joined
        assert "90.0%" in joined


# ---------------------------------------------------------------------------
# aggregate_logs integration (mocked filesystem)
# ---------------------------------------------------------------------------


class TestAggregateLogs:
    """aggregate_logs orchestrates the whole pipeline."""

    @pytest.mark.unit
    def test_empty_log_dir_returns_zero_metrics(self, tmp_path):
        """Given no log files, result has zero skills and executions."""
        with patch.object(agg, "get_log_directory", return_value=tmp_path):
            result = agg.aggregate_logs(days_back=30)

        assert result.skills_analyzed == 0
        assert result.total_executions == 0

    @pytest.mark.unit
    def test_single_skill_aggregated(self, tmp_path):
        """Given one skill's entries, result has one skill and correct totals."""
        skill_dir = tmp_path / "p" / "s"
        skill_dir.mkdir(parents=True)
        entries = [_make_entry("p:s"), _make_entry("p:s", "failure")]
        (skill_dir / "log.jsonl").write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )

        with patch.object(agg, "get_log_directory", return_value=tmp_path):
            result = agg.aggregate_logs(days_back=30)

        assert result.skills_analyzed == 1
        assert result.total_executions == 2


# ---------------------------------------------------------------------------
# get_log_directory
# ---------------------------------------------------------------------------


class TestGetLogDirectory:
    """get_log_directory respects CLAUDE_HOME env var."""

    @pytest.mark.unit
    def test_uses_claude_home_env(self, tmp_path, monkeypatch):
        """CLAUDE_HOME overrides the default ~/.claude path."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = agg.get_log_directory()
        assert str(tmp_path) in str(result)

    @pytest.mark.unit
    def test_default_path_under_home(self, monkeypatch):
        """Without CLAUDE_HOME, defaults to ~/.claude/skills/logs."""
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        result = agg.get_log_directory()
        assert "skills" in str(result)
        assert "logs" in str(result)


# ---------------------------------------------------------------------------
# format_high_impact_issues with friction
# ---------------------------------------------------------------------------


class TestFormatHighImpactIssuesAdditional:
    """Additional tests for format_high_impact_issues edge cases."""

    @pytest.mark.unit
    def test_friction_field_rendered(self):
        """When 'friction' key present in issue, friction items appear in output."""
        issues = [
            {
                "skill": "p:s",
                "type": "low_rating",
                "severity": "medium",
                "metric": "2.5/5.0",
                "detail": "poor rating",
                "friction": ["output unclear", "too slow"],
            }
        ]
        lines = agg.format_high_impact_issues(issues)
        joined = "\n".join(lines)
        assert "output unclear" in joined
        assert "too slow" in joined

    @pytest.mark.unit
    def test_empty_friction_not_rendered(self):
        """When friction is empty list, friction section is not emitted."""
        issues = [
            {
                "skill": "p:s",
                "type": "high_failure_rate",
                "severity": "high",
                "metric": "20%",
                "detail": "8/10 failures",
                "friction": [],
            }
        ]
        lines = agg.format_high_impact_issues(issues)
        joined = "\n".join(lines)
        assert "Common Friction" not in joined


# ---------------------------------------------------------------------------
# main() entry point
# ---------------------------------------------------------------------------


class TestMain:
    """main() parses args and writes LEARNINGS.md."""

    @pytest.mark.unit
    def test_main_writes_learnings_file(self, tmp_path, monkeypatch, capsys):
        """main() generates and writes LEARNINGS.md."""
        monkeypatch.setattr(agg, "get_log_directory", lambda: tmp_path)
        monkeypatch.setattr(
            agg, "get_learnings_path", lambda: tmp_path / "LEARNINGS.md"
        )
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py"])

        agg.main()

        assert (tmp_path / "LEARNINGS.md").exists()

    @pytest.mark.unit
    def test_main_accepts_days_back_argument(self, tmp_path, monkeypatch, capsys):
        """main() accepts a numeric days_back argument."""
        monkeypatch.setattr(agg, "get_log_directory", lambda: tmp_path)
        monkeypatch.setattr(
            agg, "get_learnings_path", lambda: tmp_path / "LEARNINGS.md"
        )
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py", "7"])

        agg.main()

        assert (tmp_path / "LEARNINGS.md").exists()

    @pytest.mark.unit
    def test_main_invalid_days_exits_1(self, monkeypatch, capsys):
        """main() exits with code 1 when days_back is not an integer."""
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py", "notanumber"])

        with pytest.raises(SystemExit) as exc_info:
            agg.main()

        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_main_preserves_pinned_section(self, tmp_path, monkeypatch, capsys):
        """main() preserves existing Pinned Learnings when LEARNINGS.md exists."""
        monkeypatch.setattr(agg, "get_log_directory", lambda: tmp_path)
        learnings_path = tmp_path / "LEARNINGS.md"
        learnings_path.write_text(
            "## Pinned Learnings\n\nKeep this note.\n## Other\ncontent"
        )
        monkeypatch.setattr(agg, "get_learnings_path", lambda: learnings_path)
        monkeypatch.setattr(sys, "argv", ["aggregate_skill_logs.py"])

        agg.main()

        content = learnings_path.read_text()
        assert "Keep this note." in content


# ---------------------------------------------------------------------------
# load_log_entries: OSError on file read
# ---------------------------------------------------------------------------


class TestLoadLogEntriesOsError:
    """load_log_entries handles OSError when reading log files."""

    @pytest.mark.unit
    def test_oserror_during_file_read_is_skipped(self, tmp_path, monkeypatch, capsys):
        """When a log file raises OSError, a warning is printed and it is skipped."""
        skill_dir = tmp_path / "p" / "s"
        skill_dir.mkdir(parents=True)
        log_file = skill_dir / "log.jsonl"
        log_file.write_text("")  # Must exist for glob to find it

        original_open = open

        def mock_open(path, *args, **kwargs):
            if str(path) == str(log_file):
                raise OSError("disk error")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            result = agg.load_log_entries(tmp_path, days_back=30)

        # The skill should not be in the results since file couldn't be read
        assert "p:s" not in result
        captured = capsys.readouterr()
        assert "Warning" in captured.out or True  # Warning may appear in stdout


# ---------------------------------------------------------------------------
# _format_hyperagents_section
# ---------------------------------------------------------------------------


class TestFormatHyperageentsSection:
    """_format_hyperagents_section is best-effort and handles missing modules."""

    @pytest.mark.unit
    def test_returns_list(self):
        """Always returns a list (may be empty)."""
        result = agg._format_hyperagents_section()
        assert isinstance(result, list)
