# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Tests for deferred_item_sweep.py Stop hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

HOOK_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOK_DIR))


class TestLedgerProcessing:
    """Stop hook processes unfiled ledger entries."""

    def test_skips_filed_entries(self, tmp_path: Path) -> None:
        """Entries with filed=True are not reprocessed."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps(
                [
                    {
                        "title": "Filed",
                        "source": "test",
                        "filed": True,
                        "issue_number": 1,
                    }
                ]
            )
        )
        with patch("deferred_item_sweep.call_capture_script") as mock:
            stats = process_ledger(ledger)
        mock.assert_not_called()
        assert stats["already_filed"] == 1

    def test_retries_unfiled_entries(self, tmp_path: Path) -> None:
        """Entries with filed=False get call_capture_script called."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps([{"title": "Unfiled", "source": "war-room", "filed": False}])
        )
        mock_result = {
            "status": "created",
            "issue_url": "https://github.com/org/repo/issues/99",
            "number": 99,
        }
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_result):
            stats = process_ledger(ledger)
        assert stats["filed"] == 1

    def test_empty_ledger_is_noop(self, tmp_path: Path) -> None:
        """Empty JSON array produces all-zero stats."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text("[]")
        stats = process_ledger(ledger)
        assert stats["filed"] == 0
        assert stats["already_filed"] == 0
        assert stats["failed"] == 0
        assert stats["duplicates"] == 0

    def test_missing_ledger_is_noop(self, tmp_path: Path) -> None:
        """Missing ledger file produces zero stats without crashing."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "nonexistent.json"
        stats = process_ledger(ledger)
        assert stats["filed"] == 0
        assert stats["already_filed"] == 0
        assert stats["failed"] == 0

    def test_ledger_preserved_when_entries_remain_unfiled(self, tmp_path: Path) -> None:
        """If call_capture_script returns error, ledger is NOT deleted."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps([{"title": "Stuck", "source": "test", "filed": False}])
        )
        mock_err = {"status": "error", "message": "gh timeout"}
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_err):
            stats = process_ledger(ledger)
        assert stats["failed"] == 1
        assert ledger.exists()

    def test_ledger_deleted_when_all_filed(self, tmp_path: Path) -> None:
        """When all entries are already filed=True, ledger is deleted."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps(
                [
                    {
                        "title": "Done",
                        "source": "test",
                        "filed": True,
                        "issue_number": 1,
                    }
                ]
            )
        )
        with patch("deferred_item_sweep.call_capture_script"):
            stats = process_ledger(ledger)
        assert not ledger.exists()
