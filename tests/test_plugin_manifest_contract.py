"""Marketplace and plugin manifests carry the fields Claude Code reads.

Field rules come from the plugin marketplace and manifest references
(`claude plugin validate` enforces the same ones). Each test pins one
fix, so reverting that fix turns its test red.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import yaml

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


def test_every_plugin_links_its_homepage_and_repository() -> None:
    """A homepage that does not parse as a URL stops the plugin loading."""
    manifests = sorted(REPO_ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    checked = 0
    for manifest in manifests:
        plugin = manifest.parents[1].name
        fields = json.loads(manifest.read_text(encoding="utf-8"))
        for key in ("homepage", "repository"):
            url = urlparse(fields.get(key, ""))
            assert url.scheme == "https" and url.netloc, f"{plugin}: bad {key}"
        assert fields["homepage"] == f"{REPOSITORY_URL}/tree/master/plugins/{plugin}"
        assert fields["repository"] == REPOSITORY_URL
        checked += 1
    assert checked == len(manifests)


# Commands whose only job is an external side effect (closing issues,
# relabelling a repository, reinstalling plugins). Each runs only when a
# person types it. acp, resolve-threads and create-tag are not listed:
# fixit, fix-pr and the release runbook invoke them on the model's turn.
USER_ONLY_COMMANDS = (
    "plugins/minister/commands/close-issue.md",
    "plugins/minister/commands/update-labels.md",
    "plugins/leyline/commands/reinstall-all-plugins.md",
    "plugins/leyline/commands/update-all-plugins.md",
)


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    _, block, _ = text.split("---\n", 2)
    return yaml.safe_load(block)


def test_side_effect_commands_run_only_when_a_person_types_them() -> None:
    for command in USER_ONLY_COMMANDS:
        frontmatter = _frontmatter(REPO_ROOT / command)
        assert frontmatter.get("disable-model-invocation") is True, command


def test_no_command_uses_the_underscore_spelling_of_user_invocable() -> None:
    """The field is `user-invocable`; `user_invocable` is ignored silently.

    Frontmatter is parsed, so `"user_invocable" :` and a quoted key are
    caught as well as the plain spelling. The parse is safe for every
    command: `test_every_skill_and_command_frontmatter_loads.py` in the
    abstract plugin asserts all of it is valid YAML.
    """
    offenders = [
        command.relative_to(REPO_ROOT)
        for command in sorted(REPO_ROOT.glob("plugins/*/commands/*.md"))
        if "user_invocable" in (_frontmatter(command) or {})
    ]
    assert not offenders, f"inert user_invocable key in {offenders}"


def test_frontmatter_parse_sees_a_quoted_or_spaced_underscore_key(
    tmp_path: Path,
) -> None:
    """The scan above must not depend on the key's exact spelling."""
    command = tmp_path / "cmd.md"
    command.write_text('---\n"user_invocable" : true\n---\nBody\n', encoding="utf-8")

    assert "user_invocable" in _frontmatter(command)
