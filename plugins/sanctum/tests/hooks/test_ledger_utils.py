"""Tests for shared ledger path utilities."""

from __future__ import annotations

import json
from pathlib import Path

import _vendored_leyline_atomic_file
import pytest
from _ledger_utils import get_ledger_path
from deferred_item_watcher import write_ledger_entry


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

        result = get_ledger_path()
        assert result.name == "deferred-items-session.json"
        assert ".claude" in str(result)


class TestLedgerLockWithoutFlock:
    """On a platform without fcntl or msvcrt the lock is a no-op, not an error.

    The ledger takes leyline's file_lock, which still opens the
    ``<ledger>.lock`` sidecar there: it is the file Windows locks.
    """

    def test_watcher_append_succeeds_without_fcntl(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(_vendored_leyline_atomic_file, "fcntl", None)
        ledger = tmp_path / "state" / "ledger.json"

        write_ledger_entry(ledger, {"title": "[Deferred] A", "source": "s"})

        assert [e["title"] for e in json.loads(ledger.read_text())] == ["A"]
