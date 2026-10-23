"""Readers for the spec-kit markdown that the contract tests check.

spec-kit ships skills, commands and agents as markdown, so its behavior
is what those files tell the session to do. The contract tests read the
shipped files through these helpers rather than fixture copies.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS = PLUGIN_ROOT / "skills"
COMMANDS = PLUGIN_ROOT / "commands"
AGENTS = PLUGIN_ROOT / "agents"


def read(relative: str) -> str:
    """Return the text of a file under the plugin root."""
    return (PLUGIN_ROOT / relative).read_text(encoding="utf-8")


def frontmatter(relative: str) -> dict:
    """Return the YAML frontmatter of a markdown file under the plugin root."""
    _, block, _ = read(relative).split("---\n", 2)
    return yaml.safe_load(block)


def section(text: str, heading: str) -> str:
    """Return the text under a heading, up to the next heading of any level."""
    match = re.search(
        rf"^#+ {re.escape(heading)}[^\n]*\n(.*?)(?=^#+ |\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    assert match, f"heading {heading!r} not found"
    return match.group(1)


def headings(text: str, level: int) -> list[str]:
    """Return the headings of one level, in order, outside code fences."""
    found: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("#" * level + " "):
            found.append(line[level + 1 :].strip())
    return found
