#!/usr/bin/env python3
"""Cross-check the skills plugin.json registers against the ones on disk.

The block this replaces named four skills in a hardcoded list and tested
that each one's SKILL.md exists. It reported OK over a plugin that had
nine, so the four this PR added were never checked, and its `[X]` arm
could not fire in any case: the loop directly above it had just listed
the same files off the same directory.

The pair of directions here is what makes the check worth running. A
registered skill with no SKILL.md does not load. A skill on disk that
plugin.json omits is invisible to the harness however complete it is,
which is the likelier mistake when a plugin gains a provider.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    """Print per-skill status; exit 1 when the two sides disagree."""
    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    registered = {
        Path(entry).name for entry in json.loads(manifest.read_text())["skills"]
    }
    on_disk = {p.parent.name for p in PLUGIN_ROOT.glob("skills/*/SKILL.md")}

    failed = False
    for name in sorted(registered | on_disk):
        if name not in on_disk:
            status, failed = "[X] registered, no SKILL.md", True
        elif name not in registered:
            status, failed = "[X] on disk, not registered", True
        else:
            status = "[OK]"
        print(f"  {name:<20} {status}")

    if failed:
        print("\nSkill coverage failed: registration and disk disagree.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
