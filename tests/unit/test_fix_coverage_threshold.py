"""Tests for scripts/fix_coverage_threshold.py.

Behavior: the migration script removes --cov-fail-under from addopts
and fail_under from [tool.coverage.report], then stores the threshold
in [tool.nightmarket] so run-plugin-tests.sh can enforce it explicitly
for full-suite runs only.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

import fix_coverage_threshold as fct

CONTENT_ARRAY_ADDOPTS = textwrap.dedent("""\
    [tool.pytest.ini_options]
    addopts = [
        "-v",
        "--tb=short",
        "--cov=src/pensive",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ]

    [tool.coverage.report]
    fail_under = 90
    show_missing = true
""")

CONTENT_STRING_ADDOPTS = textwrap.dedent("""\
    [tool.pytest.ini_options]
    addopts = "-v --cov=scripts --cov-report=term-missing --cov-fail-under=90"

    [tool.coverage.report]
    fail_under = 90
    show_missing = true
""")

CONTENT_NO_ADDOPTS_FLAG = textwrap.dedent("""\
    [tool.pytest.ini_options]
    addopts = "-v --cov=leyline --cov-report=term-missing --strict-markers"

    [tool.coverage.report]
    fail_under = 90
    show_missing = true
""")

CONTENT_GAUNTLET = textwrap.dedent("""\
    [tool.pytest.ini_options]
    addopts = "-v --cov=src/gauntlet --cov-report=term-missing --cov-fail-under=85"

    [tool.coverage.report]
    fail_under = 85
    show_missing = true
""")

CONTENT_NO_COV = textwrap.dedent("""\
    [tool.pytest.ini_options]
    addopts = "-v --tb=short"
