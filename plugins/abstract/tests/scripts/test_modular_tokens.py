"""Tests for modular_tokens.py CLI wrapper.

Feature: Token estimation CLI wrapper
    As a developer
    I want a CLI to estimate token usage for skill files
    So that I can check context window consumption

The modular_tokens.py script is a thin CLI wrapper around
abstract.skill_tools.estimate_tokens.
All logic runs inside ``if __name__ == "__main__"``, so tests
exercise it via subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "modular_tokens.py"


def _run(
    *args: str,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Run modular_tokens.py with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


class TestModularTokensCLI:
    """Feature: modular_tokens.py CLI entry point.

    As a developer
    I want the CLI to accept --file
    So that I can estimate token usage for any skill file
    """

    @pytest.mark.unit
    def test_help_flag_exits_zero(self) -> None:
        """Scenario: --help prints usage and exits 0.
        Given no other arguments
        When --help is passed
        Then exit code is 0 and output mentions 'file'
        """
        result = _run("--help")
        assert result.returncode == 0
        assert "file" in result.stdout.lower()

    @pytest.mark.unit
    def test_analyze_valid_skill_file(self, tmp_path: Path) -> None:
        """Scenario: Analyzing a valid SKILL.md exits 0.
        Given a temp directory with a valid SKILL.md
        When run from that directory with default --file
        Then exit code is 0
        """
        (tmp_path / "SKILL.md").write_text(
            "---\nname: test\ndescription: A test\n---\n\n# Test\n\nBody.\n"
        )
        result = _run(cwd=str(tmp_path))
        assert result.returncode == 0

    @pytest.mark.unit
    def test_analyze_nonexistent_file_exits_one(self, tmp_path: Path) -> None:
        """Scenario: Analyzing a non-existent file exits 1.
        Given a temp directory with no SKILL.md
        When run from that directory
        Then exit code is 1
        """
        result = _run(cwd=str(tmp_path))
        assert result.returncode == 1

    @pytest.mark.unit
    def test_custom_file_argument(self, tmp_path: Path) -> None:
        """Scenario: --file with a custom path works.
        Given a markdown file at a custom path
        When --file points to that file
        Then exit code is 0
        """
        custom = tmp_path / "custom-skill.md"
        custom.write_text(
            "---\nname: custom\ndescription: Custom\n---\n\n# Custom\n"
        )
        result = _run("--file", str(custom), cwd=str(tmp_path))
        assert result.returncode == 0

    @pytest.mark.unit
    def test_constants_defined(self) -> None:
        """Scenario: LARGE_SKILL_THRESHOLD and LARGE_FRONTMATTER_THRESHOLD are set.
        Given the modular_tokens module
        When imported
        Then threshold constants are positive integers
        """
        # Import the module directly to check constants
        mod_path = str(SCRIPT.parent)
        if mod_path not in sys.path:
            sys.path.insert(0, mod_path)
        import modular_tokens  # noqa: E402

        assert modular_tokens.LARGE_SKILL_THRESHOLD == 4000
        assert modular_tokens.LARGE_FRONTMATTER_THRESHOLD == 500
