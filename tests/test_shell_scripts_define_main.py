"""Ratchet: every tracked executable shell script defines main().

The house shell rules (``~/.claude/rules/shell-scripts.md``) require an
executable script to keep its logic in functions and end with
``main "$@"``. Every tracked executable script does so. A new one
without ``main()`` fails, and an allowlist entry whose script has been
fixed or removed fails too, which keeps the list honest.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Empty since the 2026-10-05 restyle brought every script under the rule.
# A script that cannot follow it gets an entry here with the reason.
ALLOWLIST: frozenset[str] = frozenset()

MAIN_DEFINITION = re.compile(r"^main\(\)\s*\{", re.MULTILINE)


def _tracked_executable_scripts() -> list[str]:
    """Paths git records with mode 100755, which is what ships executable."""
    listing = subprocess.run(
        ["git", "ls-files", "-s", "--", "*.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(
        line.split("\t", 1)[1]
        for line in listing.splitlines()
        if line.startswith("100755 ")
    )


def _defines_main(path: str) -> bool:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    return bool(MAIN_DEFINITION.search(text)) and text.rstrip().endswith('main "$@"')


def _violators() -> set[str]:
    return {p for p in _tracked_executable_scripts() if not _defines_main(p)}


def test_there_are_executable_shell_scripts() -> None:
    assert len(_tracked_executable_scripts()) > 10


def test_no_new_executable_shell_script_skips_main() -> None:
    new = sorted(_violators() - ALLOWLIST)
    assert not new, (
        f'executable shell scripts must define main() and end with `main "$@"`: {new}'
    )


def test_shell_main_allowlist_only_names_current_violators() -> None:
    """The allowlist can only shrink, so a fixed script must leave it."""
    stale = sorted(ALLOWLIST - _violators())
    assert not stale, (
        f"these scripts now define main() or are gone; remove them from "
        f"ALLOWLIST: {stale}"
    )
