"""Unit tests for the markdown report generator utility.

Tests section creation, table formatting, code blocks,
and complete report generation.
"""

from __future__ import annotations

import pytest

from pensive.utils.report_generator import MarkdownReportGenerator


class TestMarkdownReportGenerator:
    """Test suite for MarkdownReportGenerator utility class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.generator = MarkdownReportGenerator()

    # ========================================================================
    # create_section tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_section_default_level(self) -> None:
        """Given title with default level, creates h2 header."""
        # Act
        section = MarkdownReportGenerator.create_section("Summary")

        # Assert
        assert section == "## Summary\n"

    @pytest.mark.unit
    def test_create_section_level_1(self) -> None:
        """Given level 1, creates h1 header."""
        # Act
        section = MarkdownReportGenerator.create_section("Main Title", level=1)

        # Assert
        assert section == "# Main Title\n"

    @pytest.mark.unit
    def test_create_section_level_6(self) -> None:
        """Given level 6, creates h6 header."""
        # Act
        section = MarkdownReportGenerator.create_section("Deep Header", level=6)

        # Assert
        assert section == "###### Deep Header\n"

    # ========================================================================
    # create_list_item tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_list_item_no_indent(self) -> None:
        """Given content with no indent, creates top-level list item."""
        # Act
        item = MarkdownReportGenerator.create_list_item("First item")

        # Assert
        assert item == "- First item\n"

    @pytest.mark.unit
    def test_create_list_item_with_indent(self) -> None:
        """Given indent level, creates indented list item."""
        # Act
        item = MarkdownReportGenerator.create_list_item("Nested item", indent=1)

        # Assert
        assert item == "  - Nested item\n"

    @pytest.mark.unit
    def test_create_list_item_double_indent(self) -> None:
        """Given indent level 2, creates doubly nested item."""
        # Act
        item = MarkdownReportGenerator.create_list_item("Deep nested", indent=2)

        # Assert
        assert item == "    - Deep nested\n"

    # ========================================================================
    # create_code_block tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_code_block_no_language(self) -> None:
        """Given code without language, creates plain code block."""
        # Arrange
        code = "print('hello')"

        # Act
        block = MarkdownReportGenerator.create_code_block(code)

        # Assert
        assert block == "```\nprint('hello')\n```\n"

    @pytest.mark.unit
    def test_create_code_block_with_language(self) -> None:
        """Given code with language, creates syntax-highlighted block."""
        # Arrange
        code = 'fn main() { println!("Hello"); }'

        # Act
        block = MarkdownReportGenerator.create_code_block(code, language="rust")

        # Assert
        assert block == '```rust\nfn main() { println!("Hello"); }\n```\n'

    @pytest.mark.unit
    def test_create_code_block_multiline(self) -> None:
        """Given multiline code, preserves formatting."""
        # Arrange
        code = """def foo():
    return bar

