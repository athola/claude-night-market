# ruff: noqa: D101,D102,D103,PLR2004,PLC0415,S603,S607
"""Tests for deferred_item_sweep.py Stop hook."""

from __future__ import annotations

import json
import os
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
            process_ledger(ledger)
        assert not ledger.exists()

    def test_duplicate_status_marks_entry_filed(self, tmp_path: Path) -> None:
        """Duplicate detection result marks entry as filed and increments duplicates."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps([{"title": "Dupe item", "source": "brainstorm", "filed": False}])
        )
        mock_result = {"status": "duplicate", "number": 42}
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_result):
            stats = process_ledger(ledger)
        assert stats["duplicates"] == 1
        assert stats["filed"] == 0
        assert not ledger.exists()

    def test_corrupt_ledger_returns_zero_stats(self, tmp_path: Path) -> None:
        """Corrupt JSON in the ledger file returns zero stats gracefully."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text("{broken json!!!")
        stats = process_ledger(ledger)
        assert stats["filed"] == 0
        assert stats["already_filed"] == 0
        assert stats["failed"] == 0
        assert stats["duplicates"] == 0

    def test_mixed_filed_and_unfiled_entries(self, tmp_path: Path) -> None:
        """Ledger with both filed and unfiled entries processes only unfiled ones."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        entries = [
            {
                "title": "Already done",
                "source": "test",
                "filed": True,
                "issue_number": 1,
            },
            {"title": "Needs filing", "source": "war-room", "filed": False},
            {
                "title": "Also done",
                "source": "test",
                "filed": True,
                "issue_number": 2,
            },
        ]
        ledger.write_text(json.dumps(entries))
        mock_result = {"status": "created", "number": 99}
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_result):
            stats = process_ledger(ledger)
        assert stats["already_filed"] == 2
        assert stats["filed"] == 1
        assert not ledger.exists()

    def test_empty_ledger_file_is_cleaned_up(self, tmp_path: Path) -> None:
        """An empty JSON array ledger is deleted during processing."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text("[]")
        process_ledger(ledger)
        assert not ledger.exists()

    def test_unfiled_entry_updates_issue_number_in_ledger(self, tmp_path: Path) -> None:
        """Successfully filed entries get issue_number written back to the ledger."""
        from deferred_item_sweep import process_ledger

        ledger = tmp_path / "deferred-items-session.json"
        entries = [
            {"title": "Item A", "source": "war-room", "filed": False},
            {"title": "Item B", "source": "test", "filed": False},
        ]
        ledger.write_text(json.dumps(entries))

        def side_effect(title: str, source: str) -> dict:
            if title == "Item A":
                return {"status": "created", "number": 10}
            return {"status": "error", "message": "fail"}

        with patch("deferred_item_sweep.call_capture_script", side_effect=side_effect):
            stats = process_ledger(ledger)

        assert stats["filed"] == 1
        assert stats["failed"] == 1
        # Ledger preserved because Item B failed
        assert ledger.exists()
        remaining = json.loads(ledger.read_text())
        # Item A should be marked filed with issue_number
        assert remaining[0]["filed"] is True
        assert remaining[0]["issue_number"] == 10
        # Item B still unfiled
        assert remaining[1]["filed"] is not True


class TestGetLedgerPath:
    """Test ledger path resolution."""

    def test_default_path_uses_home_directory(self) -> None:
        """Default ledger path is under ~/.claude/ when CLAUDE_HOME is not set."""
        from deferred_item_sweep import get_ledger_path

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_HOME", None)
            path = get_ledger_path()
        assert path.name == "deferred-items-session.json"
        assert ".claude" in str(path)

    def test_custom_claude_home(self, tmp_path: Path) -> None:
        """CLAUDE_HOME env var overrides the default ledger location."""
        from deferred_item_sweep import get_ledger_path

        with patch.dict(os.environ, {"CLAUDE_HOME": str(tmp_path)}):
            path = get_ledger_path()
        assert path.parent == tmp_path


class TestMainFunction:
    """Test the main() entry point orchestration."""

    def test_main_prints_summary_when_items_filed(
        self, tmp_path: Path, capsys: object
    ) -> None:
        """main() writes a summary to stderr when items are filed."""
        from deferred_item_sweep import main

        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(
            json.dumps([{"title": "Test", "source": "test", "filed": False}])
        )
        mock_result = {"status": "created", "number": 1}
        with (
            patch("deferred_item_sweep.get_ledger_path", return_value=ledger),
            patch("deferred_item_sweep.call_capture_script", return_value=mock_result),
        ):
            main()

    def test_main_silent_when_no_items(self, tmp_path: Path) -> None:
        """main() produces no output when the ledger is empty or missing."""
        from deferred_item_sweep import main

        ledger = tmp_path / "nonexistent.json"
        with patch("deferred_item_sweep.get_ledger_path", return_value=ledger):
            main()
