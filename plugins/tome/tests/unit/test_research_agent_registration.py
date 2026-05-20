"""Test: tome:research is registered as a callable agent.

Issue #465: invoking ``Agent({subagent_type: "tome:research"})``
fails because the agent name is referenced by the harness but no
``research.md`` file is registered as an agent. This test pins the
fix.
"""

from __future__ import annotations

import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
AGENT_FILE = PLUGIN_ROOT / "agents" / "research.md"


def _read_agent_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    raw = text[4:end]
    out: dict[str, str] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            out[current_key] = value.strip()
        elif current_key and line.startswith(" "):
            out[current_key] += " " + line.strip()
    return out


def test_research_agent_file_exists() -> None:
    """Scenario: agents/research.md exists at the expected path.

    Given the tome plugin
    When I look for an agent named research
    Then agents/research.md is on disk.
    """
    assert AGENT_FILE.exists(), f"missing agent file: {AGENT_FILE}"


def test_research_agent_has_correct_name() -> None:
    """Scenario: agent frontmatter declares name == 'research'.

    Given agents/research.md
    When I parse the frontmatter
    Then name == 'research'.
    """
    fm = _read_agent_frontmatter(AGENT_FILE)
    assert fm.get("name") == "research"


def test_research_agent_registered_in_plugin_json() -> None:
    """Scenario: plugin.json lists agents/research.md in agents.

    Given the plugin manifest
    When I look at the agents key
    Then ./agents/research.md is present.
    """
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert "./agents/research.md" in data.get("agents", []), (
        "plugin.json must register agents/research.md so the harness "
        "loads tome:research as a dispatchable agent type"
    )


def test_research_agent_delegates_to_skill() -> None:
    """Scenario: the agent body explicitly delegates to Skill(tome:research).

    Given agents/research.md
    When I read the body
    Then it instructs the agent to invoke Skill(tome:research).
    """
    text = AGENT_FILE.read_text(encoding="utf-8")
    assert "Skill(tome:research)" in text, (
        "agent must delegate to the existing skill rather than "
        "re-implement orchestration"
    )
