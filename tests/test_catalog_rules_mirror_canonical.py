"""A hookify catalog rule must not drift from its canonical rule.

`.claude/rules/*.md` is where a rule is decided. Some of those rules are
also published through hookify's rule catalog, condensed, for use in other
repositories. The two copies are deliberately different lengths, so a
byte-comparison would be wrong. What must not differ is the machine
contract in the frontmatter: the rule name, the event it fires on, the
action it takes, and the regex that triggers it.

The drift this guards against already happened once. The catalog copy of
plan-before-large-dispatch fell behind the canonical rule, was re-synced
in f0790a1f, and that commit added a prose note saying the canonical copy
wins. A note is not an invariant, and a workflow review of that commit
pointed out that nothing would fail if it drifted again. This is the
missing half.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = REPO_ROOT / ".claude" / "rules"
CATALOG_DIR = REPO_ROOT / "plugins" / "hookify" / "skills" / "rule-catalog" / "rules"


def _frontmatter(path: Path) -> str:
    """Return the YAML frontmatter block, without its delimiters."""
    text = path.read_text()
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else ""


def _mirrored_pairs() -> list[tuple[Path, Path]]:
    """Every catalog rule that shares a filename with a canonical rule."""
    pairs = []
    for catalog in sorted(CATALOG_DIR.rglob("*.md")):
        canonical = CANONICAL_DIR / catalog.name
        if canonical.exists():
            pairs.append((canonical, catalog))
    return pairs


def test_at_least_one_rule_is_mirrored() -> None:
    """The pairing this suite guards has to exist for it to guard anything."""
    assert _mirrored_pairs(), "no catalog rule shares a name with a canonical rule"


@pytest.mark.parametrize(
    ("canonical", "catalog"),
    _mirrored_pairs(),
    ids=lambda p: p.parent.name + "/" + p.name,
)
def test_catalog_copy_keeps_the_canonical_machine_contract(
    canonical: Path, catalog: Path
) -> None:
    """The frontmatter is the contract, so it may not diverge.

    Prose may be condensed for the catalog. The trigger pattern, the event,
    and the action decide when the rule fires, and a copy that fires
    differently is a different rule wearing the same name.
    """
    assert _frontmatter(catalog) == _frontmatter(canonical), (
        f"{catalog.relative_to(REPO_ROOT)} frontmatter has drifted from "
        f"{canonical.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize(
    ("canonical", "catalog"),
    _mirrored_pairs(),
    ids=lambda p: p.parent.name + "/" + p.name,
)
def test_catalog_copy_names_its_canonical_source(
    canonical: Path, catalog: Path
) -> None:
    """A reader of the condensed copy must be able to find the full one."""
    assert canonical.name in catalog.read_text(), (
        f"{catalog.relative_to(REPO_ROOT)} does not name its canonical source"
    )
