"""Every in-repo markdown anchor points at a heading that exists.

Three dead anchors were found by hand in one session:
``docs/testing-guide.md`` cited ``quality-gates.md#cicd-integration`` for a
section that never existed, ``docs/guides/data-extraction-pattern.md`` cited
``#progressive-disclosure`` where the heading is numbered
``### 1. Progressive Disclosure``, and one SKILL.md carried a table-of-contents
entry for a step that had been renumbered.

A path test cannot catch these: the file resolves and only the fragment is
wrong, so the link renders and silently lands at the top of the page.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Vendored trees, build output, and the linked worktrees under .claude are
# copies of other checkouts; their drift is not this repository's contract.
SKIP_PARTS = {
    ".git",
    ".venv",
    ".uv-tools",
    ".mypy_cache",
    "node_modules",
    "worktrees",
    "superpowers",
}

_HEADING = re.compile(r"#{1,6}\s+(.*)")
# Markdown links with a fragment, excluding absolute URLs.
_LINK = re.compile(r"\]\((?!https?:)([^)#]*)#([a-zA-Z0-9][a-zA-Z0-9._-]*)\)")


def _slug(heading: str) -> str:
    text = re.sub(r"[`*_\[\]()]", "", heading.strip().lower())
    text = re.sub(r"[^a-z0-9 -]", "", text)
    return re.sub(r"\s+", "-", text).strip("-")


def _anchors(text: str) -> set[str]:
    return {_slug(m.group(1)) for m in map(_HEADING.match, text.splitlines()) if m}


def _markdown_files() -> list[Path]:
    return sorted(
        p
        for p in REPO_ROOT.rglob("*.md")
        if not SKIP_PARTS & set(p.relative_to(REPO_ROOT).parts)
    )


@pytest.mark.parametrize(
    "markdown", _markdown_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_every_fragment_link_names_a_real_heading(markdown: Path) -> None:
    text = markdown.read_text(encoding="utf-8")
    broken: list[str] = []
    for relative, fragment in _LINK.findall(text):
        target = markdown if relative == "" else markdown.parent / relative
        # A missing or non-markdown target is test_cited_paths_resolve's job.
        if not target.is_file() or target.suffix != ".md":
            continue
        available = _anchors(target.read_text(encoding="utf-8"))
        if fragment.lower() not in available:
            broken.append(f"{relative or markdown.name}#{fragment}")
    assert not broken, (
        f"{markdown.relative_to(REPO_ROOT)} links to headings that do not "
        f"exist: {broken}. The link still renders and lands at the top of "
        "the page, so nothing else reports this."
    )


def test_the_scan_actually_reaches_some_links() -> None:
    """Guard the guard: an over-broad skip list would make every case vacuous."""
    total = sum(
        len(_LINK.findall(p.read_text(encoding="utf-8"))) for p in _markdown_files()
    )
    assert total > 50, (
        f"only {total} fragment links found; the skip list or the link regex "
        "has stopped matching real content"
    )
