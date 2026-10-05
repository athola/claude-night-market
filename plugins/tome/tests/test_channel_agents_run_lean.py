"""Channel agents take everything they need from their delegation prompt.

Each tome research run fans out several channel agents. Without
`omitClaudeMd` every one loads the operator's user, project and local
CLAUDE.md files (about 79 KB here), including an output style meant for
the operator's replies, not for a findings report
(code.claude.com/docs/en/sub-agents, `omitClaudeMd`, CLI 2.1.271+).
The haiku search agents also get a turn bound, so a search that loops
returns partial output instead of running on.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENTS = Path(__file__).resolve().parents[1] / "agents"
CHANNEL_AGENTS = (
    "code-searcher",
    "discourse-scanner",
    "web-searcher",
    "literature-reviewer",
    "triz-analyst",
)
BOUNDED_SEARCH_AGENTS = ("code-searcher", "discourse-scanner", "web-searcher")


def _frontmatter(name: str) -> str:
    text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("name", CHANNEL_AGENTS)
def test_channel_agent_omits_claude_md(name: str) -> None:
    assert re.search(r"^omitClaudeMd: true$", _frontmatter(name), re.MULTILINE)


@pytest.mark.parametrize("name", BOUNDED_SEARCH_AGENTS)
def test_search_agent_has_a_turn_bound(name: str) -> None:
    assert re.search(r"^maxTurns: \d+$", _frontmatter(name), re.MULTILINE)
