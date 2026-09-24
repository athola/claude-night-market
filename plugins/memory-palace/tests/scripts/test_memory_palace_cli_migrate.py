"""Tests for the `migrate` subcommand.

`memory_palace.migration` carried two migrations that nothing could run:
palace JSON into the knowledge graph, and sensory encoding into
computational encoding. The CLI is where a person reaches them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from scripts.memory_palace_cli import (
    MemoryPalaceCLI,
    build_parser,
    main,
)

from memory_palace.knowledge_graph import KnowledgeGraph


@pytest.fixture
def palace_dir(tmp_path: Path) -> Path:
    palaces = tmp_path / "palaces"
    palaces.mkdir()
    palace: dict[str, Any] = {
        "id": "abc12345",
        "name": "Test Palace",
        "domain": "testing",
        "metaphor": "library",
        "created": "2025-01-01T00:00:00",
        "last_modified": "2025-06-01T00:00:00",
        "layout": {
            "districts": [],
            "buildings": [],
            "rooms": [{"id": "room-arch", "name": "Architecture"}],
            "connections": [],
        },
        "associations": {
            "concept1": {"label": "Dependency Injection", "location": "room-arch"},
        },
        "sensory_encoding": {"room-arch": {"visual": "blue walls"}},
        "metadata": {"concept_count": 1, "complexity_level": "intermediate"},
    }
    (palaces / "abc12345.json").write_text(json.dumps(palace))
    return palaces


class TestParser:
    """Feature: `migrate graph` and `migrate encoding` parse."""

    @pytest.mark.parametrize("target", ["graph", "encoding"])
    def test_migrate_targets_parse(self, target: str) -> None:
        """Both targets set command, migrate_cmd and the palaces override."""
        args = build_parser().parse_args(["migrate", target, "--palaces-dir", "/p"])
        assert args.command == "migrate"
        assert args.migrate_cmd == target
        assert args.palaces_dir == "/p"

    def test_encoding_defaults_to_a_dry_run(self) -> None:
        """`migrate encoding` writes nothing until --apply is passed."""
        assert build_parser().parse_args(["migrate", "encoding"]).apply is False
        assert build_parser().parse_args(["migrate", "encoding", "--apply"]).apply


class TestDispatch:
    """Feature: main() routes each migrate target to its CLI method.

    The collaborator lives in the module under test, so patching the
    class itself would prove only that argparse reached a name. These
    patch the method on the real class, keeping the constructor and the
    argument plumbing in the test's path.
    """

    def test_graph_dispatch(self) -> None:
        """`migrate graph` reaches migrate_graph with the absent override."""
        with (
            patch("sys.argv", ["prog", "migrate", "graph"]),
            patch.object(MemoryPalaceCLI, "migrate_graph") as method,
        ):
            main()
        method.assert_called_once_with(None)

    def test_encoding_dispatch_carries_the_apply_flag(self, palace_dir: Path) -> None:
        """`migrate encoding` passes the directory override and --apply."""
        with (
            patch(
                "sys.argv",
                ["prog", "migrate", "encoding", "--palaces-dir", str(palace_dir)],
            ),
            patch.object(MemoryPalaceCLI, "migrate_encoding") as method,
        ):
            main()
        method.assert_called_once_with(str(palace_dir), apply=False)

        with (
            patch(
                "sys.argv",
                [
                    "prog",
                    "migrate",
                    "encoding",
                    "--palaces-dir",
                    str(palace_dir),
                    "--apply",
                ],
            ),
            patch.object(MemoryPalaceCLI, "migrate_encoding") as method,
        ):
            main()
        method.assert_called_once_with(str(palace_dir), apply=True)


class TestMigrateGraph:
    """Feature: palace JSON lands in the knowledge graph."""

    def test_reports_what_it_migrated(
        self, palace_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """One palace file becomes graph entities and a one-line report."""
        cli = MemoryPalaceCLI()
        graph = KnowledgeGraph(":memory:")
        manager = Mock(graph=graph, palaces_dir=str(palace_dir))
        with patch.object(cli, "_manager", return_value=manager):
            cli.migrate_graph(str(palace_dir))
        out = capsys.readouterr().out
        assert "1 palace" in out
        assert cli.had_error is False
        assert graph.get_entity("abc12345") is not None
        graph.close()


class TestMigrateEncoding:
    """Feature: sensory encodings become computational encodings in place."""

    def test_rewrites_the_palace_file(self, palace_dir: Path) -> None:
        """The palace file loses sensory_encoding and gains computational_encoding."""
        cli = MemoryPalaceCLI()
        manager = Mock(palaces_dir=str(palace_dir))
        with patch.object(cli, "_manager", return_value=manager):
            cli.migrate_encoding(None, apply=True)
        rewritten = json.loads((palace_dir / "abc12345.json").read_text())
        assert "sensory_encoding" not in rewritten
        assert "computational_encoding" in rewritten
        assert cli.had_error is False

    def test_a_dry_run_lists_the_file_and_writes_nothing(
        self, palace_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without --apply the command reports what it would change."""
        target = palace_dir / "abc12345.json"
        before = target.read_bytes()
        cli = MemoryPalaceCLI()
        manager = Mock(palaces_dir=str(palace_dir))
        with patch.object(cli, "_manager", return_value=manager):
            cli.migrate_encoding(None)

        out = capsys.readouterr().out
        assert target.read_bytes() == before
        assert "abc12345.json" in out
        assert "--apply" in out
        assert cli.had_error is False

    def test_migrate_encoding_reports_unparsable_file(
        self, palace_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A corrupt palace file is named and makes the run fail."""
        (palace_dir / "broken.json").write_text("{not json")
        cli = MemoryPalaceCLI()
        manager = Mock(palaces_dir=str(palace_dir))
        with patch.object(cli, "_manager", return_value=manager):
            cli.migrate_encoding(None, apply=True)

        assert "broken.json" in capsys.readouterr().out
        assert cli.had_error is True

    def test_a_directory_with_no_palace_files_says_so(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An empty directory is distinguishable from a rewritten one."""
        empty = tmp_path / "empty"
        empty.mkdir()
        cli = MemoryPalaceCLI()
        manager = Mock(palaces_dir=str(empty))
        with patch.object(cli, "_manager", return_value=manager):
            cli.migrate_encoding(None, apply=True)

        assert "0 palace file(s)" in capsys.readouterr().out
        assert cli.had_error is False
