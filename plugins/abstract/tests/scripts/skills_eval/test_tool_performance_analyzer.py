"""Tests for tool performance analysis functionality."""

import json

import pytest

from abstract.skills_eval import ToolPerformanceAnalyzer

# Test constants
EXPECTED_TOOL_COUNT = 3
MAX_SCORE = 100


class TestToolPerformanceAnalyzer:
    """Test cases for ToolPerformanceAnalyzer."""

    @pytest.fixture
    def sample_tools_dir(self, tmp_path):
        """Create a temporary directory with sample tools."""
        tools_data = {
            "fast-tool.py": """#!/usr/bin/env python3
import sys

def main():
    # Fast execution
    print("Tool executed successfully")

if __name__ == "__main__":
    main()
""",
            "slow-tool.py": """#!/usr/bin/env python3
import time
import sys

def main():
    # Simulate slow operation - use 0.3s to ensure clear difference from fast tool
    # even with Python startup overhead variance
    time.sleep(0.3)
    print("Slow tool completed")

if __name__ == "__main__":
    main()
""",
            "memory-intensive-tool.py": """#!/usr/bin/env python3
import sys

def main():
    # Simulate memory-intensive operation
    large_data = ['x' * 1000 for _ in range(100)]
    print(f"Processed {len(large_data)} items")

if __name__ == "__main__":
    main()
""",
        }

        for tool_name, content in tools_data.items():
            tool_path = tmp_path / tool_name
            tool_path.write_text(content)
            tool_path.chmod(0o755)  # Make executable

        return tmp_path

    def test_analyzer_initialization(self, sample_tools_dir) -> None:
        """Test analyzer initializes correctly."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        assert analyzer.tools_dir == sample_tools_dir
        assert isinstance(analyzer.performance_metrics, dict)

    def test_discover_tools(self, sample_tools_dir) -> None:
        """Test tool discovery."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        tools = analyzer.discover_tools()

        assert len(tools) == EXPECTED_TOOL_COUNT
        tool_names = [tool["name"] for tool in tools]
        assert "fast-tool.py" in tool_names
        assert "slow-tool.py" in tool_names
        assert "memory-intensive-tool.py" in tool_names

    def test_measure_execution_time(self, sample_tools_dir) -> None:
        """Test execution time measurement."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)

        # Measure fast tool
        fast_metrics = analyzer.measure_tool_performance("fast-tool.py")
        assert "execution_time" in fast_metrics
        assert "memory_usage" in fast_metrics
        assert "cpu_usage" in fast_metrics
        assert fast_metrics["execution_time"] < 1.0  # Should be fast

    def test_compare_tool_performance(self, sample_tools_dir) -> None:
        """Test comparing performance between tools."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)

        fast_metrics = analyzer.measure_tool_performance("fast-tool.py")
        slow_metrics = analyzer.measure_tool_performance("slow-tool.py")

        # Slow tool (0.3s sleep) should take at least 0.2s longer than fast tool
        # This accounts for Python startup variance while being meaningful
        slow_time = slow_metrics["execution_time"]
        fast_time = fast_metrics["execution_time"]
        time_difference = slow_time - fast_time
        assert time_difference > 0.2, (
            f"Expected slow tool to be >0.2s slower, "
            f"but difference was {time_difference:.3f}s "
            f"(fast: {fast_time:.3f}s, slow: {slow_time:.3f}s)"
        )

    def test_benchmark_all_tools(self, sample_tools_dir) -> None:
        """Test comprehensive benchmarking of all tools."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()

        assert "total_tools" in benchmark_results
        assert "tools" in benchmark_results
        assert "summary" in benchmark_results
        assert benchmark_results["total_tools"] == EXPECTED_TOOL_COUNT
        assert len(benchmark_results["tools"]) == EXPECTED_TOOL_COUNT

    def test_identify_performance_bottlenecks(self, sample_tools_dir) -> None:
        """Test identification of performance bottlenecks."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()
        bottlenecks = analyzer.identify_bottlenecks(benchmark_results)

        assert isinstance(bottlenecks, list)
        # Should identify slow tool as a bottleneck
        bottleneck_tools = [b["tool"] for b in bottlenecks]
        assert "slow-tool.py" in bottleneck_tools

    def test_suggest_optimizations(self, sample_tools_dir) -> None:
        """Test optimization suggestions."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()
        suggestions = analyzer.suggest_optimizations(benchmark_results)

        assert isinstance(suggestions, list)
        # Should provide suggestions for slow tools
        if any(tool["name"] == "slow-tool.py" for tool in benchmark_results["tools"]):
            optimization_for_slow = [
                s for s in suggestions if "slow-tool.py" in s.get("tool", "")
            ]
            assert len(optimization_for_slow) > 0

    def test_track_performance_over_time(self, sample_tools_dir) -> None:
        """Test performance tracking across multiple runs."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)

        # First benchmark
        initial_results = analyzer.benchmark_all_tools()

        # Second benchmark (simulating change)
        second_results = analyzer.benchmark_all_tools()

        # Should be able to compare results
        comparison = analyzer.compare_benchmarks(initial_results, second_results)
        assert "changes" in comparison
        assert "improvements" in comparison
        assert "regressions" in comparison

    def test_generate_performance_report(self, sample_tools_dir) -> None:
        """Test performance report generation."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()
        report = analyzer.generate_report(benchmark_results)

        assert "Performance Analysis Report" in report
        assert "Total Tools" in report
        assert "fast-tool.py" in report
        assert "slow-tool.py" in report
        assert "Performance Summary" in report

    def test_handle_missing_tools(self, tmp_path) -> None:
        """Test handling of non-existent tools."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)

        # Should handle missing tool gracefully
        with pytest.raises((FileNotFoundError, Exception)):
            analyzer.measure_tool_performance("non-existent-tool.py")

    def test_analyze_resource_usage(self, sample_tools_dir) -> None:
        """Test resource usage analysis."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)

        # Test memory-intensive tool
        memory_metrics = analyzer.measure_tool_performance("memory-intensive-tool.py")
        assert "memory_usage" in memory_metrics
        assert memory_metrics["memory_usage"] > 0

    def test_calculate_performance_scores(self, sample_tools_dir) -> None:
        """Test performance score calculation."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()
        scores = analyzer.calculate_performance_scores(benchmark_results)

        for score_data in scores.values():
            assert "speed_score" in score_data
            assert "memory_score" in score_data
            assert "overall_score" in score_data

            # Scores should be in reasonable ranges
            assert 0 <= score_data["speed_score"] <= MAX_SCORE
            assert 0 <= score_data["memory_score"] <= MAX_SCORE
            assert 0 <= score_data["overall_score"] <= MAX_SCORE

    def test_export_performance_data(self, sample_tools_dir, tmp_path) -> None:
        """Test exporting performance data."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)
        benchmark_results = analyzer.benchmark_all_tools()

        export_file = tmp_path / "performance_data.json"
        analyzer.export_results(benchmark_results, export_file)

        assert export_file.exists()

        # Verify exported data
        with open(export_file) as f:
            exported_data = json.load(f)

        assert "total_tools" in exported_data
        assert "tools" in exported_data
        assert "summary" in exported_data

    def test_detect_performance_regressions(self, sample_tools_dir) -> None:
        """Test detection of performance regressions."""
        analyzer = ToolPerformanceAnalyzer(sample_tools_dir)

        # Initial benchmark
        baseline = analyzer.benchmark_all_tools()

        # Simulate regression (manually modify results)
        for tool in baseline["tools"]:
            tool["execution_time"] *= 2  # Double execution time

        regression_results = analyzer.benchmark_all_tools()
        regressions = analyzer.detect_regressions(baseline, regression_results)

        assert isinstance(regressions, list)
        # Should detect regressions in execution time
        assert len(regressions) > 0
