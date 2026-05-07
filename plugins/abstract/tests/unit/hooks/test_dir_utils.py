"""Tests for hooks/shared/dir_utils.py.

Feature: Shared directory helpers for PreToolUse/PostToolUse hooks
(D-04).

As an abstract hook
I want one shared definition of get_observability_dir,
get_log_directory, and get_config_dir
So that the inline duplicates in pre_skill_execution.py and
skill_execution_logger.py can delete their local copies and the
behavior stays identical to abstract.utils.

The shared module must:
- Honor CLAUDE_HOME
- Always create the target directory (hooks rely on the side
  effect of mkdir before writing)
- Return paths whose final segments match the legacy literals
  (skills/observability, skills/logs, skills/discussions)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_DIR_UTILS_PATH = Path(__file__).parents[3] / "hooks" / "shared" / "dir_utils.py"
_spec = importlib.util.spec_from_file_location(
    "abstract_hooks_dir_utils",
    _DIR_UTILS_PATH,
)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["abstract_hooks_dir_utils"] = _mod
_spec.loader.exec_module(_mod)


class TestObservabilityDir:
    """Feature: shared get_observability_dir.

    Given hooks call get_observability_dir(),
    When CLAUDE_HOME points to a tmp directory,
    Then it returns ``<CLAUDE_HOME>/skills/observability`` and
    creates it on disk.
    """

    @pytest.mark.unit
    def test_returns_path_under_claude_home(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: respects CLAUDE_HOME, creates the dir."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = _mod.get_observability_dir()
        assert result == tmp_path / "skills" / "observability"
        assert result.is_dir()


class TestLogDirectory:
    """Feature: shared get_log_directory.

    Given hooks call get_log_directory(),
    When CLAUDE_HOME points to a tmp directory,
    Then it returns ``<CLAUDE_HOME>/skills/logs`` and creates it.
    """

    @pytest.mark.unit
    def test_returns_path_under_claude_home(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: respects CLAUDE_HOME, creates the dir."""
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        result = _mod.get_log_directory()
        assert result == tmp_path / "skills" / "logs"
        assert result.is_dir()


class TestConfigDir:
    """Feature: shared get_config_dir.

    Given hooks call get_config_dir(),
    When HOME points to a tmp directory,
    Then it returns ``<HOME>/.claude/skills/discussions`` and
    creates it.
    """

    @pytest.mark.unit
    def test_returns_path_under_home(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: get_config_dir resolves under HOME."""
        monkeypatch.setenv("HOME", str(tmp_path))
        # Path.home() is cached on some platforms; force it to
        # reread HOME by clearing the lru_cache if present.
        result = _mod.get_config_dir()
        assert result == tmp_path / ".claude" / "skills" / "discussions"
        assert result.is_dir()


class TestNegativePaths:
    """S11 (#484): negative paths for the three dir helpers.

    Three failure modes: CLAUDE_HOME unset (fall back to HOME),
    not-a-dir collision (target path exists as a regular file),
    and permission denial on the parent (non-root only).
    """

    @pytest.mark.unit
    def test_observability_dir_falls_back_to_home_when_claude_home_unset(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: CLAUDE_HOME unset.

        Given the env var is not set,
        When get_observability_dir is called,
        Then it falls back to ``HOME/.claude/skills/observability``
        and creates it.
        """
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        # Path.home() reads HOME at call time on POSIX.
        result = _mod.get_observability_dir()
        assert result == tmp_path / ".claude" / "skills" / "observability"
        assert result.is_dir()

    @pytest.mark.unit
    def test_log_directory_raises_when_target_exists_as_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: not-a-dir collision.

        Given ``<CLAUDE_HOME>/skills/logs`` already exists as a
        regular file (a config-bug or stale state),
        When get_log_directory is called,
        Then ``mkdir(exist_ok=True)`` surfaces ``FileExistsError``
        rather than silently succeeding or returning a broken path.
        The hook should fail loudly so the operator sees the bad
        state instead of silently writing nowhere.
        """
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        skills = tmp_path / "skills"
        skills.mkdir(parents=True)
        # Place a regular file where the directory should be.
        (skills / "logs").write_text("oops, not a directory")
        with pytest.raises(FileExistsError):
            _mod.get_log_directory()

    @pytest.mark.unit
    @pytest.mark.skipif(
        os.geteuid() == 0,
        reason="root bypasses POSIX permission bits",
    )
    def test_config_dir_raises_on_unwritable_home(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: permission denied.

        Given HOME points to a directory whose mode disallows writes,
        When get_config_dir is called,
        Then ``mkdir(parents=True)`` raises ``PermissionError`` and
        the hook surfaces the failure rather than swallowing it.
        Skipped under euid 0 because root ignores permission bits.
        """
        monkeypatch.setenv("HOME", str(tmp_path))
        # Read+execute only; no write bit.
        tmp_path.chmod(0o555)
        try:
            with pytest.raises(PermissionError):
                _mod.get_config_dir()
        finally:
            # Restore so pytest can clean up the tmp_path tree.
            tmp_path.chmod(0o755)
