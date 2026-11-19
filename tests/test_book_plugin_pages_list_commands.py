"""Every plugin command is named on that plugin's book page (BOOK-3)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "book" / "src" / "plugins"
COMMAND_DIRS = sorted(
    d
    for d in ROOT.glob("plugins/*/commands")
    if (PAGES / f"{d.parent.name}.md").exists()
)


@pytest.mark.parametrize("command_dir", COMMAND_DIRS, ids=lambda d: d.parent.name)
def test_plugin_page_names_every_command(command_dir: Path) -> None:
    page = (PAGES / f"{command_dir.parent.name}.md").read_text(encoding="utf-8")
    missing = sorted(c.stem for c in command_dir.glob("*.md") if c.stem not in page)
    assert not missing, missing


def _frontmatter_description(command: Path) -> tuple[str, str] | None:
    """The description's first physical line and its parsed text.

    A row filled from the first line after ``description:`` kept a folded
    scalar's ``>-`` or the first half of a wrapped sentence.
    """
    text = command.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    frontmatter = text.split("---", 2)[1]
    match = re.search(r"^description:[ \t]*(.*)$", frontmatter, re.MULTILINE)
    if match is None:
        return None
    parsed = (yaml.safe_load(frontmatter) or {}).get("description", "")
    return match.group(1).strip(), " ".join(str(parsed).split())


@pytest.mark.parametrize("command_dir", COMMAND_DIRS, ids=lambda d: d.parent.name)
def test_command_rows_carry_the_parsed_description(command_dir: Path) -> None:
    plugin = command_dir.parent.name
    page = (PAGES / f"{plugin}.md").read_text(encoding="utf-8")
    broken = []
    for command in sorted(command_dir.glob("*.md")):
        description = _frontmatter_description(command)
        if description is None:
            continue
        first_line, parsed = description
        if first_line == parsed:
            continue
        row = re.compile(
            rf"^\|\s*`/(?:{re.escape(plugin)}:)?{re.escape(command.stem)}`"
            rf"[^\n]*\|\s*{re.escape(first_line)}\s*\|\s*$",
            re.MULTILINE,
        )
        if row.search(page):
            broken.append(f"/{command.stem}: {first_line!r}")
    assert not broken, broken


def test_the_book_does_not_document_the_unread_pr_alias() -> None:
    """``aliases: [pr]`` was a frontmatter key nothing reads, so ``/pr``
    never resolved, and the book taught it as the way to prepare a PR.
    """
    alias = re.compile(r"(?<![\w/.:-])/pr(?![\w/-])")
    pages = sorted((ROOT / "book" / "src").rglob("*.md"))
    hits = [
        f"{page.relative_to(ROOT)}:{lineno}"
        for page in pages
        for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1)
        if alias.search(line)
    ]
    assert not hits, hits


def test_plugin_commands_do_not_teach_the_unread_pr_alias() -> None:
    """A command doc that shows ``/pr`` teaches a command that never resolves.

    ``prepare-pr.md`` names the alias only to say it does not resolve.
    """
    alias = re.compile(r"(?<![\w/.:-])/pr(?![\w/-])")
    pages = [
        page
        for page in sorted((ROOT / "plugins").glob("*/commands/**/*.md"))
        if page.name != "prepare-pr.md"
    ]
    hits = [
        f"{page.relative_to(ROOT)}:{lineno}"
        for page in pages
        for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1)
        if alias.search(line)
    ]
    assert not hits, hits
