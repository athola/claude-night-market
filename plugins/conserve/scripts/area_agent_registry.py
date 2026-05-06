#!/usr/bin/env python3
"""Area-agent registry for auto-role assignment.

Maps codebase directories to specialist agent configurations.
When work targets a specific area, the matching config is
loaded to provide deep context without manual prompt engineering.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

# D-02: pull canonical frontmatter parser from leyline.
_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
if str(_LEYLINE_SRC) not in sys.path:
    sys.path.insert(0, str(_LEYLINE_SRC))

from leyline.frontmatter import (  # noqa: E402 - import after sys.path setup
    parse_frontmatter_with_body,
)


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
    meta, body = parse_frontmatter_with_body(text)
    body = body.strip() if meta else text.strip()

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