def baz():
    return qux"""

        # Act
        block = MarkdownReportGenerator.create_code_block(code, language="python")

        # Assert
        assert "```python\n" in block
        assert "def foo():" in block
        assert "def baz():" in block
        assert "\n```\n" in block

    # ========================================================================
    # create_score_line tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_score_line_default_max(self) -> None:
        """Given score with default max, formats correctly."""
        # Act
        line = MarkdownReportGenerator.create_score_line("Quality", 8.5)

        # Assert
        assert line == "**Quality**: 8.5/10.0\n"

    @pytest.mark.unit
    def test_create_score_line_custom_max(self) -> None:
        """Given custom max score, uses that value."""
        # Act
        line = MarkdownReportGenerator.create_score_line(
            "Coverage", 75.0, max_score=100.0
        )

        # Assert
        assert line == "**Coverage**: 75.0/100.0\n"

    # ========================================================================
    # create_table_header tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_table_header_simple(self) -> None:
        """Given column names, creates valid markdown table header."""
        # Arrange
        columns = ["File", "Issues", "Severity"]

        # Act
        header = MarkdownReportGenerator.create_table_header(columns)

        # Assert
        assert "| File | Issues | Severity |" in header
        assert "| --- | --- | --- |" in header

    @pytest.mark.unit
    def test_create_table_header_single_column(self) -> None:
        """Given single column, creates minimal table."""
        # Act
        header = MarkdownReportGenerator.create_table_header(["Status"])

        # Assert
        assert "| Status |" in header
        assert "| --- |" in header

    # ========================================================================
    # create_table_row tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_table_row_values(self) -> None:
        """Given row values, creates valid markdown row."""
        # Arrange
        values = ["main.py", "3", "high"]

        # Act
        row = MarkdownReportGenerator.create_table_row(values)

        # Assert
        assert row == "| main.py | 3 | high |\n"

    @pytest.mark.unit
    def test_create_table_row_single_value(self) -> None:
        """Given single value, creates single-cell row."""
        # Act
        row = MarkdownReportGenerator.create_table_row(["Passed"])

        # Assert
        assert row == "| Passed |\n"

    # ========================================================================
    # create_report tests
    # ========================================================================

    @pytest.mark.unit
    def test_create_report_text_sections(self) -> None:
        """Given text sections, creates formatted report."""
        # Arrange
        sections = [
            {"title": "Overview", "content": "This is an overview.", "type": "text"},
            {"title": "Details", "content": "More details here.", "type": "text"},
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Test Report", sections)

        # Assert
        assert "# Test Report" in report
        assert "## Overview" in report
        assert "This is an overview." in report
        assert "## Details" in report
        assert "More details here." in report

    @pytest.mark.unit
    def test_create_report_list_sections(self) -> None:
        """Given list sections, creates bullet lists."""
        # Arrange
        sections = [
            {
                "title": "Findings",
                "content": ["Issue 1", "Issue 2", "Issue 3"],
                "type": "list",
            },
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Findings Report", sections)

        # Assert
        assert "# Findings Report" in report
        assert "## Findings" in report
        assert "- Issue 1" in report
        assert "- Issue 2" in report
        assert "- Issue 3" in report

    @pytest.mark.unit
    def test_create_report_table_section(self) -> None:
        """Given table section, creates markdown table."""
        # Arrange
        sections = [
            {
                "title": "Issues",
                "headers": ["File", "Line", "Severity"],
                "content": [
                    ["app.py", "10", "high"],
                    ["utils.py", "25", "medium"],
                ],
                "type": "table",
            },
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Issue Report", sections)

        # Assert
        assert "# Issue Report" in report
        assert "## Issues" in report
        assert "| File | Line | Severity |" in report
        assert "| app.py | 10 | high |" in report
        assert "| utils.py | 25 | medium |" in report

    @pytest.mark.unit
    def test_create_report_score_section(self) -> None:
        """Given score section, creates formatted score line."""
        # Arrange
        sections = [
            {
                "title": "Quality Score",
                "score": 8.5,
                "max_score": 10.0,
                "type": "score",
            },
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Quality Report", sections)

        # Assert
        assert "# Quality Report" in report
        assert "**Quality Score**: 8.5/10.0" in report

    @pytest.mark.unit
    def test_create_report_mixed_sections(self) -> None:
        """Given mixed section types, creates complete report."""
        # Arrange
        sections = [
            {"title": "Summary", "content": "Overview text", "type": "text"},
            {"title": "Checks", "content": ["Check 1", "Check 2"], "type": "list"},
            {"title": "Score", "score": 9.0, "max_score": 10.0, "type": "score"},
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Complete Report", sections)

        # Assert
        assert "# Complete Report" in report
        assert "Overview text" in report
        assert "- Check 1" in report
        assert "**Score**: 9.0/10.0" in report

    @pytest.mark.unit
    def test_create_report_section_without_title(self) -> None:
        """Given section without title, omits header."""
        # Arrange
        sections = [
            {"content": "Just content, no title", "type": "text"},
        ]

        # Act
        report = MarkdownReportGenerator.create_report("Report", sections)

        # Assert
        assert "# Report" in report
        assert "Just content, no title" in report
        # Should not have "## " for this section (no title)
        lines = report.split("\n")
        section_headers = [line for line in lines if line.startswith("## ")]
        assert len(section_headers) == 0
