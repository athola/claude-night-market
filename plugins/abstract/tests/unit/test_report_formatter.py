"""Tests for the shared validator report formatter.

Feature: Validator report formatting

As a plugin developer
I want a shared report formatter for plugin validators
So that validation reports have consistent structure
and validators avoid copy-pasting report generation logic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abstract.report_formatter import format_validator_report


class TestFormatValidatorReport:
    """Feature: format_validator_report produces consistent report output."""

    @pytest.mark.unit
    def test_report_includes_title_and_separator(self):
        """
        Scenario: Report header contains the title and a separator line.
        Given a title string
        When format_validator_report is called
        Then the first line is the title
        And the second line is a 50-char '=' separator.
        """
        result = format_validator_report(
            title="My Plugin Report",
            plugin_root=Path("/tmp/plugin"),
            skill_file_count=0,
            metadata=[],
            issues=[],
        )
        lines = result.splitlines()
        assert lines[0] == "My Plugin Report"
        assert lines[1] == "=" * 50

    @pytest.mark.unit
    def test_report_includes_plugin_root_and_skill_count(self):
        """
        Scenario: Report shows plugin root path and skill file count.
        Given a plugin root and skill file count
        When format_validator_report is called
        Then the output contains both values.
        """
        result = format_validator_report(
            title="Title",
            plugin_root=Path("/home/user/my-plugin"),
            skill_file_count=7,
            metadata=[],
            issues=[],
        )
        assert "Plugin Root: /home/user/my-plugin" in result
        assert "Skill Files: 7" in result

    @pytest.mark.unit
    def test_report_renders_metadata_pairs(self):
        """
        Scenario: Domain-specific metadata lines appear in the report.
        Given metadata tuples for domain-specific summaries
        When format_validator_report is called
        Then each label and value appears in the output.
        """
        result = format_validator_report(
            title="Title",
            plugin_root=Path("/tmp"),
            skill_file_count=0,
            metadata=[
                ("Review Skills", sorted({"a", "b"})),
                ("Evidence Patterns", sorted({"x"})),
            ],
            issues=[],
        )
        assert "Review Skills: ['a', 'b']" in result
        assert "Evidence Patterns: ['x']" in result

    @pytest.mark.unit
    def test_report_enumerates_issues_when_present(self):
        """
        Scenario: Issues are numbered in the report.
        Given a list of two issues
        When format_validator_report is called
        Then the report contains a count header and numbered entries.
        """
        result = format_validator_report(
            title="Title",
            plugin_root=Path("/tmp"),
            skill_file_count=0,
            metadata=[],
            issues=["Missing field X", "Bad pattern Y"],
        )
        assert "Issues Found (2):" in result
        assert "1. Missing field X" in result
        assert "2. Bad pattern Y" in result

    @pytest.mark.unit
    def test_report_shows_success_when_no_issues(self):
        """
        Scenario: Clean report when no issues found.
        Given an empty issues list
        When format_validator_report is called
        Then the report contains a success message.
        """
        result = format_validator_report(
            title="Title",
            plugin_root=Path("/tmp"),
            skill_file_count=0,
            metadata=[],
            issues=[],
        )
        assert "All validations passed successfully!" in result
        assert "Issues Found" not in result

    @pytest.mark.unit
    def test_report_uses_custom_success_message(self):
        """
        Scenario: Custom success message overrides the default.
        Given a custom success_message parameter
        When format_validator_report is called with no issues
        Then the report uses the custom message instead of the default.
        """
        result = format_validator_report(
            title="Title",
            plugin_root=Path("/tmp"),
            skill_file_count=0,
            metadata=[],
            issues=[],
            success_message="All review workflow skills validated successfully!",
        )
        assert "All review workflow skills validated successfully!" in result
        assert "All validations passed successfully!" not in result
