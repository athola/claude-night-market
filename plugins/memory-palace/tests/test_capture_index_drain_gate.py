"""The staged capture index must carry no undrained captures.

``scripts/precommit_palace_maintenance.sh`` runs the promote and
prune-orphans drain on every commit, then re-stages what changed. That
drain has three outcomes per entry, not two: promote, archive, and
**hold** (``index_promoter`` module docstring). A held entry keeps
``routing_type: pending``, so a converged drain does not by itself prove
the index is empty of undrained captures.

This gate closes that gap. It reads the index the commit is about to
carry and fails when any entry is still ``pending``, naming the keys and
the curate command. The invariant it defends: a committed
``memory-palace-index.yaml`` has zero pending entries.

The gate keys on ``routing_type`` alone, not on
``index_analytics._is_inert``, which additionally requires the default
maturity and importance score. A half-processed entry that was scored
but never routed is exactly the case the drain still owes work on, and
the stricter three-field test would wave it through.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_CHECK_PATH = _PLUGIN_ROOT / "scripts" / "check_capture_index_drained.py"


def _load_check_module():
    """Import the gate script by path; it is not an installed module."""
    sys.path.insert(0, str(_PLUGIN_ROOT / "src"))
    if "check_capture_index_drained" in sys.modules:
        return sys.modules["check_capture_index_drained"]
    spec = importlib.util.spec_from_file_location(
        "check_capture_index_drained", _CHECK_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_capture_index_drained"] = module
    spec.loader.exec_module(module)
    return module


def _entry(routing_type: str, **overrides: Any) -> dict[str, Any]:
    """Build one index entry at the given routing type."""
    entry = {
        "content_hash": "sha256:abcd",
        "stored_at": "data/staging/capture.md",
        "importance_score": 76,
        "last_updated": "2026-07-01T00:00:00+00:00",
        "title": "Capture",
        "maturity": "growing",
        "routing_type": routing_type,
    }
    entry.update(overrides)
    return entry


def _write_index(tmp_path: Path, entries: dict[str, dict[str, Any]]) -> Path:
    """Persist an index file and return its path."""
    path = tmp_path / "memory-palace-index.yaml"
    path.write_text(
        yaml.safe_dump({"entries": entries, "hashes": {}}, sort_keys=False),
        encoding="utf-8",
    )
    return path


class TestPendingKeys:
    """The pure classification the gate reports on."""

    def test_drained_entries_yield_no_keys(self) -> None:
        """GIVEN every entry routed
        WHEN pending keys are collected
        THEN none are reported.
        """
        check = _load_check_module()
        index = {
            "entries": {
                "https://example.com/a": _entry("meta"),
                "https://example.com/b": _entry("archived"),
                "https://example.com/c": _entry("local"),
            }
        }
        assert check.pending_keys(index) == []

    def test_pending_entry_is_reported(self) -> None:
        """GIVEN one entry left at the capture default
        WHEN pending keys are collected
        THEN that key is reported.
        """
        check = _load_check_module()
        index = {
            "entries": {
                "https://example.com/a": _entry("meta"),
                "https://example.com/b": _entry("pending"),
            }
        }
        assert check.pending_keys(index) == ["https://example.com/b"]

    def test_scored_but_unrouted_entry_is_reported(self) -> None:
        """GIVEN an entry scored and matured but never routed
        WHEN pending keys are collected
        THEN it is reported, because the drain still owes it work.

        This is the case ``_is_inert`` misses: it requires all three
        capture defaults, and this entry carries only one.
        """
        check = _load_check_module()
        index = {
            "entries": {
                "https://example.com/b": _entry(
                    "pending", importance_score=88, maturity="evergreen"
                )
            }
        }
        assert check.pending_keys(index) == ["https://example.com/b"]

    def test_entry_missing_routing_type_is_reported(self) -> None:
        """GIVEN an entry written before routing_type existed
        WHEN pending keys are collected
        THEN it is reported rather than silently passing.
        """
        check = _load_check_module()
        entry = _entry("meta")
        del entry["routing_type"]
        assert check.pending_keys({"entries": {"https://example.com/a": entry}}) == [
            "https://example.com/a"
        ]


class TestGateExitStatus:
    """The commit-blocking behavior the pre-commit hook depends on."""

    def test_drained_index_exits_zero(self, tmp_path: Path) -> None:
        """GIVEN a fully drained index
        WHEN the gate runs
        THEN it exits 0.
        """
        check = _load_check_module()
        path = _write_index(tmp_path, {"https://example.com/a": _entry("meta")})
        assert check.main([str(path)]) == 0

    def test_pending_index_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an index with an undrained capture
        WHEN the gate runs
        THEN it exits nonzero and names the key.
        """
        check = _load_check_module()
        path = _write_index(tmp_path, {"https://example.com/b": _entry("pending")})

        assert check.main([str(path)]) == 1

        output = capsys.readouterr().err
        assert "https://example.com/b" in output

    def test_failure_names_the_remediation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a blocked commit
        WHEN the gate reports
        THEN the message carries the command that resolves it.

        A gate that blocks without saying how to proceed trains people
        to reach for --no-verify.
        """
        check = _load_check_module()
        path = _write_index(tmp_path, {"https://example.com/b": _entry("pending")})
        check.main([str(path)])

        output = capsys.readouterr().err
        assert "index promote --apply" in output

    def test_long_backlog_is_truncated(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a large pending backlog
        WHEN the gate reports
        THEN it lists a bounded sample and counts the remainder.

        The 47-entry backlog of 2ed3737b would otherwise bury the
        remediation line under its own output.
        """
        check = _load_check_module()
        entries = {f"https://example.com/{i}": _entry("pending") for i in range(40)}
        path = _write_index(tmp_path, entries)

        assert check.main([str(path)]) == 1

        output = capsys.readouterr().err
        assert output.count("https://example.com/") <= check.MAX_LISTED
        assert "40 pending" in output

    def test_missing_index_exits_zero(self, tmp_path: Path) -> None:
        """GIVEN no index file in this tree
        WHEN the gate runs
        THEN it exits 0.

        A worktree without the capture corpus has nothing to drain, and
        the sibling prune guard (test_index_prune_cli_guard) establishes
        that such a tree must not fail the commit.
        """
        check = _load_check_module()
        assert check.main([str(tmp_path / "absent.yaml")]) == 0
