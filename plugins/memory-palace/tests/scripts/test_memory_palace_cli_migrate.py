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


class TestDispatch:
    """Feature: main() routes each migrate target to its CLI method."""

    @pytest.mark.parametrize(
        "target,method", [("graph", "migrate_graph"), ("encoding", "migrate_encoding")]
    )
    def test_migrate_dispatch(self, target: str, method: str) -> None:
        """Each target reaches its CLI method with the (absent) override."""
        with (
            patch("sys.argv", ["prog", "migrate", target]),
            patch("scripts.memory_palace_cli.MemoryPalaceCLI") as mock_cls,
        ):
            mock_cli = Mock()
            mock_cli.had_error = False
            mock_cls.return_value = mock_cli
            main()
            getattr(mock_cli, method).assert_called_once_with(None)


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
            cli.migrate_encoding(None)
        rewritten = json.loads((palace_dir / "abc12345.json").read_text())
        assert "sensory_encoding" not in rewritten
        assert "computational_encoding" in rewritten
        assert cli.had_error is False
