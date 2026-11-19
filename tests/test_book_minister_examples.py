"""Every `python tracker.py ...` example in the minister book page parses.

The page documented list/show/report subcommands that do not exist, so
each copied example exited 2 with an argparse error (BOOK-2).
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "minister" / "src"))

from minister.project_tracker import build_cli_parser  # noqa: E402 - minister src goes on sys.path first

EXAMPLES = re.findall(
    r"^python tracker\.py (.+)$",
    (ROOT / "book" / "src" / "plugins" / "minister.md").read_text(),
    re.MULTILINE,
)


@pytest.mark.parametrize("args", EXAMPLES)
def test_book_tracker_examples_parse(args: str) -> None:
    build_cli_parser().parse_args(shlex.split(args))


def test_the_page_has_examples() -> None:
    assert EXAMPLES


def test_every_minister_command_is_listed() -> None:
    """close-issue, create-issue and update-labels were missing (BOOK-3)."""
    page = (ROOT / "book" / "src" / "plugins" / "minister.md").read_text()
    commands = sorted(
        p.stem for p in (ROOT / "plugins" / "minister" / "commands").glob("*.md")
    )
    missing = [name for name in commands if f"`/minister:{name}`" not in page]
    assert commands and not missing, missing
