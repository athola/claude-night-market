"""Tests for MemoryPalaceCLI argument parser and main() dispatch.

Covers:
- build_parser() for all subcommands
- main() dispatch routing
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from scripts.memory_palace_cli import (
    build_parser,
    main,
)


class TestBuildParser:
    """Feature: CLI argument parser parses all subcommands correctly."""

    @pytest.mark.parametrize(
        "argv,expected_cmd",
        [
            (["enable"], "enable"),
            (["disable"], "disable"),
            (["status"], "status"),
            (["skills"], "skills"),
            (["install"], "install"),
            (["list"], "list"),
        ],
        ids=["enable", "disable", "status", "skills", "install", "list"],
    )
    def test_simple_commands(self, argv: list[str], expected_cmd: str) -> None:
        """Given a simple subcommand, parser sets command correctly."""
        parser = build_parser()
        args = parser.parse_args(argv)
        assert args.command == expected_cmd

    def test_create_command(self) -> None:
        """Given 'create name domain', parser sets name and domain."""
        parser = build_parser()
        args = parser.parse_args(["create", "MyPalace", "programming"])
        assert args.command == "create"
        assert args.name == "MyPalace"
        assert args.domain == "programming"
        assert args.metaphor == "building"

    def test_create_with_metaphor(self) -> None:
        """Given --metaphor, parser sets custom metaphor."""
        parser = build_parser()
        args = parser.parse_args(
            ["create", "Fort", "rust", "--metaphor", "fortress"],
        )
        assert args.metaphor == "fortress"

    def test_search_command(self) -> None:
        """Given 'search query', parser captures query and type."""
        parser = build_parser()
        args = parser.parse_args(["search", "decorators", "--type", "fuzzy"])
        assert args.command == "search"
        assert args.query == "decorators"
        assert args.type == "fuzzy"

    def test_sync_command_flags(self) -> None:
        """Given sync with flags, parser captures them."""
        parser = build_parser()
        args = parser.parse_args(["sync", "--auto-create", "--dry-run"])
        assert args.command == "sync"
        assert args.auto_create is True
        assert args.dry_run is True

    def test_prune_command(self) -> None:
        """Given 'prune --apply --stale-days 60', parser captures flags."""
        parser = build_parser()
        args = parser.parse_args(["prune", "--apply", "--stale-days", "60"])
        assert args.command == "prune"
        assert args.apply is True
        assert args.stale_days == 60

    def test_garden_metrics_command(self) -> None:
        """Given 'garden metrics', parser captures garden_cmd."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "garden",
                "metrics",
                "--path",
                "/tmp/g.json",
                "--format",
                "brief",
                "--now",
                "2025-01-01T00:00:00",
            ]
        )
        assert args.command == "garden"
        assert args.garden_cmd == "metrics"
        assert args.path == "/tmp/g.json"
        assert args.format == "brief"

    def test_garden_tend_command(self) -> None:
        """Given 'garden tend' with options, parser captures them."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "garden",
                "tend",
                "--prune-days",
                "5",
                "--stale-days",
                "14",
                "--archive-days",
                "60",
                "--apply",
                "--prometheus",
                "--palaces",
            ]
        )
        assert args.command == "garden"
        assert args.garden_cmd == "tend"
        assert args.prune_days == 5
        assert args.stale_days == 14
        assert args.archive_days == 60
        assert args.apply is True
        assert args.prometheus is True
        assert args.palaces is True

    def test_export_command(self) -> None:
        """Given 'export --destination path', parser captures dest."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "export",
                "--destination",
                "/tmp/out.json",
            ]
        )
        assert args.command == "export"
        assert args.destination == "/tmp/out.json"

    def test_import_command(self) -> None:
        """Given 'import --source path --overwrite', parser captures."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "import",
                "--source",
                "/tmp/in.json",
                "--overwrite",
            ]
        )
        assert args.command == "import"
        assert args.source == "/tmp/in.json"
        assert args.overwrite is True

    def test_manager_command(self) -> None:
        """Given 'manager delete p1', parser captures remainder."""
        parser = build_parser()
        args = parser.parse_args(["manager", "delete", "p1"])
        assert args.command == "manager"
        assert args.manager_args == ["delete", "p1"]

    def test_no_command_sets_none(self) -> None:
        """Given no arguments, command is None."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestMainDispatch:
    """Feature: main() dispatches to correct handler."""

    def test_no_command_prints_help(self) -> None:
        """Given no arguments, main prints help."""
        with patch("sys.argv", ["prog"]):
            with patch("scripts.memory_palace_cli.build_parser") as mock_bp:
                mock_parser = Mock()
                mock_parser.parse_args.return_value = Mock(command=None)
                mock_bp.return_value = mock_parser
                main()
                mock_parser.print_help.assert_called_once()

    @pytest.mark.parametrize(
        "command,method",
        [
            ("enable", "enable_plugin"),
            ("disable", "disable_plugin"),
            ("status", "show_status"),
            ("skills", "list_skills"),
            ("list", "list_palaces"),
        ],
        ids=["enable", "disable", "status", "skills", "list"],
    )
    def test_simple_command_dispatch(self, command: str, method: str) -> None:
        """Given a simple command, main calls the right CLI method."""
        with patch("sys.argv", ["prog", command]):
            with patch("scripts.memory_palace_cli.MemoryPalaceCLI") as mock_cls:
                mock_cli = Mock()
                mock_cls.return_value = mock_cli
                main()
                getattr(mock_cli, method).assert_called_once()
