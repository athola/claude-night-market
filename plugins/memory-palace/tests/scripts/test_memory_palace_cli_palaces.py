"""Tests for MemoryPalaceCLI palace CRUD and related operations.

Covers:
- list_skills(), install_skills()
- create_palace(), list_palaces()
- sync_queue()
- prune_check(), prune_apply()
- search_palaces()
- run_palace_manager()
- export_palaces(), import_palaces()
- _palaces_dir() resolution
- prune check duplicate reporting
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from scripts.memory_palace_cli import MemoryPalaceCLI

from memory_palace.palace_manager import MemoryPalaceManager


class TestListSkills:
    """Feature: List available skills from the skills directory."""

    def test_lists_skills(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given skills directory with skill folders, list them."""
        cli = MemoryPalaceCLI()
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "test-skill").mkdir()
        skill_md = skills_dir / "test-skill" / "SKILL.md"
        skill_md.write_text(
            "---\ndescription: A test skill\n---\n# Test\n",
            encoding="utf-8",
        )
        cli.plugin_dir = tmp_path
        cli.list_skills()
        out = capsys.readouterr().out
        assert "Available" in out

    def test_no_skills_directory_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no skills directory, print warning."""
        cli = MemoryPalaceCLI()
        cli.plugin_dir = tmp_path
        cli.list_skills()
        out = capsys.readouterr().out
        assert "[WARN]" in out


class TestCreatePalace:
    """Feature: Create a new memory palace."""

    def test_creates_palace_returns_true(self) -> None:
        """Given valid name and domain, create returns True."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.create_palace.return_value = {"id": "new-1"}

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.create_palace("Test", "testing", "building")

        assert result is True
        mock_manager.create_palace.assert_called_once_with(
            "Test",
            "testing",
            "building",
        )

    def test_empty_name_returns_false(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given empty name, returns False with error."""
        cli = MemoryPalaceCLI()
        result = cli.create_palace("", "testing")
        assert result is False
        assert "[ERROR]" in capsys.readouterr().out

    def test_empty_domain_returns_false(self) -> None:
        """Given empty domain, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.create_palace("Test", "") is False

    def test_manager_error_returns_false(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager raises, returns False with error."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.create_palace.side_effect = OSError("disk full")

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.create_palace("Test", "testing")

        assert result is False
        assert "Failed to create palace" in capsys.readouterr().out


class TestListPalaces:
    """Feature: List all memory palaces."""

    def test_lists_palaces_with_details(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given palaces exist, print their details."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.return_value = [
            {"id": "p1", "name": "Palace One", "domain": "d1", "concept_count": 5},
        ]

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.list_palaces()

        assert result is True
        out = capsys.readouterr().out
        assert "Palace One" in out
        assert "Total: 1 palaces" in out
        mock_manager.list_palaces.assert_called_once()

    def test_empty_list_shows_hint(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no palaces, print creation hint."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.return_value = []

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.list_palaces()

        assert result is True
        assert "/palace create" in capsys.readouterr().out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.side_effect = OSError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.list_palaces() is False


class TestSyncQueue:
    """Feature: Sync intake queue into palaces."""

    def test_sync_with_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given processed items, print summary."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.return_value = {
            "processed": 5,
            "skipped": 1,
            "palaces_updated": ["p1"],
            "palaces_created": [],
            "unmatched": ["q1", "q2"],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.sync_queue(auto_create=False, dry_run=False)

        assert result is True
        out = capsys.readouterr().out
        assert "Processed: 5" in out
        assert "Skipped: 1" in out
        assert "Unmatched queries: 2" in out
        mock_manager.sync_from_queue.assert_called_once()

    def test_dry_run_header(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given dry_run=True, print DRY RUN header."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.return_value = {
            "processed": 0,
            "skipped": 0,
            "palaces_updated": [],
            "palaces_created": [],
            "unmatched": [],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.sync_queue(dry_run=True)

        assert "DRY RUN" in capsys.readouterr().out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.side_effect = FileNotFoundError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.sync_queue() is False


class TestPruneCheckCLI:
    """Feature: CLI prune check reports palace health."""

    def test_healthy_palaces(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no issues found, print healthy message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 2,
            "total_stale": 0,
            "total_low_quality": 0,
            "total_duplicates": 0,
            "recommendations": [],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_check(stale_days=90)

        assert result is True
        assert "healthy" in capsys.readouterr().out.lower()
        mock_manager.prune_check.assert_called_once_with(stale_days=90)

    def test_stale_entries_reported(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given stale entries, print recommendations."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 1,
            "total_stale": 3,
            "total_low_quality": 0,
            "total_duplicates": 0,
            "recommendations": [
                {
                    "palace_name": "Old Palace",
                    "palace_id": "old-1",
                    "stale": ["e1", "e2", "e3"],
                    "low_quality": [],
                },
            ],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.prune_check()

        out = capsys.readouterr().out
        assert "Stale entries" in out
        assert "3 stale entries" in out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.side_effect = OSError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.prune_check() is False


class TestPruneApply:
    """Feature: Apply prune actions after user approval."""

    def test_applies_prune(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given recommendations, apply_prune removes entries."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "recommendations": [{"palace_id": "p1"}],
        }
        mock_manager.apply_prune.return_value = {
            "stale": 2,
            "low_quality": 1,
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_apply(["stale", "low_quality"])

        assert result is True
        out = capsys.readouterr().out
        assert "Stale removed: 2" in out
        assert "Low quality removed: 1" in out
        mock_manager.apply_prune.assert_called_once()

    def test_no_cleanup_needed(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no recommendations, print clean message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {"recommendations": []}

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_apply(["stale"])

        assert result is True
        assert "No cleanup" in capsys.readouterr().out


class TestSearchPalaces:
    """Feature: Search across all palaces."""

    def test_search_with_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given matching entries, print results."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.return_value = [
            {
                "palace_name": "Python Palace",
                "palace_id": "p1",
                "matches": [
                    {"type": "association", "concept_id": "decorators"},
                ],
            },
        ]

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.search_palaces("decorators", "semantic")

        assert result is True
        out = capsys.readouterr().out
        assert "Python Palace" in out
        assert "decorators" in out
        mock_manager.search_palaces.assert_called_once_with(
            "decorators",
            "semantic",
        )

    def test_no_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no matches, print no-match message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.return_value = []

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.search_palaces("nonexistent")

        assert result is True
        assert "No matches" in capsys.readouterr().out

    def test_empty_query_returns_false(self) -> None:
        """Given empty query, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.search_palaces("") is False

    def test_search_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.side_effect = FileNotFoundError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.search_palaces("test") is False


class TestInstallSkills:
    """Feature: Install skills into Claude's skill directory."""

    def test_install_success(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given valid directories, install copies skills."""
        cli = MemoryPalaceCLI()

        # Create source skills
        source_skills = tmp_path / "plugin" / "skills"
        source_skills.mkdir(parents=True)
        (source_skills / "test-skill").mkdir()
        (source_skills / "test-skill" / "SKILL.md").write_text("# Test")
        cli.plugin_dir = tmp_path / "plugin"

        # Create target skills dir
        claude_skills = tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        with patch.object(Path, "home", return_value=tmp_path):
            result = cli.install_skills()

        assert result is True
        installed = claude_skills / "memory-palace" / "test-skill" / "SKILL.md"
        assert installed.exists()

    def test_no_skills_dir_returns_false(self, tmp_path: Path) -> None:
        """Given no source skills directory, returns False."""
        cli = MemoryPalaceCLI()
        cli.plugin_dir = tmp_path  # no skills subdirectory

        claude_skills = tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        with patch.object(Path, "home", return_value=tmp_path):
            assert cli.install_skills() is False


class TestRunPalaceManager:
    """Feature: Forward manager subcommands."""

    def test_delete_command(self) -> None:
        """Given 'delete <id>', deletes palace."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.delete_palace.return_value = True

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["delete", "p1"])

        assert result is True
        mock_manager.delete_palace.assert_called_once_with("p1")

    def test_delete_nonexistent(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given 'delete <nonexistent>', prints error."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.delete_palace.return_value = False

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["delete", "bad-id"])

        assert result is False
        assert "not found" in capsys.readouterr().out

    def test_status_command(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given 'status', prints index stats."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.get_master_index.return_value = {
            "global_stats": {
                "total_palaces": 3,
                "total_concepts": 10,
                "domains": {"testing": 2, "math": 1},
            },
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["status"])

        assert result is True
        out = capsys.readouterr().out
        assert "Total palaces: 3" in out
        assert "testing: 2 palaces" in out

    def test_unknown_command_warns(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given unknown subcommand, prints warning."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["unknown-cmd"])

        assert result is False
        assert "not supported" in capsys.readouterr().out

    def test_no_args_returns_false(self) -> None:
        """Given empty args, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.run_palace_manager([]) is False


class TestExportImportCLI:
    """Feature: Export and import palaces via CLI methods."""

    def test_export_delegates_to_manager(self) -> None:
        """Given a destination, export delegates to manager."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.export_palaces("/tmp/out.json", palaces_dir="/tmp/p")

        mock_manager.export_state.assert_called_once_with("/tmp/out.json")

    def test_export_error_prints_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager error, print error message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.export_state.side_effect = FileNotFoundError("write err")

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.export_palaces("/tmp/out.json")

        assert "Export failed" in capsys.readouterr().out

    def test_import_delegates_to_manager(self) -> None:
        """Given a source, import delegates to manager."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.import_palaces("/tmp/in.json", keep_existing=False)

        mock_manager.import_state.assert_called_once_with(
            "/tmp/in.json",
            keep_existing=False,
        )

    def test_import_error_prints_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager error, print error message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.import_state.side_effect = FileNotFoundError("read err")

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.import_palaces("/tmp/in.json")

        assert "Import failed" in capsys.readouterr().out


class TestPalacesDir:
    """Feature: _palaces_dir resolution."""

    def test_override_takes_precedence(self) -> None:
        """Given override value, use it."""
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir("/custom") == "/custom"

    def test_falls_back_to_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given no override, use PALACES_DIR env var."""
        monkeypatch.setenv("PALACES_DIR", "/from/env")
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir() == "/from/env"

    def test_returns_none_when_no_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given no override and no env var, returns None."""
        monkeypatch.delenv("PALACES_DIR", raising=False)
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir() is None


class TestPruneCheckDuplicates:
    """Feature: Prune check reports duplicate entries."""

    def test_duplicates_shown(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given duplicates in results, print them."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 2,
            "total_stale": 0,
            "total_low_quality": 0,
            "total_duplicates": 1,
            "recommendations": [],
            "duplicates": [
                {
                    "query": "shared topic",
                    "locations": ["dup-a", "dup-b"],
                },
            ],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.prune_check()

        out = capsys.readouterr().out
        assert "Duplicates found" in out
        assert "shared topic" in out
