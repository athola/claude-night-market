"""Tests for the per-file-ignores audit hook.

Verifies that changes to [tool.ruff.lint.per-file-ignores] in
pyproject.toml are detected and blocked unless explicitly approved.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_per_file_ignores import diff_per_file_ignores, main


class TestDiffPerFileIgnores:
    """Given two TOML strings, detect newly added ignore rules."""

    def test_no_change_returns_empty(self) -> None:
        """When old and new are identical, no diff is reported."""
        toml = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "PLR2004"]
        """)
        assert diff_per_file_ignores(toml, toml) == {}

    def test_new_rule_detected(self) -> None:
        """When a new rule is added to an existing pattern, it is flagged."""
        old = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
        """)
        new = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "PLR2004"]
        """)
        result = diff_per_file_ignores(old, new)
        assert result == {"tests/**/*.py": ["PLR2004"]}

    def test_new_pattern_detected(self) -> None:
        """When an entirely new file pattern is added, all its rules are flagged."""
        old = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
        """)
        new = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
            "scripts/**/*.py" = ["E402", "S603"]
        """)
        result = diff_per_file_ignores(old, new)
        assert result == {"scripts/**/*.py": ["E402", "S603"]}

    def test_removed_rule_not_flagged(self) -> None:
        """When a rule is removed, no diff is reported."""
        old = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "PLR2004"]
        """)
        new = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
        """)
        assert diff_per_file_ignores(old, new) == {}

    def test_no_per_file_ignores_section(self) -> None:
        """When the section doesn't exist in either, no diff."""
        old = "[tool.ruff]\nline-length = 88\n"
        new = "[tool.ruff]\nline-length = 100\n"
        assert diff_per_file_ignores(old, new) == {}

    def test_section_added_from_scratch(self) -> None:
        """When per-file-ignores is added to a file that had none."""
        old = "[tool.ruff]\nline-length = 88\n"
        new = textwrap.dedent("""\
            [tool.ruff]
            line-length = 88

            [tool.ruff.lint.per-file-ignores]
            "hooks/**/*.py" = ["BLE001"]
        """)
        result = diff_per_file_ignores(old, new)
        assert result == {"hooks/**/*.py": ["BLE001"]}

    def test_multiple_patterns_changed(self) -> None:
        """When multiple patterns gain new rules."""
        old = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
            "scripts/**/*.py" = ["E402"]
        """)
        new = textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "S108"]
            "scripts/**/*.py" = ["E402", "S603", "S607"]
        """)
        result = diff_per_file_ignores(old, new)
        assert result == {
            "tests/**/*.py": ["S108"],
            "scripts/**/*.py": ["S603", "S607"],
        }


class TestMainEntrypoint:
    """Integration tests using a real git repo."""

    @pytest.fixture()
    def git_repo(self, tmp_path: Path) -> Path:
        """Create a minimal git repo with a pyproject.toml."""
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101"]
        """)
        )
        subprocess.run(
            ["git", "add", "pyproject.toml"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        return tmp_path

    def test_no_change_exits_zero(self, git_repo: Path) -> None:
        """When pyproject.toml is unchanged, exit 0."""
        pyproject = git_repo / "pyproject.toml"
        assert main([str(pyproject)], repo_root=git_repo) == 0

    def test_new_rule_exits_one(self, git_repo: Path) -> None:
        """When a new rule is added, exit 1."""
        pyproject = git_repo / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "PLR2004"]
        """)
        )
        assert main([str(pyproject)], repo_root=git_repo) == 1

    def test_override_env_var(
        self, git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When ALLOW_NEW_IGNORES=1, exit 0 even with new rules."""
        monkeypatch.setenv("ALLOW_NEW_IGNORES", "1")
        pyproject = git_repo / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [tool.ruff.lint.per-file-ignores]
            "tests/**/*.py" = ["S101", "PLR2004"]
        """)
        )
        assert main([str(pyproject)], repo_root=git_repo) == 0

    def test_non_pyproject_file_ignored(self, git_repo: Path) -> None:
        """When a non-pyproject.toml file is passed, exit 0."""
        other = git_repo / "other.py"
        other.write_text("x = 1\n")
        assert main([str(other)], repo_root=git_repo) == 0
