"""Every plugin command is named on that plugin's book page (BOOK-3)."""

from __future__ import annotations

from pathlib import Path

import pytest

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
