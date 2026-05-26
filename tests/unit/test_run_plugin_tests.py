"""Tests for scripts/run-plugin-tests.sh threshold extraction.

The script reads coverage_threshold from [tool.nightmarket] in a
plugin's pyproject.toml using awk and passes it as --cov-fail-under
to pytest for full-suite runs.  These tests verify the awk command
produces the correct threshold value for representative pyproject.toml
configurations.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "run-plugin-tests.sh"

# Awk program body — the same logic embedded in run-plugin-tests.sh.
# Reads coverage_threshold from the [tool.nightmarket] TOML section.
# Passed directly to subprocess.run (no shell quoting needed).
AWK_PROGRAM = r"""
/^\[tool\.nightmarket\]/ { in_nm=1; next }
/^\[/ { in_nm=0 }
in_nm && /^coverage_threshold[[:space:]]*=/ {
    split($0, a, "="); gsub(/[[:space:]]/, "", a[2]); print a[2]; exit
}
"""


def _run_awk(content: str, tmp_path: Path) -> str:
    """Write content to a temp pyproject.toml and run the awk command."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    result = subprocess.run(
        ["awk", AWK_PROGRAM, str(pyproject)],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class TestRunPluginTestsThresholdExtraction:
    """Feature: run-plugin-tests.sh reads coverage threshold from pyproject.toml.

    As a CI system
    I want the test runner to enforce the correct coverage threshold
    So that per-plugin thresholds are applied consistently without
    embedding them in pytest addopts (which would fail subset runs).
    """

    @pytest.mark.unit
    def test_reads_90_percent_threshold(self, tmp_path: Path) -> None:
        """
        Scenario: standard plugin with 90% coverage threshold
        Given a pyproject.toml with [tool.nightmarket] coverage_threshold = 90
        When the awk command extracts the threshold
        Then it returns "90"
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 90

            [tool.pytest.ini_options]
            addopts = ["-v", "--cov=src/pkg"]
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_reads_85_percent_threshold_for_gauntlet(self, tmp_path: Path) -> None:
        """
        Scenario: gauntlet plugin uses non-default 85% threshold
        Given a pyproject.toml with coverage_threshold = 85
        When the awk command extracts the threshold
        Then it returns "85"
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 85
        """)
        assert _run_awk(content, tmp_path) == "85"

    @pytest.mark.unit
    def test_returns_empty_when_section_absent(self, tmp_path: Path) -> None:
        """
        Scenario: plugin has no [tool.nightmarket] section
        Given a pyproject.toml without [tool.nightmarket]
        When the awk command runs
        Then it returns an empty string (no threshold enforced)
        """
        content = textwrap.dedent("""\
            [tool.pytest.ini_options]
            addopts = "-v --tb=short"
        """)
        assert _run_awk(content, tmp_path) == ""

    @pytest.mark.unit
    def test_ignores_other_tool_sections(self, tmp_path: Path) -> None:
        """
        Scenario: pyproject.toml has many [tool.*] sections
        Given content with [tool.ruff], [tool.mypy], and [tool.nightmarket]
        When the awk command extracts the threshold
        Then it reads only from [tool.nightmarket], ignoring others
        """
        content = textwrap.dedent("""\
            [tool.ruff]
            line-length = 88

            [tool.mypy]
            strict = true

            [tool.nightmarket]
            coverage_threshold = 90

            [tool.coverage.run]
            source = ["src"]
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_stops_at_first_match(self, tmp_path: Path) -> None:
        """
        Scenario: [tool.nightmarket] section has coverage_threshold followed by other keys
        Given a section with multiple keys
        When the awk command runs
        Then it returns the first coverage_threshold value and exits
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 90
            some_other_key = true
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_real_pensive_pyproject(self) -> None:
        """
        Scenario: pensive's actual pyproject.toml after migration
        Given the migrated pensive/pyproject.toml on disk
        When the awk command extracts the threshold
        Then it returns "90" (pensive uses standard 90% threshold)
        """
        pyproject = Path(__file__).parents[2] / "plugins" / "pensive" / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pensive pyproject.toml not found")
        result = subprocess.run(
            ["awk", AWK_PROGRAM.strip(), str(pyproject)],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "90"

    @pytest.mark.unit
    def test_real_gauntlet_pyproject(self) -> None:
        """
        Scenario: gauntlet's actual pyproject.toml after migration preserves 85%
        Given the migrated gauntlet/pyproject.toml on disk
        When the awk command extracts the threshold
        Then it returns "85" (gauntlet has non-default threshold)
        """
        pyproject = (
            Path(__file__).parents[2] / "plugins" / "gauntlet" / "pyproject.toml"
        )
        if not pyproject.exists():
            pytest.skip("gauntlet pyproject.toml not found")
        result = subprocess.run(
            ["awk", AWK_PROGRAM.strip(), str(pyproject)],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "85"
