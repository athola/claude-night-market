"""Third-party actions run at a fixed commit, and tool versions do not float.

A tag can be moved to other code after review. ``deploy-book.yml`` runs a
third-party action while holding ``pages: write`` and ``id-token: write``,
and it and the memory-palace cron installed whatever mdbook or uv was
newest that day. First-party ``actions/*`` and ``github/*`` stay on tags,
which ``scripts/check_pinned_versions.py`` compares against upstream. A
SHA pin is skipped by that check, so Dependabot bumps them instead.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))
USES = re.compile(
    r"uses:\s*(?P<owner>[\w.-]+)/(?P<rest>[\w./-]+)@(?P<ref>\S+)(?P<tail>.*)$"
)
FIRST_PARTY = {"actions", "github"}


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_third_party_actions_are_pinned_to_a_commit(workflow: Path) -> None:
    loose = []
    for line in workflow.read_text().splitlines():
        match = USES.search(line)
        if not match or match.group("owner") in FIRST_PARTY:
            continue
        ref, tail = match.group("ref"), match.group("tail")
        if not re.fullmatch(r"[0-9a-f]{40}", ref) or not re.search(r"#\s*v\d", tail):
            loose.append(line.strip())
    assert not loose, loose


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_no_tool_version_floats_to_latest(workflow: Path) -> None:
    text = workflow.read_text()
    assert not re.search(r"^\s*(mdbook-)?version:\s*['\"]?latest", text, re.M)


def test_dependabot_bumps_the_action_pins() -> None:
    config = (REPO_ROOT / ".github" / "dependabot.yml").read_text()
    assert "package-ecosystem: github-actions" in config
