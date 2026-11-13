"""Readers shared by the SKILL.md contract tests in this directory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def read_or_fail(path: Path) -> str:
    """Fail the test, rather than error, when a pinned file is missing."""
    if not path.exists():
        pytest.fail(f"missing: {path}")
    return path.read_text(encoding="utf-8")


def read_frontmatter(content: str) -> str:
    """Return the YAML frontmatter block between the leading ``---`` markers."""
    if not content.startswith("---\n"):
        pytest.fail("SKILL.md must begin with `---` YAML frontmatter")
    end = content.find("\n---\n", 4)
    if end == -1:
        pytest.fail("SKILL.md frontmatter has no closing `---`")
    return content[4:end]
