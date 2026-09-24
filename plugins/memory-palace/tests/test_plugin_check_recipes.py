"""The plugin-check chain must be able to fail.

``search`` ended in ``|| true`` because the sample bundle held no palaces,
so it exited 1 with "No palaces indexed" on every run. The suffix hid that,
and would equally hide a crash in ``search`` itself.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = PLUGIN_ROOT / "Makefile"


def _recipes() -> dict[str, list[str]]:
    """Map each target to its recipe lines, comments excluded."""
    recipes: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in MAKEFILE.read_text(encoding="utf-8").splitlines():
        rule = re.match(r"^([A-Za-z0-9_.-]+):(?!=)", line)
        if rule:
            current = recipes.setdefault(rule.group(1), [])
        elif line.startswith("\t") and current is not None:
            current.append(line.strip())
        elif line.startswith("#") or not line.strip():
            continue
        else:
            current = None
    return recipes


def _plugin_check_prerequisites() -> list[str]:
    match = re.search(
        r"^plugin-check:([^#\n]*)", MAKEFILE.read_text(encoding="utf-8"), re.M
    )
    assert match, "plugin-check target is gone; update this guard"
    return match.group(1).split()


def test_no_plugin_check_prerequisite_swallows_its_exit_status() -> None:
    recipes = _recipes()
    prerequisites = _plugin_check_prerequisites()
    assert "search" in prerequisites
    offenders = [
        f"{target}: {line}"
        for target in prerequisites
        for line in recipes.get(target, [])
        if line.endswith("|| true")
    ]
    assert not offenders, offenders


def test_sample_bundle_gives_search_a_palace_to_index() -> None:
    bundle = json.loads(
        (PLUGIN_ROOT / "examples" / "palaces-sample.json").read_text(encoding="utf-8")
    )
    assert bundle["palaces"], "search exits 1 on an empty store"
