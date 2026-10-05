"""Marketplace and plugin manifests carry the fields Claude Code reads.

Field rules come from the plugin marketplace and manifest references
(`claude plugin validate` enforces the same ones). Each test pins one
fix, so reverting that fix turns its test red.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def _marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def test_renamed_plugins_migrate_to_current_entries() -> None:
    """Users who installed `conservation` or `pensieve` follow the rename.

    Without the map, Claude Code reports the old name as not found in
    the marketplace instead of migrating the install.
    """
    marketplace = _marketplace()
    current = {entry["name"] for entry in marketplace["plugins"]}
    renames = marketplace["renames"]

    assert renames == {"conservation": "conserve", "pensieve": "pensive"}
    for old, new in renames.items():
        assert old not in current, f"{old} is still listed, so it is not renamed"
        assert new in current, f"rename target {new} is not a listed plugin"
