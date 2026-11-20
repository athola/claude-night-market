"""Each release rebuilds the maintainer's gauntlet graph.

A release can change what gauntlet extraction writes. The installed-plugin
SessionStart hook covers users; this covers the release runbook, so the
graph the maintainer reviews the next branch against is never older than
the code that ships.
"""

from __future__ import annotations

import re
import shlex
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

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


def _make_graph_argv() -> list[str]:
    """The command ``make graph`` runs, as make expands it."""
    dry = subprocess.run(
        ["make", "-n", "graph"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in dry.stdout.splitlines() if "graph_build.py" in line]
    assert len(lines) == 1, dry.stdout
    return shlex.split(lines[0])


@pytest.mark.skipif(shutil.which("make") is None, reason="needs make")
def test_make_graph_names_a_script_that_exists_with_no_incremental_flag() -> None:
    """A grep of the recipe passed a wrong script path or a broken argument."""
    argv = _make_graph_argv()
    script = next(arg for arg in argv if arg.endswith("graph_build.py"))
    assert (REPO_ROOT / script).is_file(), script
    assert "--incremental" not in argv
    assert argv[-1] == "."


@pytest.mark.skipif(
    shutil.which("make") is None or shutil.which("uv") is None,
    reason="needs make and uv",
)
def test_make_graph_records_a_full_build(tmp_path: Path) -> None:
    """Run the expanded recipe on a two-file tree and read the graph back."""
    (tmp_path / "a.py").write_text("def f():\n    return g()\n")
    (tmp_path / "b.py").write_text("def g():\n    return 1\n")
    argv = [*_make_graph_argv()[:-1], str(tmp_path)]
    built = subprocess.run(
        argv, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=300
    )
    assert built.returncode == 0, built.stdout + built.stderr
    with sqlite3.connect(tmp_path / ".gauntlet" / "graph.db") as conn:
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = 'last_build_type'"
        ).fetchone()
    assert row == ("full",)


def test_release_runbook_rebuilds_the_graph() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    section = runbook.split("## Release runbook", 1)[1].split("\n## ", 1)[0]
    assert "make graph" in section
    assert "- [ ] `make graph`" in section
