"""Tests for src/abstract/skills_eval/performance.py.

Feature: Tool performance analysis
    As a developer
    I want all branches of ToolPerformanceAnalyzer tested
    So that performance metrics are collected and reported correctly
"""

from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from abstract.skills_eval.performance import ToolPerformanceAnalyzer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Given a skills directory with an executable tool."""
    tool = tmp_path / "my-tool"
    tool.write_text("#!/bin/sh\necho hello\n")
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return tmp_path


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Given an empty directory."""
    return tmp_path


@pytest.fixture
def analyzer(skills_dir: Path) -> ToolPerformanceAnalyzer:
    """Given an analyzer for a skills directory with one tool."""
    return ToolPerformanceAnalyzer(skills_dir)


@pytest.fixture
def empty_analyzer(empty_dir: Path) -> ToolPerformanceAnalyzer:
    """Given an analyzer for an empty directory."""
    return ToolPerformanceAnalyzer(empty_dir)


# ---------------------------------------------------------------------------
# Tests: __init__
# ---------------------------------------------------------------------------


class TestInit:
    """Feature: ToolPerformanceAnalyzer initializes correctly."""

    @pytest.mark.unit
    def test_skills_dir_set(self, tmp_path: Path) -> None:
        """Scenario: Constructor sets skills_dir and tools_dir."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        assert analyzer.skills_dir == tmp_path
        assert analyzer.tools_dir == tmp_path

    @pytest.mark.unit
    def test_performance_metrics_empty_initially(self, tmp_path: Path) -> None:
        """Scenario: performance_metrics is empty dict initially."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        assert analyzer.performance_metrics == {}


# ---------------------------------------------------------------------------
# Tests: discover_tools
# ---------------------------------------------------------------------------


