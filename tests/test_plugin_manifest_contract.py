"""Marketplace and plugin manifests carry the fields Claude Code reads.

Field rules come from the plugin marketplace and manifest references
(`claude plugin validate` enforces the same ones). Each test pins one
fix, so reverting that fix turns its test red.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

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


# Every top-level key marketplace-reference.md lists. Claude Code strips
# anything else at load time, so data kept outside this set is never read.
MARKETPLACE_TOP_LEVEL_FIELDS = frozenset(
    {
        "$schema",
        "name",
        "owner",
        "plugins",
        "description",
        "version",
        "metadata",
        "forceRemoveDeletedPlugins",
        "allowCrossMarketplaceDependenciesOn",
        "renames",
    }
)


def test_marketplace_top_level_holds_only_fields_claude_code_reads() -> None:
    unknown = set(_marketplace()) - MARKETPLACE_TOP_LEVEL_FIELDS
    assert not unknown, f"Claude Code strips these marketplace fields: {unknown}"


def test_optional_dependencies_live_under_metadata() -> None:
    """`optional_dependencies` is not a manifest field; `metadata` is free-form."""
    misplaced = [
        manifest.relative_to(REPO_ROOT)
        for manifest in sorted(REPO_ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
        if "optional_dependencies" in json.loads(manifest.read_text(encoding="utf-8"))
    ]
    assert not misplaced, f"top-level optional_dependencies in {misplaced}"


REPOSITORY_URL = "https://github.com/athola/claude-night-market"
# Their manifests are being edited on another branch; they gain the same
# links when that work lands, and this set must then be emptied.
LINKS_PENDING = frozenset({"conserve", "egregore"})


def test_every_plugin_links_its_homepage_and_repository() -> None:
    """A homepage that does not parse as a URL stops the plugin loading."""
    manifests = sorted(REPO_ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    checked = 0
    for manifest in manifests:
        plugin = manifest.parents[1].name
        if plugin in LINKS_PENDING:
            continue
        fields = json.loads(manifest.read_text(encoding="utf-8"))
        for key in ("homepage", "repository"):
            url = urlparse(fields.get(key, ""))
            assert url.scheme == "https" and url.netloc, f"{plugin}: bad {key}"
        assert fields["homepage"] == f"{REPOSITORY_URL}/tree/master/plugins/{plugin}"
        assert fields["repository"] == REPOSITORY_URL
        checked += 1
    assert checked == len(manifests) - len(LINKS_PENDING)
