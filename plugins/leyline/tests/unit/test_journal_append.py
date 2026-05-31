"""Behavior tests for the journal_append CLI wrapper.

Feature: Append decision-journal entries from the command line

    As a workflow (or developer) capturing a decision or lesson
    I want a deterministic CLI that writes a well-formed entry
    So that every consumer produces identical, ID-stable records.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from journal_append import main


class TestJournalAppendCli:
    """CLI behavior over the leyline decision-journal core."""

    @pytest.mark.unit
    def test_dry_run_prints_entry_and_writes_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: dry-run preview
        Given a project root with no journal yet
        When I append a tradeoff with --dry-run
        Then the rendered entry is printed and no file is written.
        """
        rc = main(
            [
                "tradeoffs",
                "--title",
                "Pick Postgres",
                "--field",
                "context=durable storage",
                "--project-root",
                str(tmp_path),
                "--dry-run",
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert "## TR-001: Pick Postgres" in out
        assert not (tmp_path / "docs" / "tradeoffs.md").exists()

    @pytest.mark.unit
    def test_real_write_creates_file(self, tmp_path: Path) -> None:
        """Scenario: real append
        Given a project root
        When I append a lesson via --json
        Then docs/lessons-learned.md is created with the entry.
        """
        rc = main(
            [
                "lessons",
                "--json",
                '{"title": "Cache stampede", "what_happened": "thundering herd"}',
                "--project-root",
                str(tmp_path),
            ]
        )
        target = tmp_path / "docs" / "lessons-learned.md"
        assert rc == 0
        assert target.exists()
        assert "## LL-001: Cache stampede" in target.read_text()

    @pytest.mark.unit
    def test_missing_title_returns_2(self, tmp_path: Path) -> None:
        """Scenario: missing required title
        When I append with no title
        Then the CLI exits non-zero (usage error) without writing.
        """
        rc = main(["tradeoffs", "--project-root", str(tmp_path)])
        assert rc == 2
        assert not (tmp_path / "docs" / "tradeoffs.md").exists()

    @pytest.mark.unit
    def test_malformed_json_exits_cleanly(self, tmp_path: Path) -> None:
        """Scenario: malformed --json
        When I pass invalid JSON
        Then the CLI exits with a usage error, not an uncaught traceback.
        """
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "tradeoffs",
                    "--json",
                    "{not valid",
                    "--project-root",
                    str(tmp_path),
                ]
            )
        assert "valid JSON" in str(exc.value)
        assert not (tmp_path / "docs" / "tradeoffs.md").exists()

    @pytest.mark.unit
    def test_unknown_supersede_returns_1(self, tmp_path: Path) -> None:
        """Scenario: supersede a non-existent entry
        When I supersede TR-999 in a fresh journal
        Then the CLI reports the error and exits 1.
        """
        rc = main(
            [
                "tradeoffs",
                "--title",
                "Switch approach",
                "--supersedes",
                "TR-999",
                "--project-root",
                str(tmp_path),
            ]
        )
        assert rc == 1