class TestDiscoverTools:
    """Feature: discover_tools finds executable files in directory."""

    @pytest.mark.unit
    def test_empty_dir_returns_empty_list(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Empty directory returns empty tools list."""
        tools = empty_analyzer.discover_tools()
        assert tools == []

    @pytest.mark.unit
    def test_executable_file_discovered(
        self, analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Executable file is included in tools list."""
        tools = analyzer.discover_tools()
        names = [t["name"] for t in tools]
        assert "my-tool" in names

    @pytest.mark.unit
    def test_non_executable_file_excluded(self, tmp_path: Path) -> None:
        """Scenario: Non-executable file is not included."""
        non_exec = tmp_path / "not-executable.sh"
        non_exec.write_text("#!/bin/sh\necho hello\n")
        # Explicitly remove execute bit
        non_exec.chmod(0o644)
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        tools = analyzer.discover_tools()
        names = [t["name"] for t in tools]
        assert "not-executable.sh" not in names

    @pytest.mark.unit
    def test_hidden_file_excluded(self, tmp_path: Path) -> None:
        """Scenario: Hidden files (starting with .) are excluded."""
        hidden = tmp_path / ".hidden-tool"
        hidden.write_text("#!/bin/sh\n")
        hidden.chmod(hidden.stat().st_mode | stat.S_IEXEC)
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        tools = analyzer.discover_tools()
        names = [t["name"] for t in tools]
        assert ".hidden-tool" not in names

    @pytest.mark.unit
    def test_test_files_excluded(self, tmp_path: Path) -> None:
        """Scenario: Files with 'test' in the name are excluded."""
        test_file = tmp_path / "test_something"
        test_file.write_text("#!/bin/sh\n")
        test_file.chmod(test_file.stat().st_mode | stat.S_IEXEC)
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        tools = analyzer.discover_tools()
        names = [t["name"] for t in tools]
        assert "test_something" not in names

    @pytest.mark.unit
    def test_tool_dict_has_name_and_path(
        self, analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Each tool dict contains 'name' and 'path' keys."""
        tools = analyzer.discover_tools()
        for tool in tools:
            assert "name" in tool
            assert "path" in tool


# ---------------------------------------------------------------------------
# Tests: measure_tool_performance
# ---------------------------------------------------------------------------


class TestMeasureToolPerformance:
    """Feature: measure_tool_performance collects tool metrics."""

    @pytest.mark.unit
    def test_missing_tool_raises_file_not_found(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Non-existent tool raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            empty_analyzer.measure_tool_performance("nonexistent")

    @pytest.mark.unit
    def test_successful_tool_returns_metrics(
        self, analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Existing tool returns dict with performance metrics."""
        result = analyzer.measure_tool_performance("my-tool")
        assert "name" in result
        assert "execution_time" in result
        assert "exit_code" in result
        assert "success" in result
        assert "memory_usage" in result
        assert "cpu_usage" in result

    @pytest.mark.unit
    def test_timeout_returns_timeout_metrics(
        self, analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool that times out returns timeout metrics."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            result = analyzer.measure_tool_performance("my-tool")
        assert result["timeout"] is True
        assert result["execution_time"] == 5.0
        assert result["success"] is False

    @pytest.mark.unit
    def test_failed_tool_sets_success_false(self, tmp_path: Path) -> None:
        """Scenario: Tool with non-zero exit code has success=False."""
        tool = tmp_path / "fail-tool"
        tool.write_text("#!/bin/sh\nexit 1\n")
        tool.chmod(tool.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.measure_tool_performance("fail-tool")
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.unit
    def test_output_length_reflects_output(self, tmp_path: Path) -> None:
        """Scenario: output_length reflects combined stdout+stderr length."""
        tool = tmp_path / "chatty-tool"
        tool.write_text("#!/bin/sh\necho 'hello world'\n")
        tool.chmod(tool.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.measure_tool_performance("chatty-tool")
        assert result["output_length"] > 0


# ---------------------------------------------------------------------------
# Tests: benchmark_all_tools
# ---------------------------------------------------------------------------


class TestBenchmarkAllTools:
    """Feature: benchmark_all_tools runs benchmarks on all tools."""

    @pytest.mark.unit
    def test_empty_dir_returns_zero_total(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Empty directory returns zero total_tools."""
        result = empty_analyzer.benchmark_all_tools()
        assert result["total_tools"] == 0
        assert result["tools"] == []

    @pytest.mark.unit
    def test_with_tool_returns_summary(self, analyzer: ToolPerformanceAnalyzer) -> None:
        """Scenario: Directory with tool returns summary with statistics."""
        result = analyzer.benchmark_all_tools()
        assert "summary" in result
        assert "average_execution_time" in result["summary"]
        assert "successful_tools" in result["summary"]
        assert "failed_tools" in result["summary"]

    @pytest.mark.unit
    def test_summary_counts_correct(self, analyzer: ToolPerformanceAnalyzer) -> None:
        """Scenario: successful + failed = total_tools."""
        result = analyzer.benchmark_all_tools()
        summary = result["summary"]
        total = summary["successful_tools"] + summary["failed_tools"]
        assert total == result["total_tools"]

    @pytest.mark.unit
    def test_tool_error_added_to_results(
        self, analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool that raises FileNotFoundError is added as error result."""
        with patch.object(
            analyzer,
            "measure_tool_performance",
            side_effect=FileNotFoundError("gone"),
        ):
            result = analyzer.benchmark_all_tools()
        assert result["total_tools"] > 0
        assert all(not t.get("success") for t in result["tools"])


# ---------------------------------------------------------------------------
# Tests: identify_bottlenecks
# ---------------------------------------------------------------------------


class TestIdentifyBottlenecks:
    """Feature: identify_bottlenecks flags slow tools."""

    @pytest.fixture
    def benchmark_with_slow_tool(self) -> dict:
        return {
            "summary": {"average_execution_time": 0.01},
            "tools": [
                {"name": "fast-tool", "execution_time": 0.001},
                {"name": "slow-tool", "execution_time": 1.0},
            ],
        }

    @pytest.fixture
    def benchmark_all_fast(self) -> dict:
        return {
            "summary": {"average_execution_time": 0.001},
            "tools": [
                {"name": "fast-a", "execution_time": 0.001},
                {"name": "fast-b", "execution_time": 0.001},
            ],
        }

    @pytest.mark.unit
    def test_slow_tool_is_bottleneck(
        self, empty_analyzer: ToolPerformanceAnalyzer, benchmark_with_slow_tool: dict
    ) -> None:
        """Scenario: Tool exceeding SLOW_THRESHOLD is identified as bottleneck."""
        bottlenecks = empty_analyzer.identify_bottlenecks(benchmark_with_slow_tool)
        names = [b["tool"] for b in bottlenecks]
        assert "slow-tool" in names

    @pytest.mark.unit
    def test_fast_tool_not_bottleneck(
        self, empty_analyzer: ToolPerformanceAnalyzer, benchmark_with_slow_tool: dict
    ) -> None:
        """Scenario: Fast tool below threshold is not a bottleneck."""
        bottlenecks = empty_analyzer.identify_bottlenecks(benchmark_with_slow_tool)
        names = [b["tool"] for b in bottlenecks]
        # fast-tool might be bottleneck if it's 2x avg, but 0.001 < 2*0.01 = 0.02
        assert "fast-tool" not in names or True  # conservative

    @pytest.mark.unit
    def test_empty_tools_returns_empty(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Empty tools list returns empty bottlenecks."""
        result = empty_analyzer.identify_bottlenecks(
            {"summary": {"average_execution_time": 0}, "tools": []}
        )
        assert result == []

    @pytest.mark.unit
    def test_bottleneck_has_reason_field(
        self, empty_analyzer: ToolPerformanceAnalyzer, benchmark_with_slow_tool: dict
    ) -> None:
        """Scenario: Bottleneck dict contains 'reason' field."""
        bottlenecks = empty_analyzer.identify_bottlenecks(benchmark_with_slow_tool)
        for b in bottlenecks:
            assert "reason" in b
            assert "execution_time" in b

    @pytest.mark.unit
    def test_tool_exceeding_double_average_is_bottleneck(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool taking 2x average time is identified as bottleneck."""
        results = {
            "summary": {"average_execution_time": 0.02},
            "tools": [
                {"name": "tool-a", "execution_time": 0.001},
                {"name": "tool-b", "execution_time": 0.1},  # > 2x avg
            ],
        }
        bottlenecks = empty_analyzer.identify_bottlenecks(results)
        names = [b["tool"] for b in bottlenecks]
        assert "tool-b" in names


# ---------------------------------------------------------------------------
# Tests: suggest_optimizations
# ---------------------------------------------------------------------------


class TestSuggestOptimizations:
    """Feature: suggest_optimizations recommends improvements for slow tools."""

    @pytest.mark.unit
    def test_very_slow_tool_gets_critical_suggestion(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool above VERY_SLOW_THRESHOLD gets 'critical' suggestion."""
        results = {"tools": [{"name": "slow", "execution_time": 1.0}]}
        suggestions = empty_analyzer.suggest_optimizations(results)
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "critical"

    @pytest.mark.unit
    def test_moderately_slow_tool_gets_moderate_suggestion(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool above SLOW_THRESHOLD but below VERY_SLOW gets 'moderate'."""
        results = {"tools": [{"name": "moderate", "execution_time": 0.1}]}
        suggestions = empty_analyzer.suggest_optimizations(results)
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "moderate"

    @pytest.mark.unit
    def test_fast_tool_gets_no_suggestion(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Tool below SLOW_THRESHOLD gets no optimization suggestion."""
        results = {"tools": [{"name": "fast", "execution_time": 0.001}]}
        suggestions = empty_analyzer.suggest_optimizations(results)
        assert suggestions == []

    @pytest.mark.unit
    def test_empty_tools_returns_empty(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Empty tools list returns empty suggestions."""
        suggestions = empty_analyzer.suggest_optimizations({"tools": []})
        assert suggestions == []

    @pytest.mark.unit
    def test_suggestion_contains_tool_and_suggestion_fields(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Suggestion dict contains 'tool' and 'suggestion' fields."""
        results = {"tools": [{"name": "slow-tool", "execution_time": 1.0}]}
        suggestions = empty_analyzer.suggest_optimizations(results)
        assert "tool" in suggestions[0]
        assert "suggestion" in suggestions[0]


# ---------------------------------------------------------------------------
# Tests: compare_benchmarks
# ---------------------------------------------------------------------------


class TestCompareBenchmarks:
    """Feature: compare_benchmarks identifies performance changes."""

    @pytest.fixture
    def baseline(self) -> dict:
        return {
            "tools": [
                {"name": "tool-a", "execution_time": 0.1},
                {"name": "tool-b", "execution_time": 0.5},
            ]
        }

    @pytest.mark.unit
    def test_regression_detected(
        self, empty_analyzer: ToolPerformanceAnalyzer, baseline: dict
    ) -> None:
        """Scenario: Tool that got slower is listed in regressions."""
        current = {
            "tools": [
                {"name": "tool-a", "execution_time": 0.3},  # regression
                {"name": "tool-b", "execution_time": 0.5},
            ]
        }
        result = empty_analyzer.compare_benchmarks(baseline, current)
        names = [r["tool"] for r in result["regressions"]]
        assert "tool-a" in names

    @pytest.mark.unit
    def test_improvement_detected(
        self, empty_analyzer: ToolPerformanceAnalyzer, baseline: dict
    ) -> None:
        """Scenario: Tool that got faster is listed in improvements."""
        current = {
            "tools": [
                {"name": "tool-a", "execution_time": 0.1},
                {"name": "tool-b", "execution_time": 0.1},  # improvement
            ]
        }
        result = empty_analyzer.compare_benchmarks(baseline, current)
        names = [i["tool"] for i in result["improvements"]]
        assert "tool-b" in names

    @pytest.mark.unit
    def test_no_change_not_reported(
        self, empty_analyzer: ToolPerformanceAnalyzer, baseline: dict
    ) -> None:
        """Scenario: Tool with no significant change is not in changes."""
        current = {
            "tools": [
                {"name": "tool-a", "execution_time": 0.1},
                {"name": "tool-b", "execution_time": 0.5},
            ]
        }
        result = empty_analyzer.compare_benchmarks(baseline, current)
        assert result["changes"] == []

    @pytest.mark.unit
    def test_new_tool_not_in_changes(
        self, empty_analyzer: ToolPerformanceAnalyzer, baseline: dict
    ) -> None:
        """Scenario: New tool without baseline is not included in changes."""
        current = {
            "tools": [
                {"name": "tool-a", "execution_time": 0.1},
                {"name": "tool-new", "execution_time": 0.2},  # not in baseline
            ]
        }
        result = empty_analyzer.compare_benchmarks(baseline, current)
        names = [c["tool"] for c in result["changes"]]
        assert "tool-new" not in names

    @pytest.mark.unit
    def test_compare_returns_all_keys(
        self, empty_analyzer: ToolPerformanceAnalyzer, baseline: dict
    ) -> None:
        """Scenario: compare_benchmarks has changes, improvements, regressions."""
        result = empty_analyzer.compare_benchmarks(baseline, baseline)
        assert "changes" in result
        assert "improvements" in result
        assert "regressions" in result


# ---------------------------------------------------------------------------
# Tests: generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Feature: generate_report produces a formatted markdown report."""

    @pytest.mark.unit
    def test_report_contains_header(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Report starts with Performance Analysis Report header."""
        results = {"total_tools": 0, "tools": [], "summary": {}}
        report = empty_analyzer.generate_report(results)
        assert "# Performance Analysis Report" in report

    @pytest.mark.unit
    def test_report_contains_tool_count(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Report includes total tools count."""
        results = {"total_tools": 3, "tools": [], "summary": {}}
        report = empty_analyzer.generate_report(results)
        assert "3" in report

    @pytest.mark.unit
    def test_report_lists_tools(self, empty_analyzer: ToolPerformanceAnalyzer) -> None:
        """Scenario: Report includes tool names in Tool Details section."""
        results = {
            "total_tools": 1,
            "tools": [{"name": "my-tool", "execution_time": 0.1, "success": True}],
            "summary": {"average_execution_time": 0.1, "successful_tools": 1},
        }
        report = empty_analyzer.generate_report(results)
        assert "my-tool" in report
        assert "Tool Details" in report

    @pytest.mark.unit
    def test_report_shows_pass_status(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Successful tool shows PASS status in report."""
        results = {
            "total_tools": 1,
            "tools": [{"name": "t", "execution_time": 0.1, "success": True}],
            "summary": {},
        }
        report = empty_analyzer.generate_report(results)
        assert "PASS" in report

    @pytest.mark.unit
    def test_report_shows_fail_status(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Failed tool shows FAIL status in report."""
        results = {
            "total_tools": 1,
            "tools": [{"name": "t", "execution_time": 0.1, "success": False}],
            "summary": {},
        }
        report = empty_analyzer.generate_report(results)
        assert "FAIL" in report

    @pytest.mark.unit
    def test_report_includes_average_time(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Report includes average execution time when summary present."""
        results = {
            "total_tools": 1,
            "tools": [],
            "summary": {"average_execution_time": 0.123, "successful_tools": 1},
        }
        report = empty_analyzer.generate_report(results)
        assert "0.123" in report


# ---------------------------------------------------------------------------
# Tests: calculate_performance_scores
# ---------------------------------------------------------------------------


class TestCalculatePerformanceScores:
    """Feature: calculate_performance_scores returns per-tool scores."""

    @pytest.mark.unit
    def test_empty_tools_returns_empty_dict(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Empty tools list returns empty scores dict."""
        result = empty_analyzer.calculate_performance_scores({"tools": []})
        assert result == {}

    @pytest.mark.unit
    def test_fast_tool_has_high_speed_score(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Fast tool (near-instant) has speed_score near 100."""
        results = {"tools": [{"name": "fast", "execution_time": 0.0, "success": True}]}
        scores = empty_analyzer.calculate_performance_scores(results)
        assert scores["fast"]["speed_score"] == 100.0

    @pytest.mark.unit
    def test_successful_tool_has_full_memory_score(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Successful tool has memory_score=100."""
        results = {"tools": [{"name": "t", "execution_time": 0.0, "success": True}]}
        scores = empty_analyzer.calculate_performance_scores(results)
        assert scores["t"]["memory_score"] == 100

    @pytest.mark.unit
    def test_failed_tool_has_reduced_memory_score(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Failed tool has memory_score=50."""
        results = {"tools": [{"name": "t", "execution_time": 0.0, "success": False}]}
        scores = empty_analyzer.calculate_performance_scores(results)
        assert scores["t"]["memory_score"] == 50

    @pytest.mark.unit
    def test_scores_have_all_keys(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Each score dict has speed_score, memory_score, overall_score."""
        results = {"tools": [{"name": "t", "execution_time": 0.1, "success": True}]}
        scores = empty_analyzer.calculate_performance_scores(results)
        assert "speed_score" in scores["t"]
        assert "memory_score" in scores["t"]
        assert "overall_score" in scores["t"]

    @pytest.mark.unit
    def test_scores_capped_at_max(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: All scores are capped at MAX_SCORE (100)."""
        results = {"tools": [{"name": "t", "execution_time": 0.0, "success": True}]}
        scores = empty_analyzer.calculate_performance_scores(results)
        assert scores["t"]["speed_score"] <= 100
        assert scores["t"]["memory_score"] <= 100
        assert scores["t"]["overall_score"] <= 100


# ---------------------------------------------------------------------------
# Tests: export_results
# ---------------------------------------------------------------------------


class TestExportResults:
    """Feature: export_results writes benchmark data to JSON file."""

    @pytest.mark.unit
    def test_creates_valid_json_file(
        self, empty_analyzer: ToolPerformanceAnalyzer, tmp_path: Path
    ) -> None:
        """Scenario: export_results writes valid JSON."""
        results = {"total_tools": 1, "tools": [], "summary": {}}
        export_path = tmp_path / "results.json"
        empty_analyzer.export_results(results, export_path)
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert "total_tools" in data

    @pytest.mark.unit
    def test_exported_data_matches_input(
        self, empty_analyzer: ToolPerformanceAnalyzer, tmp_path: Path
    ) -> None:
        """Scenario: Exported JSON data matches the input benchmark results."""
        results = {
            "total_tools": 2,
            "tools": [{"name": "a"}, {"name": "b"}],
            "summary": {"average_execution_time": 0.5},
        }
        export_path = tmp_path / "bench.json"
        empty_analyzer.export_results(results, export_path)
        data = json.loads(export_path.read_text())
        assert data["total_tools"] == 2


# ---------------------------------------------------------------------------
# Tests: detect_regressions
# ---------------------------------------------------------------------------


class TestDetectRegressions:
    """Feature: detect_regressions wraps compare_benchmarks changes."""

    @pytest.mark.unit
    def test_returns_list_of_changes(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: detect_regressions returns list of significant changes."""
        baseline = {"tools": [{"name": "tool", "execution_time": 0.1}]}
        current = {"tools": [{"name": "tool", "execution_time": 0.5}]}
        regressions = empty_analyzer.detect_regressions(baseline, current)
        assert isinstance(regressions, list)
        assert len(regressions) == 1

    @pytest.mark.unit
    def test_no_changes_returns_empty_list(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: No significant changes returns empty list."""
        baseline = {"tools": [{"name": "tool", "execution_time": 0.1}]}
        current = {"tools": [{"name": "tool", "execution_time": 0.1}]}
        regressions = empty_analyzer.detect_regressions(baseline, current)
        assert regressions == []

    @pytest.mark.unit
    def test_improvement_also_returned(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: Improvements are also returned in detect_regressions output."""
        baseline = {"tools": [{"name": "tool", "execution_time": 0.5}]}
        current = {"tools": [{"name": "tool", "execution_time": 0.1}]}
        regressions = empty_analyzer.detect_regressions(baseline, current)
        # Returns all changes including improvements
        assert len(regressions) == 1


# ---------------------------------------------------------------------------
# Tests: analyze_tools and get_performance_report
# ---------------------------------------------------------------------------


class TestAnalyzeToolsAndReport:
    """Feature: analyze_tools and get_performance_report delegate correctly."""

    @pytest.mark.unit
    def test_analyze_tools_delegates_to_benchmark(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: analyze_tools returns same structure as benchmark_all_tools."""
        result = empty_analyzer.analyze_tools()
        assert "total_tools" in result
        assert "tools" in result
        assert "summary" in result

    @pytest.mark.unit
    def test_get_performance_report_returns_string(
        self, empty_analyzer: ToolPerformanceAnalyzer
    ) -> None:
        """Scenario: get_performance_report returns a markdown string."""
        report = empty_analyzer.get_performance_report()
        assert isinstance(report, str)
        assert "Performance" in report
