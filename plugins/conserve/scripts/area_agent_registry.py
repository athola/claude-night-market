#!/usr/bin/env python3
"""Area-agent registry for auto-role assignment.

Maps codebase directories to specialist agent configurations.
When work targets a specific area, the matching config is
loaded to provide deep context without manual prompt engineering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

# Pattern to extract YAML frontmatter
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_yaml_list(text: str) -> list[str]:
    """Parse a simple YAML list (lines starting with '- ')."""
    return [
        line.strip().lstrip("- ").strip().strip('"').strip("'")
        for line in text.splitlines()
        if line.strip().startswith("- ")
    ]


def _parse_frontmatter(text: str) -> dict[str, str | list[str]]:
    """Extract key-value pairs from YAML-like frontmatter.

    Handles simple scalars and list values (lines starting with -).
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    result: dict[str, str | list[str]] = {}
    current_key = ""
    list_buffer: list[str] = []

    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            list_buffer.append(stripped.lstrip("- ").strip().strip('"').strip("'"))
        elif ":" in stripped:
            # Save previous list if any
            if current_key and list_buffer:
                result[current_key] = list_buffer
                list_buffer = []
            key, _, value = stripped.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value:
                result[current_key] = value
        else:
            continue

    # Save trailing list
    if current_key and list_buffer:
        result[current_key] = list_buffer

    return result


@dataclass(frozen=True)
class AreaAgentConfig:
    """Configuration for a codebase area specialist agent."""

    area_name: str
    ownership_globs: tuple[str, ...] = ()
    tags: list[str] = field(default_factory=list)
    body: str = ""

    def matches_path(self, file_path: str) -> bool:
        """Check if a file path matches any ownership glob."""
        return any(fnmatch(file_path, glob) for glob in self.ownership_globs)


def load_area_config(config_path: Path) -> AreaAgentConfig:
    """Load an area-agent configuration from a Markdown file.

    Args:
        config_path: Path to the .md config file.

    Returns:
        Parsed AreaAgentConfig.

    """
    text = config_path.read_text()
    meta = _parse_frontmatter(text)

    # Extract body (everything after frontmatter)
    fm_match = FRONTMATTER_RE.match(text)
    body = text[fm_match.end() :].strip() if fm_match else text.strip()

    globs = meta.get("ownership_globs", [])
    if isinstance(globs, str):
        globs = [globs]

    tags_raw = meta.get("tags", [])
    if isinstance(tags_raw, str):
        tags_raw = [tags_raw]

    return AreaAgentConfig(
        area_name=str(meta.get("area_name", config_path.stem)),
        ownership_globs=tuple(globs),
        tags=list(tags_raw),
        body=body,
    )


def find_area_config(
    file_path: str,
    configs_dir: Path,
) -> AreaAgentConfig | None:
    """Find the area-agent config matching a file path.

    Scans all .md files in configs_dir and returns the first
    config whose ownership globs match the given file path.

    Args:
        file_path: The file path to match.
        configs_dir: Directory containing area-agent .md configs.

    Returns:
        Matching AreaAgentConfig, or None if no match.

    """
    if not configs_dir.is_dir():
        return None

    for config_file in sorted(configs_dir.glob("*.md")):
        config = load_area_config(config_file)
        if config.matches_path(file_path):
            return config

    return None
