"""Tests for the check_ruff_version pre-commit script.

Feature: Surface when the locked ruff lags the latest PyPI release

As a maintainer
I want pre-commit to tell me when ruff has fallen behind upstream
So that the single uv-managed ruff stays current deliberately
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_ruff_version as crv


def _lock(text: str, tmp_path: Path) -> Path:
    lock = tmp_path / "uv.lock"
    lock.write_text(text)
    return lock


RUFF_PINNED = """[[package]]
name = "ruff"
version = "0.14.13"
source = "registry+https://pypi.org/simple"

[[package]]
name = "other-tool"
version = "9.9.9"
"""


class TestLockedVersion:
    """Scenario: locked_version reads the ruff pin from uv.lock."""

    @pytest.mark.unit
    def test_returns_ruff_version_from_lock(self, tmp_path, monkeypatch):
        """Given uv.lock pins ruff 0.14.13, When read, Then returns 0.14.13."""
        monkeypatch.setattr(crv, "UV_LOCK", str(_lock(RUFF_PINNED, tmp_path)))
        assert crv.locked_version() == "0.14.13"

    @pytest.mark.unit
    def test_ignores_ruff_listed_only_as_a_dependency(self, tmp_path, monkeypatch):
        """Given ruff appears only in another package's dependency list,
        Then returns None.

        uv.lock lists dependencies as ``{ name = "ruff" }`` indented inside
        other packages; only a ``[[package]] name = "ruff"`` block is the
        actual pin.
        """
        text = """[[package]]
name = "claude-night-market"
version = "1.9.14"
dependencies = [
    { name = "ruff" },
]
"""
        monkeypatch.setattr(crv, "UV_LOCK", str(_lock(text, tmp_path)))
        assert crv.locked_version() is None

    @pytest.mark.unit
    def test_missing_lock_returns_none(self, tmp_path, monkeypatch):
        """Given no readable lock file, Then returns None (skip cleanly)."""
        monkeypatch.setattr(crv, "UV_LOCK", str(tmp_path / "missing.lock"))
        assert crv.locked_version() is None


class TestAsTuple:
    """Scenario: versions compare as numeric tuples, not strings."""

    @pytest.mark.unit
    def test_minor_bump_is_greater(self):
        """Given 0.14.13 and 0.15.20, Then 0.15.20 compares greater."""
        assert crv._as_tuple("0.15.20") > crv._as_tuple("0.14.13")

    @pytest.mark.unit
    def test_avoids_string_ordering_trap(self):
        """Given 0.9.0 vs 0.10.0, Then numeric order wins (not '9' > '1')."""
        assert crv._as_tuple("0.10.0") > crv._as_tuple("0.9.0")


class TestMain:
    """Scenario: main reports staleness without blocking by default."""

    @pytest.mark.unit
    def test_outdated_advisory_exits_zero_with_notice(self, monkeypatch, capsys):
        """Given locked behind latest and advisory mode,
        Then exit 0 with an actionable notice on stderr.
        """
        monkeypatch.setattr(crv, "locked_version", lambda: "0.14.13")
        monkeypatch.setattr(crv, "latest_version", lambda: "0.15.20")
        monkeypatch.setattr(crv, "OUTDATED_IS_BLOCKING", False)
        assert crv.main() == 0
        captured = capsys.readouterr()
        assert "0.14.13" in captured.err
        assert "0.15.20" in captured.err
        assert "uv lock --upgrade-package ruff" in captured.err

    @pytest.mark.unit
    def test_outdated_blocking_exits_one(self, monkeypatch):
        """Given blocking mode and stale ruff, Then exit 1."""
        monkeypatch.setattr(crv, "locked_version", lambda: "0.14.13")
        monkeypatch.setattr(crv, "latest_version", lambda: "0.15.20")
        monkeypatch.setattr(crv, "OUTDATED_IS_BLOCKING", True)
        assert crv.main() == 1

    @pytest.mark.unit
    def test_current_exits_zero(self, monkeypatch, capsys):
        """Given locked equals latest, Then exit 0 and report current."""
        monkeypatch.setattr(crv, "locked_version", lambda: "0.15.20")
        monkeypatch.setattr(crv, "latest_version", lambda: "0.15.20")
        assert crv.main() == 0
        assert "current" in capsys.readouterr().out.lower()

    @pytest.mark.unit
    def test_offline_exits_zero(self, monkeypatch, capsys):
        """Given PyPI is unreachable, Then exit 0 and skip cleanly."""
        monkeypatch.setattr(crv, "locked_version", lambda: "0.14.13")
        monkeypatch.setattr(crv, "latest_version", lambda: None)
        assert crv.main() == 0
        assert "offline" in capsys.readouterr().out.lower()

    @pytest.mark.unit
    def test_unresolvable_locked_version_exits_zero(self, monkeypatch, capsys):
        """Given the lock cannot be read, Then exit 0 and skip."""
        monkeypatch.setattr(crv, "locked_version", lambda: None)
        assert crv.main() == 0
        assert "skipping" in capsys.readouterr().out.lower()
