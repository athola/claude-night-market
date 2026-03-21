"""Tests for shared ledger path utilities."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestGetLedgerPath:
    """Feature: Ledger path resolution.

    As a sanctum hook
    I want a consistent ledger path
    So that deferred items are tracked across hooks
    """

    def test_returns_path_under_claude_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Scenario: CLAUDE_HOME is set.

        Given CLAUDE_HOME points to a custom directory
        When get_ledger_path is called
        Then it returns a path under that directory
        """
        monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
        from _ledger_utils import get_ledger_path

        result = get_ledger_path()
        assert result.parent == tmp_path
        assert result.name == "deferred-items-session.json"

    def test_defaults_to_home_claude_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: CLAUDE_HOME is not set.

        Given CLAUDE_HOME is unset
        When get_ledger_path is called
        Then it falls back to ~/.claude/
        """
        monkeypatch.delenv("CLAUDE_HOME", raising=False)
        from _ledger_utils import get_ledger_path

        result = get_ledger_path()
        assert result.name == "deferred-items-session.json"
        assert ".claude" in str(result)
