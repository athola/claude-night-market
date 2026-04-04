"""Tests for stale graph.db warning in precommit hook."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(_HOOKS_DIR))

from precommit_gate import (
    _graph_staleness_warning,  # noqa: E402 - sys.path modified above
)


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


class TestGraphStalenessWarning:
    """
    Feature: Warn when graph.db is stale

    As a developer
    I want a warning when my graph is outdated
    So that I know to rebuild for accurate analysis
    """

    @pytest.mark.unit
    def test_returns_none_when_no_graph(self, gauntlet_dir: Path) -> None:
        """No graph.db means no warning."""
        result = _graph_staleness_warning(gauntlet_dir)
        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_fresh(self, gauntlet_dir: Path) -> None:
        """
        Scenario: Graph was built recently
        Given graph.db was modified < threshold ago
        When checking staleness
        Then no warning is returned
        """
        db = gauntlet_dir / "graph.db"
        db.write_bytes(b"")  # fresh file, mtime = now
        result = _graph_staleness_warning(gauntlet_dir)
        assert result is None

    @pytest.mark.unit
    def test_returns_warning_when_stale(self, gauntlet_dir: Path) -> None:
        """
        Scenario: Graph is older than threshold
        Given graph.db was modified >24h ago
        When checking staleness
        Then a warning string is returned
        """
        db = gauntlet_dir / "graph.db"
        db.write_bytes(b"")
        # Set mtime to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(db, (old_time, old_time))
        result = _graph_staleness_warning(gauntlet_dir)
        assert result is not None
        assert "stale" in result.lower() or "old" in result.lower()
        assert "gauntlet-graph build" in result

    @pytest.mark.unit
    def test_custom_threshold_from_config(self, gauntlet_dir: Path) -> None:
        """
        Scenario: Custom threshold via config
        Given config sets stale_threshold_hours to 1
        And graph.db is 2 hours old
        When checking staleness
        Then a warning is returned
        """
        import json

        (gauntlet_dir / "config.json").write_text(
            json.dumps({"stale_threshold_hours": 1})
        )
        db = gauntlet_dir / "graph.db"
        db.write_bytes(b"")
        old_time = time.time() - (2 * 3600)
        os.utime(db, (old_time, old_time))
        result = _graph_staleness_warning(gauntlet_dir)
        assert result is not None
