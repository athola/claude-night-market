"""The shipped research workflow must stay loadable, honest, and bounded."""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "research.js"
README = PLUGIN_ROOT / "README.md"


def test_workflow_ships_at_the_discovered_location() -> None:
    """GIVEN the plugin as installed.

    WHEN the harness looks for workflows
    THEN it finds one at workflows/ in the plugin root
    """
    assert WORKFLOW.is_file()


def test_meta_is_the_first_statement_and_is_complete() -> None:
    """GIVEN the shipped script.

    WHEN the runtime reads meta
    THEN only comments precede it and it carries name and description
    """
    content = WORKFLOW.read_text()
    match = re.search(r"^export\s+const\s+meta\s*=", content, re.MULTILINE)
    assert match is not None
    for line in content[: match.start()].splitlines():
        stripped = line.strip()
        assert not stripped or stripped.startswith(("//", "/*", "*", "*/"))
    meta = content[match.end() : content.index("\n}\n", match.end())]
    assert "name:" in meta
    assert "description:" in meta


def test_every_channel_routes_to_a_tome_agent_that_exists() -> None:
    """GIVEN a script that names agent types.

    WHEN it dispatches a channel
    THEN the agent it names is one this plugin actually ships
    """
    content = WORKFLOW.read_text()
    named = set(re.findall(r"agentType: 'tome:([a-z-]+)'", content))
    assert named
    shipped = {p.stem for p in (PLUGIN_ROOT / "agents").glob("*.md")}
    assert named <= shipped, f"missing agents: {named - shipped}"


def test_an_empty_channel_is_distinguishable_from_a_broken_one() -> None:
    """GIVEN a channel that returns nothing.

    WHEN the workflow reports coverage
    THEN empty, failed and skipped are separate, with what was searched

    A thin topic and an error must not look alike; that distinction is
    the reason the skill records what each channel searched for.
    """
    content = WORKFLOW.read_text()
    for key in ("empty", "failed", "skipped", "searched"):
        assert f"{key}," in content or f"{key}:" in content


def test_the_readme_states_the_bundled_overlap() -> None:
    """GIVEN a harness that now bundles /deep-research.

    WHEN a reader opens the channel list
    THEN the overlap is stated rather than left to be discovered
    """
    readme = README.read_text()
    assert "/deep-research" in readme
    assert "workflows/research.js" in readme
