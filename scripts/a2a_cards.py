#!/usr/bin/env python3
"""Generate A2A protocol agent cards for night-market agents.

Reads agent .md files across plugins and generates A2A-compliant
agent card JSON files for cross-framework agent discovery.

Usage:
    python scripts/a2a_cards.py [--output bridge/a2a/]
    python scripts/a2a_cards.py --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# D-11: shared metadata helper lives alongside this script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _plugin_meta import (  # noqa: E402 - script must inject its own dir before importing sibling helper
    get_plugin_version,
)

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "bridge" / "a2a"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

PROVIDER = {
    "organization": "Claude Night Market",
    "url": "https://github.com/athola/claude-night-market",
}

BASE_URL = "https://github.com/athola/claude-night-market"


# ---------- frontmatter parsing ----------


def parse_agent_frontmatter(content: str) -> dict[str, Any]:
    """Parse agent .md frontmatter (supports both YAML and JSON)."""
    stripped = content.strip()

    # Try JSON format first
    if stripped.startswith("{"):
        try:
            end = stripped.index("\n\n")
            json_block = stripped[:end]
        except ValueError:
            json_block = stripped
        try:
            return json.loads(json_block)
        except json.JSONDecodeError:
            pass

    # Try YAML format
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}

    raw_yaml = match.group(1)
    result: dict[str, Any] = {}

    current_key: str = ""
    multiline_lines: list[str] | None = None

    for line in raw_yaml.split("\n"):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue

        # Key-value pair at top level
        kv_match = re.match(r"^([a-zA-Z_-]+)\s*:\s*(.*)", line)
        if kv_match and not line[0].isspace():
            # Flush previous multiline
            if multiline_lines is not None and current_key:
                result[current_key] = " ".join(
                    ln for ln in multiline_lines if ln
                ).strip()
                multiline_lines = None

            current_key = kv_match.group(1).strip()
            val = kv_match.group(2).strip()

            if val == "|" or val == ">":
                multiline_lines = []
                continue

            if not val:
                result[current_key] = ""
                continue

            # Inline list
            if val.startswith("[") and val.endswith("]"):
                result[current_key] = [
                    s.strip().strip("'\"") for s in val[1:-1].split(",") if s.strip()
                ]
                continue

            result[current_key] = val.strip("'\"")
            continue

        # Multiline continuation
        if multiline_lines is not None:
            multiline_lines.append(stripped_line)
            continue

        # List items
        if stripped_line.startswith("- ") and current_key:
            prev = result.get(current_key)
            if not isinstance(prev, list):
                result[current_key] = []
            result[current_key].append(stripped_line[2:].strip().strip("'\""))

    # Flush final multiline
    if multiline_lines is not None and current_key:
        result[current_key] = " ".join(ln for ln in multiline_lines if ln).strip()

    return result


# ---------- card generation ----------


def generate_agent_card(
    fm: dict[str, Any],
    plugin_name: str,
    version: str,
) -> dict[str, Any]:
    """Generate an A2A-compliant agent card from agent metadata."""
    name = fm.get("name", "unknown")
    description = fm.get("description", "")
    if isinstance(description, list):
        description = " ".join(description)

    # Map tools to A2A skills
    tools = fm.get("tools", [])
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(",")]

    skills = []
    if tools:
        skills.append(
            {
                "id": f"{plugin_name}-{name}-tools",
                "name": f"{name} tool capabilities",
                "description": f"Agent uses: {', '.join(tools)}",
                "tags": ["tools", plugin_name],
            }
        )

    # Add a primary skill from the agent's purpose
    skills.append(
        {
            "id": f"{plugin_name}-{name}",
            "name": name,
            "description": description,
            "tags": [plugin_name, "night-market"],
            "examples": [
                f"Use the {name} agent to help with {plugin_name} tasks",
            ],
        }
    )

    card: dict[str, Any] = {
        "name": f"Night Market: {name}",
        "description": description,
        "url": f"{BASE_URL}/tree/master/plugins/{plugin_name}/agents",
        "provider": PROVIDER,
        "version": version,
        "documentationUrl": (f"{BASE_URL}/tree/master/plugins/{plugin_name}/README.md"),
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "defaultInputModes": ["text/plain", "text/markdown"],
        "defaultOutputModes": ["text/plain", "text/markdown"],
        "skills": skills,
    }

    return card


# ---------- discovery ----------


def discover_agents(
    plugins_dir: Path,
) -> list[tuple[str, str, Path]]:
    """Discover all agent .md files across plugins."""
    agents = []
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        agents_dir = plugin_dir / "agents"
        if not agents_dir.is_dir():
            continue
        for agent_file in sorted(agents_dir.glob("*.md")):
            agent_name = agent_file.stem
            agents.append((plugin_dir.name, agent_name, agent_file))
    return agents


# ---------- batch generation ----------


def generate_all_cards(
    plugins_dir: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Generate A2A agent cards for all agents."""
    output_dir.mkdir(parents=True, exist_ok=True)

    agents = discover_agents(plugins_dir)
    cards = []

    for plugin_name, agent_name, agent_path in agents:
        content = agent_path.read_text(encoding="utf-8")
        fm = parse_agent_frontmatter(content)

        if not fm.get("name"):
            fm["name"] = agent_name

        version = get_plugin_version(plugins_dir / plugin_name)
        card = generate_agent_card(fm, plugin_name, version)
        cards.append(card)

        # Write individual card
        card_file = output_dir / f"{plugin_name}-{agent_name}.json"
        card_file.write_text(json.dumps(card, indent=2) + "\n")

    # Write combined roster
    roster = {
        "schemaVersion": "1.0",
        "generator": "claude-night-market/a2a-cards",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_agents": len(cards),
        "agents": cards,
    }
    (output_dir / "agent-cards.json").write_text(json.dumps(roster, indent=2) + "\n")

    return cards


# ---------- CLI ----------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate A2A agent cards for night-market agents"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: bridge/a2a/)",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=PLUGINS_DIR,
        help="Plugins directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discoverable agents",
    )

    args = parser.parse_args()

    if args.list:
        agents = discover_agents(args.plugins_dir)
        print(f"Found {len(agents)} agents:")
        for plugin, name, _ in agents:
            print(f"  {plugin}:{name}")
        return

    cards = generate_all_cards(args.plugins_dir, args.output)
    print(f"Generated {len(cards)} A2A agent cards in {args.output}/")


if __name__ == "__main__":
    main()
