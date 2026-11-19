"""The book's "All Hooks" table names every registered hook and its events.

Nothing compared the table with hooks.json, so it carried wrong events and
omitted eleven hooks while every other capabilities table stayed in sync
(BOOK-1).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "book" / "src" / "reference" / "capabilities-reference.md"
SCRIPT = re.compile(r"hooks/([\w.-]+\.(?:py|sh))")


def _registered() -> dict[str, tuple[set[str], set[str]]]:
    """Map each hook script name to (plugins, events) from every hooks.json."""
    found: dict[str, tuple[set[str], set[str]]] = defaultdict(lambda: (set(), set()))
    for manifest in sorted(ROOT.glob("plugins/*/hooks/hooks.json")):
        plugin = manifest.parent.parent.name
        for event, groups in json.loads(manifest.read_text())["hooks"].items():
            for group in groups:
                for hook in group.get("hooks", []):
                    for name in SCRIPT.findall(hook.get("command", "")):
                        found[name][0].add(plugin)
                        found[name][1].add(event)
    return dict(found)


def _documented() -> dict[str, tuple[set[str], set[str]]]:
    text = TABLE.read_text()
    section = text.split("### All Hooks (Alphabetical)", 1)[1].split("\n#", 1)[0]
    rows: dict[str, tuple[set[str], set[str]]] = defaultdict(lambda: (set(), set()))
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].startswith("`"):
            continue
        name = cells[0].strip("`")
        rows[name][0].update(p.strip() for p in cells[1].split(","))
        rows[name][1].update(e.strip() for e in cells[2].split(","))
    return dict(rows)


def test_hook_table_matches_registered_hooks() -> None:
    registered, documented = _registered(), _documented()
    assert sorted(set(registered) - set(documented)) == [], "registered, not in table"
    assert sorted(set(documented) - set(registered)) == [], "in table, not registered"
    wrong = {
        name: (documented[name], registered[name])
        for name in registered
        if documented[name] != registered[name]
    }
    assert wrong == {}
