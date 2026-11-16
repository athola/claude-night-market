"""Each release rebuilds the maintainer's gauntlet graph.

A release can change what gauntlet extraction writes. The installed-plugin
SessionStart hook covers users; this covers the release runbook, so the
graph the maintainer reviews the next branch against is never older than
the code that ships.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = REPO_ROOT / ".claude" / "skills" / "night-market-operations" / "SKILL.md"


def test_make_graph_runs_a_full_build_in_the_gauntlet_environment() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    recipe = re.search(r"^graph:.*\n((?:\t.*\n)+)", makefile, re.MULTILINE)
    assert recipe, "no graph: target in the root Makefile"
    body = recipe.group(1)
    assert "uv run --project plugins/gauntlet" in body
    assert "graph_build.py" in body
    assert "--incremental" not in body


def test_release_runbook_rebuilds_the_graph() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    section = runbook.split("## Release runbook", 1)[1].split("\n## ", 1)[0]
    assert "make graph" in section
    assert "- [ ] `make graph`" in section
