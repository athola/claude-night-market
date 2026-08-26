"""The README's badges are claims, and claims drift.

The skills badge read 209 while 211 shipped, and the "What's New"
section said four plugins carry a `workflows/` script on a branch where
all 23 do. Both were true when written. Neither had anything watching
it, which is the same defect this repository has been closing all
cycle: a documented number with no gate is a number that is right once.

Exemplar practice for plugin-collection READMEs is to generate the
index section from the manifest. That is the better fix and a larger
one. This gate is the cheaper half: it does not write the numbers, it
refuses to let them be wrong.

Scope is deliberately narrow. Only counts that are mechanically
derivable from the tree are checked, because a gate that needs
judgment to satisfy gets edited to pass rather than obeyed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def _actual_plugins() -> int:
    return len(list((REPO_ROOT / "plugins").glob("*/.claude-plugin/plugin.json")))


def _actual_skills() -> int:
    return len(list((REPO_ROOT / "plugins").glob("*/skills/*/SKILL.md")))


def _badge_value(label: str) -> int:
    """Return the number in a shields.io badge, e.g. `plugins-23-orange`."""
    match = re.search(rf"badge/{label}-(\d+)-", _readme())
    assert match is not None, f"README has no {label} badge to check"
    return int(match.group(1))


def test_plugin_badge_matches_the_plugin_directories() -> None:
    """GIVEN the plugins the repository ships.

    WHEN a reader trusts the README badge
    THEN the badge names the number that ships
    """
    assert _badge_value("plugins") == _actual_plugins()


def test_skill_badge_matches_the_shipped_skill_files() -> None:
    """GIVEN every SKILL.md under a plugin.

    WHEN a reader trusts the README badge
    THEN the badge names the number that ships

    This is the one that drifted: 209 against 211 on disk.
    """
    assert _badge_value("skills") == _actual_skills()


def test_the_plugin_count_in_prose_matches_the_badge() -> None:
    """GIVEN the "What's Inside" section stating a plugin count.

    WHEN it disagrees with the badge above it
    THEN one of the two is wrong and the reader cannot tell which
    """
    prose = re.search(r"(\d+) plugins in four layers", _readme())

    assert prose is not None, "README no longer states a plugin count in prose"
    assert int(prose.group(1)) == _actual_plugins()


@pytest.mark.parametrize("layer", ["Foundation", "Utility", "Domain", "Meta"])
def test_every_layer_named_in_whats_inside_still_has_members(layer: str) -> None:
    """GIVEN the four-layer description of the plugin set.

    WHEN a layer is named
    THEN at least one backticked plugin under it exists on disk

    A layer whose plugins were all renamed would otherwise read as
    current while describing nothing.
    """
    section = re.search(
        rf"\*\*{layer}\*\*(.+?)(?=\n\n\*\*|\n\n<picture)", _readme(), re.DOTALL
    )
    assert section is not None, f"README no longer describes the {layer} layer"

    named = re.findall(r"`([a-z-]+)`", section.group(1))
    existing = [n for n in named if (REPO_ROOT / "plugins" / n).is_dir()]

    assert existing, f"{layer} names no plugin that exists: {named}"