""")


class TestExtractThreshold:
    """Feature: read the existing coverage threshold from pyproject.toml content."""

    @pytest.mark.unit
    def test_reads_threshold_from_report_section(self) -> None:
        """
        Scenario: plugin has fail_under in [tool.coverage.report]
        Given content with [tool.coverage.report] fail_under = 90
        When extract_threshold is called
        Then it returns 90
        """
        assert fct.extract_threshold(CONTENT_ARRAY_ADDOPTS) == 90

    @pytest.mark.unit
    def test_reads_gauntlet_threshold_of_85(self) -> None:
        """
        Scenario: plugin uses non-default 85% threshold
        Given content with fail_under = 85
        When extract_threshold is called
        Then it returns 85
        """
        assert fct.extract_threshold(CONTENT_GAUNTLET) == 85

    @pytest.mark.unit
    def test_returns_zero_when_no_threshold_configured(self) -> None:
        """
        Scenario: plugin has no coverage threshold at all
        Given content with no fail_under or --cov-fail-under
        When extract_threshold is called
        Then it returns 0
        """
        assert fct.extract_threshold(CONTENT_NO_COV) == 0

    @pytest.mark.unit
    def test_falls_back_to_addopts_flag_when_report_section_missing(self) -> None:
        """
        Scenario: plugin has --cov-fail-under in addopts only (no config section)
        Given content with --cov-fail-under=90 in addopts only
        When extract_threshold is called
        Then it returns 90
        """
        content = '[tool.pytest.ini_options]\naddopts = "--cov-fail-under=90"\n'
        assert fct.extract_threshold(content) == 90


class TestRemoveCovFailUnder:
    """Feature: strip --cov-fail-under from addopts without touching other flags."""

    @pytest.mark.unit
    def test_removes_from_array_addopts(self) -> None:
        """
        Scenario: --cov-fail-under is a quoted item in an array addopts
        Given array-style addopts with "--cov-fail-under=90"
        When remove_cov_fail_under_from_addopts is called
        Then --cov-fail-under=90 is gone
        And other flags remain
        """
        result = fct.remove_cov_fail_under_from_addopts(CONTENT_ARRAY_ADDOPTS)
        assert "--cov-fail-under" not in result
        assert "--cov=src/pensive" in result
        assert "--tb=short" in result

    @pytest.mark.unit
    def test_removes_from_string_addopts(self) -> None:
        """
        Scenario: --cov-fail-under is inline in a string addopts value
        Given string-style addopts with --cov-fail-under=90
        When remove_cov_fail_under_from_addopts is called
        Then --cov-fail-under is gone
        And surrounding flags remain
        """
        result = fct.remove_cov_fail_under_from_addopts(CONTENT_STRING_ADDOPTS)
        assert "--cov-fail-under" not in result
        assert "--cov=scripts" in result

    @pytest.mark.unit
    def test_noop_when_flag_absent(self) -> None:
        """
        Scenario: addopts has no --cov-fail-under
        Given content without the flag
        When remove_cov_fail_under_from_addopts is called
        Then content is unchanged
        """
        result = fct.remove_cov_fail_under_from_addopts(CONTENT_NO_ADDOPTS_FLAG)
        assert result == CONTENT_NO_ADDOPTS_FLAG


class TestRemoveFailUnderFromReport:
    """Feature: strip fail_under from [tool.coverage.report] section only."""

    @pytest.mark.unit
    def test_removes_fail_under_line(self) -> None:
        """
        Scenario: [tool.coverage.report] has fail_under = 90
        Given content with that key
        When remove_fail_under_from_report_section is called
        Then fail_under is gone from that section
        """
        result = fct.remove_fail_under_from_report_section(CONTENT_ARRAY_ADDOPTS)
        assert "fail_under" not in result

    @pytest.mark.unit
    def test_preserves_other_report_keys(self) -> None:
        """
        Scenario: [tool.coverage.report] has other keys besides fail_under
        Given content with show_missing = true alongside fail_under
        When remove_fail_under_from_report_section is called
        Then show_missing = true is still present
        """
        result = fct.remove_fail_under_from_report_section(CONTENT_ARRAY_ADDOPTS)
        assert "show_missing = true" in result

    @pytest.mark.unit
    def test_noop_when_key_absent(self) -> None:
        """
        Scenario: [tool.coverage.report] has no fail_under
        Given content without fail_under in the report section
        When remove_fail_under_from_report_section is called
        Then content is unchanged
        """
        result = fct.remove_fail_under_from_report_section(CONTENT_NO_COV)
        assert result == CONTENT_NO_COV


class TestAddNightmarketSection:
    """Feature: write threshold into [tool.nightmarket] for run-plugin-tests.sh."""

    @pytest.mark.unit
    def test_adds_section_before_build_system(self) -> None:
        """
        Scenario: pyproject.toml has [build-system] section
        Given content with [build-system]
        When add_nightmarket_section is called with threshold 90
        Then [tool.nightmarket] with coverage_threshold = 90 appears before it
        """
        content = "[build-system]\nrequires = ['hatchling']\n"
        result = fct.add_nightmarket_section(content, 90)
        nm_pos = result.index("[tool.nightmarket]")
        bs_pos = result.index("[build-system]")
        assert nm_pos < bs_pos
        assert "coverage_threshold = 90" in result

    @pytest.mark.unit
    def test_appends_section_when_no_build_system(self) -> None:
        """
        Scenario: pyproject.toml has no [build-system] section
        Given content without [build-system]
        When add_nightmarket_section is called with threshold 85
        Then [tool.nightmarket] with coverage_threshold = 85 is appended
        """
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        result = fct.add_nightmarket_section(content, 85)
        assert "[tool.nightmarket]" in result
        assert "coverage_threshold = 85" in result

    @pytest.mark.unit
    def test_does_not_duplicate_section(self) -> None:
        """
        Scenario: [tool.nightmarket] already exists
        Given content that already has [tool.nightmarket]
        When add_nightmarket_section is called again
        Then only one [tool.nightmarket] section exists
        """
        content = "[tool.nightmarket]\ncoverage_threshold = 90\n"
        result = fct.add_nightmarket_section(content, 90)
        assert result.count("[tool.nightmarket]") == 1


class TestMigratePlugin:
    """Feature: end-to-end migration of a single pyproject.toml file."""

    @pytest.mark.unit
    def test_full_migration_array_addopts(self, tmp_path: Path) -> None:
        """
        Scenario: plugin with array-style addopts is migrated
        Given a pyproject.toml with --cov-fail-under=90 in array addopts
          and fail_under = 90 in [tool.coverage.report]
        When migrate_plugin is called
        Then --cov-fail-under is removed from addopts
        And fail_under is removed from [tool.coverage.report]
        And [tool.nightmarket] coverage_threshold = 90 is present
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(CONTENT_ARRAY_ADDOPTS)

        changed = fct.migrate_plugin(pyproject)

        result = pyproject.read_text()
        assert changed is True
        assert "--cov-fail-under" not in result
        assert "fail_under" not in result
        assert "coverage_threshold = 90" in result

    @pytest.mark.unit
    def test_full_migration_string_addopts(self, tmp_path: Path) -> None:
        """
        Scenario: plugin with string-style addopts is migrated
        Given a pyproject.toml with --cov-fail-under=90 inline in addopts string
        When migrate_plugin is called
        Then --cov-fail-under is removed
        And [tool.nightmarket] coverage_threshold = 90 is present
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(CONTENT_STRING_ADDOPTS)

        changed = fct.migrate_plugin(pyproject)

        result = pyproject.read_text()
        assert changed is True
        assert "--cov-fail-under" not in result
        assert "coverage_threshold = 90" in result

    @pytest.mark.unit
    def test_migration_preserves_other_addopts_flags(self, tmp_path: Path) -> None:
        """
        Scenario: migration preserves non-threshold flags
        Given content with --cov=src/pensive and --cov-fail-under=90
        When migrate_plugin is called
        Then --cov=src/pensive is still present
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(CONTENT_ARRAY_ADDOPTS)

        fct.migrate_plugin(pyproject)

        result = pyproject.read_text()
        assert "--cov=src/pensive" in result
        assert "--cov-report=term-missing" in result

    @pytest.mark.unit
    def test_skips_plugin_with_no_threshold(self, tmp_path: Path) -> None:
        """
        Scenario: plugin has no coverage threshold configured
        Given a pyproject.toml with no fail_under or --cov-fail-under
        When migrate_plugin is called
        Then the file is not modified
        And the function returns False
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(CONTENT_NO_COV)

        changed = fct.migrate_plugin(pyproject)

        assert changed is False
        assert pyproject.read_text() == CONTENT_NO_COV

    @pytest.mark.unit
    def test_dry_run_does_not_write_file(self, tmp_path: Path) -> None:
        """
        Scenario: dry-run mode previews changes without writing
        Given a pyproject.toml that would be modified
        When migrate_plugin is called with dry_run=True
        Then the file on disk is unchanged
        And the function returns True (indicating it would change)
        """
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(CONTENT_ARRAY_ADDOPTS)

        changed = fct.migrate_plugin(pyproject, dry_run=True)

        assert changed is True
        assert pyproject.read_text() == CONTENT_ARRAY_ADDOPTS
