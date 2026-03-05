"""Extended tests for scripts/tool_performance_analyzer.py.

Feature: Tool performance analysis
    As a developer
    I want the scripts-level ToolPerformanceAnalyzer tested
    So that tool execution timing works correctly
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


class TestToolPerformanceAnalyzerExtended:
    """Feature: ToolPerformanceAnalyzer with executable tools."""

    @pytest.mark.unit
    def test_analyze_tools_with_executable_file(self, tmp_path: Path) -> None:
        """Scenario: Directory with executable file triggers analysis loop.
        Given a directory with a simple executable script
        When analyze_tools is called
        Then total_tools is 1 and the tool is in results
        """
        from tool_performance_analyzer import ToolPerformanceAnalyzer

        # Create a simple executable Python script
        tool_file = tmp_path / "my-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 1
        assert "my-tool.py" in result["tools"]

    @pytest.mark.unit
    def test_analyze_tools_excludes_test_files(self, tmp_path: Path) -> None:
        """Scenario: Files with 'test' in name are excluded.
        Given an executable file with 'test' in its name
        When analyze_tools is called
        Then the test file is not counted as a tool
        """
        from tool_performance_analyzer import ToolPerformanceAnalyzer

        test_tool = tmp_path / "test_helper.py"
        test_tool.write_text("#!/usr/bin/env python3\npass\n")
        test_tool.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 0

    @pytest.mark.unit
    def test_analyze_tools_excludes_hidden_files(self, tmp_path: Path) -> None:
        """Scenario: Hidden files (starting with '.') are excluded."""
        from tool_performance_analyzer import ToolPerformanceAnalyzer

        hidden_tool = tmp_path / ".hidden-tool"
        hidden_tool.write_text("#!/usr/bin/env python3\npass\n")
        hidden_tool.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 0

    @pytest.mark.unit
    def test_get_performance_report_with_tools(self, tmp_path: Path) -> None:
        """Scenario: Report includes tool names when tools are present.
        Given an executable tool in the directory
        When get_performance_report is called
        Then the report includes 'Detailed Results' section
        """
        from tool_performance_analyzer import ToolPerformanceAnalyzer

        tool_file = tmp_path / "my-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        report = analyzer.get_performance_report()
        assert "Tool Performance Report" in report
        assert "my-tool.py" in report

    @pytest.mark.unit
    def test_analyze_tool_result_has_required_keys(self, tmp_path: Path) -> None:
        """Scenario: Each tool result has expected keys.
        Given an executable tool
        When analyze_tools is called
        Then the tool result dict has execution_time, exit_code, success
        """
        from tool_performance_analyzer import ToolPerformanceAnalyzer

        tool_file = tmp_path / "my-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        tool_data = result["tools"]["my-tool.py"]
        assert "execution_time" in tool_data
        assert "exit_code" in tool_data
        assert "success" in tool_data
        assert "output_length" in tool_data
