"""The graph-build skill must run the build where tree-sitter is installed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_SKILL = Path(__file__).resolve().parents[3] / "skills" / "graph-build" / "SKILL.md"


@pytest.mark.unit
def test_build_commands_run_in_the_plugin_environment() -> None:
    # A bare python3 may lack tree-sitter: the incremental build then
    # parsed 1123 files into nothing on this repository.
    text = _SKILL.read_text(encoding="utf-8")
    assert not re.search(r"python3\s+\S*graph_build\.py", text)
    assert text.count("uv run --project ${CLAUDE_PLUGIN_ROOT} python") >= 2
