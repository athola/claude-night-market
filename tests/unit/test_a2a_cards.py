"""Tests for a2a_cards.py — A2A agent card generator.

Feature: Generate A2A protocol agent cards for night-market agents

As a night-market maintainer
I want to publish agents as A2A-compatible agent cards
So that any A2A-compatible framework can discover and delegate to them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from a2a_cards import (
    generate_agent_card,
    generate_all_cards,
    parse_agent_frontmatter,
)


@pytest.fixture()
def yaml_agent_md() -> str:
    """Agent file with YAML frontmatter."""
    return """\
---
name: code-reviewer
description: |
  Expert code review agent specializing in bug detection, API analysis, test
  quality, and detailed code audits.
tools: [Read, Write, Edit, Bash, Glob, Grep]
model: sonnet
---

# Code Reviewer Agent

Reviews code.
"""


@pytest.fixture()
def json_agent_md() -> str:
    """Agent file with JSON frontmatter."""
    return """\
{
  "name": "meta-architect",
  "description": "Agent for architectural guidance and structural optimization",
  "version": "1.0.0",
  "type": "architecture"
}

# Meta Architect

Designs architectures.
"""


@pytest.fixture()
def tmp_agents(tmp_path: Path) -> Path:
    """Create a temporary plugin structure with agents."""
    pensive = tmp_path / "pensive"
    pensive_agents = pensive / "agents"
    pensive_agents.mkdir(parents=True)
    pensive_plugin = pensive / ".claude-plugin"
    pensive_plugin.mkdir()
    (pensive_plugin / "plugin.json").write_text(
        json.dumps({"name": "pensive", "version": "1.7.0"})
    )

    (pensive_agents / "code-reviewer.md").write_text(
        """\
---
name: code-reviewer
description: Expert code review agent for bug detection and audits.
tools: [Read, Write, Bash, Glob, Grep]
model: sonnet
---

# Code Reviewer
"""
    )

    (pensive_agents / "architecture-reviewer.md").write_text(
        """\
---
name: architecture-reviewer
description: Architecture review for system design and coupling analysis.
tools: [Read, Bash, Glob, Grep]
---

# Architecture Reviewer
"""
    )

    return tmp_path


class TestParseAgentFrontmatter:
    """
    Feature: Parse agent frontmatter from both YAML and JSON formats

    As a card generator
    I want to read agent metadata from .md files
    So that I can translate them to A2A agent cards.
    """

    @pytest.mark.unit
    def test_parses_yaml_frontmatter(self, yaml_agent_md: str) -> None:
        """
        Scenario: YAML frontmatter agent file
        Given an agent .md with YAML frontmatter
        When I parse it
        Then name and description are extracted.
        """
        fm = parse_agent_frontmatter(yaml_agent_md)
        assert fm["name"] == "code-reviewer"
        assert "code review" in fm["description"]

    @pytest.mark.unit
    def test_parses_json_frontmatter(self, json_agent_md: str) -> None:
        """
        Scenario: JSON frontmatter agent file
        Given an agent .md with JSON object at the top
        When I parse it
        Then name and description are extracted.
        """
        fm = parse_agent_frontmatter(json_agent_md)
        assert fm["name"] == "meta-architect"
        assert "architectural" in fm["description"]


class TestGenerateAgentCard:
    """
    Feature: Generate A2A-compliant agent cards

    As a publisher
    I want to generate valid A2A agent cards
    So that other frameworks can discover night-market agents.
    """

    @pytest.mark.unit
    def test_generates_valid_card(self) -> None:
        """
        Scenario: Generate card from agent metadata
        Given agent metadata with name and description
        When I generate an A2A card
        Then it has all required A2A fields.
        """
        fm = {
            "name": "code-reviewer",
            "description": "Expert code review agent",
            "tools": ["Read", "Write", "Bash"],
        }
        card = generate_agent_card(fm, "pensive", "1.7.0")

        assert card["name"] == "Night Market: code-reviewer"
        assert card["version"] == "1.7.0"
        assert "url" in card
        assert "provider" in card
        assert "skills" in card
        assert isinstance(card["skills"], list)
        assert len(card["skills"]) > 0

    @pytest.mark.unit
    def test_card_has_capabilities(self) -> None:
        """
        Scenario: Card declares capabilities
        Given agent metadata
        When I generate an A2A card
        Then capabilities reflect the agent's nature.
        """
        fm = {"name": "test", "description": "test agent"}
        card = generate_agent_card(fm, "test", "1.0.0")

        assert "capabilities" in card
        assert isinstance(card["capabilities"], dict)

    @pytest.mark.unit
    def test_card_includes_input_output_modes(self) -> None:
        """
        Scenario: Card declares I/O modes
        Given agent metadata
        When I generate an A2A card
        Then default input/output modes are set.
        """
        fm = {"name": "test", "description": "test agent"}
        card = generate_agent_card(fm, "test", "1.0.0")

        assert "defaultInputModes" in card
        assert "defaultOutputModes" in card
        assert "text/plain" in card["defaultInputModes"]


class TestGenerateAllCards:
    """
    Feature: Batch generate agent cards for all plugins

    As a maintainer
    I want to generate cards for all agents at once
    So that the full roster is discoverable.
    """

    @pytest.mark.unit
    def test_discovers_and_generates_cards(
        self, tmp_agents: Path, tmp_path: Path
    ) -> None:
        """
        Scenario: Generate cards for all agents
        Given a plugins directory with 2 agents
        When I generate all cards
        Then 2 card files are created.
        """
        output = tmp_path / "a2a-out"
        cards = generate_all_cards(tmp_agents, output)

        assert len(cards) == 2
        assert (output / "agent-cards.json").exists()

        roster = json.loads((output / "agent-cards.json").read_text())
        assert len(roster["agents"]) == 2
