#!/usr/bin/env python3
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
