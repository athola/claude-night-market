#!/usr/bin/env python3
"""Cross-check the skills plugin.json registers against the ones on disk.

Both directions are checked, and both come from plugin.json and the
directory rather than a hardcoded list, so a newly added skill is
covered without editing this script. A registered skill with no
SKILL.md does not load. A skill on disk that plugin.json omits is
invisible to the harness however complete it is, which is the likelier
mistake when a plugin gains a provider.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


#: Every manifest that claims to list this plugin's skills. Checking one
#: was not enough: `plugin.json` and `metadata.json` are maintained by
#: hand and drift apart, and a skill present in one and absent from the
#: other is registered as far as half the tooling is concerned.
MANIFESTS = ("plugin.json", "metadata.json")


def _registered(manifest: str) -> set[str]:
    """Skill directory names one manifest lists."""
    path = PLUGIN_ROOT / ".claude-plugin" / manifest
    return {Path(entry).name for entry in json.loads(path.read_text())["skills"]}


def main() -> int:
    """Print per-skill status and exit 1 when the manifests and disk disagree."""
    registrations = {name: _registered(name) for name in MANIFESTS}
    on_disk = {p.parent.name for p in PLUGIN_ROOT.glob("skills/*/SKILL.md")}
    every = set(on_disk).union(*registrations.values())

    failed = False
    for name in sorted(every):
        absent_from = [m for m, names in registrations.items() if name not in names]
        if name not in on_disk:
            status, failed = "[X] registered, no SKILL.md", True
        elif absent_from:
            status, failed = f"[X] on disk, absent from {', '.join(absent_from)}", True
        else:
            status = "[OK]"
        print(f"  {name:<20} {status}")

    if failed:
        print("\nSkill coverage failed: registration and disk disagree.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
