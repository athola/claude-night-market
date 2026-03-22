"""Tests for shared ledger path utilities."""

from __future__ import annotations

from pathlib import Path

import pytest
from hooks._ledger_utils import get_ledger_path


class TestGetLedgerPath:
    """
    Feature: Consistent ledger path resolution

    As a sanctum hook developer
    I want a single get_ledger_path utility
    So that all hooks resolve the ledger path consistently
    """

    @pytest.mark.unit
    def test_returns_default_path_under_home(self, tmp_path, monkeypatch):
        """
        Scenario: No CLAUDE_HOME set
        Given CLAUDE_HOME is not in the environment
        When get_ledger_path is called
        Then it returns ~/.claude/deferred-items-session.json
        """
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

        path = get_ledger_path()
        assert path.name == "deferred-items-session.json"
        assert str(tmp_path / ".claude") in str(path)

    @pytest.mark.unit
    def test_respects_claude_home_env(self, tmp_path, monkeypatch):
        """
        Scenario: CLAUDE_HOME is set
        Given CLAUDE_HOME points to a custom directory
        When get_ledger_path is called
        Then it returns the ledger path under that directory
        """
        custom_dir = tmp_path / "custom-claude"
        monkeypatch.setenv("CLAUDE_HOME", str(custom_dir))

        path = get_ledger_path()
        assert path == custom_dir / "deferred-items-session.json"

    @pytest.mark.unit
    def test_returns_path_object(self, monkeypatch):
        """
        Scenario: Return type is Path
        Given any environment configuration
        When get_ledger_path is called
        Then it returns a pathlib.Path instance
        """
        path = get_ledger_path()
        assert isinstance(path, Path)
