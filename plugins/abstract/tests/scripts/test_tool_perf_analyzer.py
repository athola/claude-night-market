"""Extended tests for scripts/tool_performance_analyzer.py.

Feature: Tool performance analysis
    As a developer
    I want the scripts-level ToolPerformanceAnalyzer tested
    So that tool execution timing works correctly
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from tool_performance_analyzer import ToolPerformanceAnalyzer


class TestToolPerformanceAnalyzerExtended:
    """Feature: ToolPerformanceAnalyzer with executable tools."""

    @pytest.mark.unit
    def test_analyze_tools_with_executable_file(self, tmp_path: Path) -> None:
        """Scenario: Directory with executable file triggers analysis loop.
        Given a directory with a simple executable script
        When analyze_tools is called
        Then total_tools is 1 and the tool is in results
        """
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
        test_tool = tmp_path / "test_helper.py"
        test_tool.write_text("#!/usr/bin/env python3\npass\n")
        test_tool.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 0

    @pytest.mark.unit
    def test_analyze_tools_excludes_hidden_files(self, tmp_path: Path) -> None:
        """Scenario: Hidden files (starting with '.') are excluded."""
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
        tool_file = tmp_path / "my-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        report = analyzer.get_performance_report()
        assert "Tool Performance Report" in report
        assert "my-tool.py" in report

    @pytest.mark.unit
    def test_status_column_shows_ok_for_success(self, tmp_path: Path) -> None:
        """Scenario: Successful tool shows 'OK' in report status column.
        Given an executable tool that exits 0
        When get_performance_report is called
        Then the report row starts with '| OK'
        """
        tool_file = tmp_path / "good-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        report = analyzer.get_performance_report()
        assert "| OK good-tool.py |" in report

    @pytest.mark.unit
    def test_status_column_shows_fail_for_failure(self, tmp_path: Path) -> None:
        """Scenario: Failed tool shows 'FAIL' in report status column.
        Given an executable tool that exits non-zero
        When get_performance_report is called
        Then the report row starts with '| FAIL'
        """
        tool_file = tmp_path / "bad-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
        tool_file.chmod(0o755)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        report = analyzer.get_performance_report()
        assert "| FAIL bad-tool.py |" in report

    @pytest.mark.unit
    def test_status_column_shows_fail_timeout(self, tmp_path: Path) -> None:
        """Scenario: Timed-out tool shows 'FAIL (timeout)' in report.
        Given analyze_tools returns a result with timeout=True
        When get_performance_report is called
        Then status includes 'FAIL (timeout)'
        """
        synthetic = {
            "total_tools": 1,
            "tools": {
                "slow-tool.py": {
                    "execution_time": 5.0,
                    "exit_code": -1,
                    "output_length": 0,
                    "success": False,
                    "timeout": True,
                },
            },
        }
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        with patch.object(analyzer, "analyze_tools", return_value=synthetic):
            report = analyzer.get_performance_report()
        assert "| FAIL (timeout) slow-tool.py |" in report

    @pytest.mark.unit
    def test_status_column_shows_fail_error(self, tmp_path: Path) -> None:
        """Scenario: Errored tool shows 'FAIL (error)' in report.
        Given analyze_tools returns a result with error=True
        When get_performance_report is called
        Then status includes 'FAIL (error)'
        """
        synthetic = {
            "total_tools": 1,
            "tools": {
                "broken-tool.py": {
                    "execution_time": 0.0,
                    "exit_code": -1,
                    "output_length": 0,
                    "success": False,
                    "error": True,
                },
            },
        }
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        with patch.object(analyzer, "analyze_tools", return_value=synthetic):
            report = analyzer.get_performance_report()
        assert "| FAIL (error) broken-tool.py |" in report

    @pytest.mark.unit
    def test_analyze_tool_result_has_required_keys(self, tmp_path: Path) -> None:
        """Scenario: Each tool result has expected keys.
        Given an executable tool
        When analyze_tools is called
        Then the tool result dict has execution_time, exit_code, success
        """
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
