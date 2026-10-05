"""Ratchet: every tracked executable shell script defines main().

The house shell rules (``~/.claude/rules/shell-scripts.md``) require an
executable script to keep its logic in functions and end with
``main "$@"``. The restyle stopped partway, so the scripts that predate
it are listed below. The list may only shrink: a new executable script
without ``main()`` fails, and so does an entry whose script has since
been fixed or removed, which forces the list to follow the fix.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Scripts that predate the rule. Remove an entry when its script is
# restyled; the stale-entry test below fails until you do.
ALLOWLIST = frozenset(
    {
        ".claude/skills/night-market-diagnostics-toolkit/scripts/health-snapshot.sh",
        "assets/tapes/add-subtitles.sh",
        "plugins/conjure/bin/status.sh",
        "plugins/conserve/tests/test_runtime_loading.sh",
        "plugins/egregore/scripts/install_launchd.sh",
        "plugins/egregore/scripts/install_systemd.sh",
        "plugins/egregore/scripts/watchdog.sh",
        "plugins/leyline/hooks/auto-star-repo.sh",
        "plugins/memory-palace/scripts/precommit_palace_maintenance.sh",
        "plugins/phantom/scripts/entrypoint.sh",
        "scripts/awesome-submit.sh",
        "scripts/capabilities-sync-check.sh",
        "scripts/check-all-quality.sh",
        "scripts/clawhub-batch-publish.sh",
        "scripts/clawhub-cron.sh",
        "scripts/clawhub-submit.sh",
        "scripts/shared/check-json-utils-drift.sh",
        "scripts/without-git-env.sh",
    }
)

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
