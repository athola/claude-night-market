"""Tests for modular_analyze.py CLI wrapper.

Feature: Skill analysis CLI wrapper
    As a developer
    I want a CLI to analyze skill complexity
    So that I can check token usage from the command line

The modular_analyze.py script is a thin CLI wrapper around
abstract.skill_tools.analyze_skill.
All logic runs inside ``if __name__ == "__main__"``, so tests
exercise it via subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "modular_analyze.py"


def _run(
    *args: str,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Run modular_analyze.py with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


class TestModularAnalyzeCLI:
    """Feature: modular_analyze.py CLI entry point.

    As a developer
    I want the CLI to accept --path and --threshold
    So that I can control analysis scope and sensitivity
    """

    @pytest.mark.unit
    def test_help_flag_exits_zero(self) -> None:
        """Scenario: --help prints usage and exits 0.
        Given no other arguments
        When --help is passed
        Then exit code is 0 and output contains 'usage'
        """
        result = _run("--help")
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "path" in result.stdout.lower()

    @pytest.mark.unit
    def test_analyze_valid_skill_file(self, tmp_path: Path) -> None:
        """Scenario: Analyzing a valid SKILL.md produces exit code 0.
        Given a temp directory with a valid SKILL.md
        When --path points to that directory
        Then exit code is 0 (no exception)
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: A test\n---\n\n# Test\n\nBody.\n"
        )
        result = _run("--path", str(skill_dir))
        assert result.returncode == 0

    @pytest.mark.unit
    def test_analyze_nonexistent_path_exits_one(self, tmp_path: Path) -> None:
        """Scenario: Analyzing a non-existent path exits with code 1.
        Given a path that does not exist
        When --path is set to that path
        Then exit code is 1
        """
        result = _run("--path", str(tmp_path / "nonexistent"))
        assert result.returncode == 1

    @pytest.mark.unit
    def test_custom_threshold_accepted(self, tmp_path: Path) -> None:
        """Scenario: --threshold is accepted without error.
        Given a valid skill directory
        When --threshold 50 is passed
        Then exit code is 0
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: A test\n---\n\n# Test\n"
        )
        result = _run("--path", str(skill_dir), "--threshold", "50")
        assert result.returncode == 0

    @pytest.mark.unit
    def test_verbose_flag_accepted(self, tmp_path: Path) -> None:
        """Scenario: --verbose flag is accepted without error.
        Given a valid skill directory
        When --verbose is passed
        Then exit code is 0
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: A test\n---\n\n# Test\n"
        )
        result = _run("--path", str(skill_dir), "--verbose")
        assert result.returncode == 0
