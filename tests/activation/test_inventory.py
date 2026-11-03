"""FR-1: the inventory is the denominator of every activation rate.

If it miscounts, every rate is wrong, and if its hash ignores a
description edit, a comparison cannot see which items changed.
"""

from __future__ import annotations

from scripts.activation.inventory import (
    build_inventory,
    library_hash,
    missing_from_listing,
)

from .conftest import write


def test_inventory_lists_each_routed_kind_and_skips_disabled(plugin_tree):
    items = build_inventory(plugin_tree)
    assert [(i.id, i.kind) for i in items] == [
        ("alpha:shell-check", "skill"),
        ("alpha:ship", "command"),
        ("beta:sweep", "workflow"),
    ]


def test_folded_yaml_description_is_whitespace_normalized(plugin_tree):
    skill = next(i for i in build_inventory(plugin_tree) if i.kind == "skill")
    assert skill.description == "Audit shell scripts for quoting bugs."


def test_workflow_text_joins_description_and_when_to_use(plugin_tree):
    flow = next(i for i in build_inventory(plugin_tree) if i.kind == "workflow")
    assert flow.description == (
        "Sweep every area in parallel - Run before a release. It's read-only."
    )


def test_description_edit_changes_library_hash(plugin_tree):
    before = library_hash(build_inventory(plugin_tree))
    write(
        plugin_tree / "plugins/alpha/commands/ship.md",
        "---\ndescription: Commit, push, and open a PR.\n---\n\n# Ship\n",
    )
    assert library_hash(build_inventory(plugin_tree)) != before


def test_body_edit_leaves_library_hash_unchanged(plugin_tree):
    before = library_hash(build_inventory(plugin_tree))
    write(
        plugin_tree / "plugins/alpha/commands/ship.md",
        "---\ndescription: Commit and push the current branch.\n---\n\n# Other\n",
    )
    assert library_hash(build_inventory(plugin_tree)) == before


def test_missing_from_listing_names_items_the_init_event_lacks(plugin_tree):
    items = build_inventory(plugin_tree)
    init = {"skills": ["alpha:shell-check", "beta:sweep"], "slash_commands": []}
    assert missing_from_listing(items, init) == ["alpha:ship"]


def test_shared_id_is_one_routing_target_showing_the_command(plugin_tree):
    write(
        plugin_tree / "plugins/alpha/skills/ship/SKILL.md",
        "---\nname: ship\ndescription: Skill text the listing hides.\n---\n",
    )
    items = [i for i in build_inventory(plugin_tree) if i.id == "alpha:ship"]
    assert len(items) == 1
    assert items[0].kind == "command"
    assert items[0].description == "Commit and push the current branch."
    assert items[0].shadowed == ("plugins/alpha/skills/ship/SKILL.md",)


def test_workflow_outranks_command_for_a_shared_id(plugin_tree):
    write(
        plugin_tree / "plugins/beta/commands/sweep.md",
        "---\ndescription: Command text.\n---\n",
    )
    (item,) = [i for i in build_inventory(plugin_tree) if i.id == "beta:sweep"]
    assert item.kind == "workflow"
    assert item.shadowed == ("plugins/beta/commands/sweep.md",)


def test_disabled_file_does_not_shadow(plugin_tree):
    write(
        plugin_tree / "plugins/alpha/skills/hidden/SKILL.md",
        "---\nname: hidden\ndescription: Visible skill.\n---\n",
    )
    (item,) = [i for i in build_inventory(plugin_tree) if i.id == "alpha:hidden"]
    assert item.kind == "skill" and item.shadowed == ()
