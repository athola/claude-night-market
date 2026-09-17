"""A plugin installed from the marketplace has no ``.claude/rules/``.

Every plugin here ships on its own. A reader who installs `abstract`
gets `plugins/abstract/` and nothing else: no repository root, no
`CLAUDE.md`, and no `.claude/rules/`. Prose inside a shipped skill,
command, agent, or shared module that says "see
`.claude/rules/bounded-autonomy.md`" therefore points that reader at a
path which does not exist on their machine, and gives them no signal
that the lookup failed rather than the instruction being wrong.

Review on PR #662 found this in four files. The sweep found 15. They
all arrived the same way: the rule is real and load-bearing *here*, so
citing it read as diligence rather than as a dangling reference.

The fix direction matters and is not "delete the citation". The
substance has to travel with the plugin. State the principle inline,
or point at a module inside the same plugin. This gate only checks
that the repo-local path is gone; it cannot check that the content
survived, which is the reviewer's job.

Scope is the shipped surface only. `docs/`, `tests/`, and Python
source are excluded: those are read in a checkout, not by a
marketplace install.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The directories a marketplace install actually delivers to a reader.
SHIPPED_SUBTREES = ("skills", "commands", "agents", "shared-modules")

RULES_PATH = re.compile(r"\.claude/rules/")

# Files whose subject *is* the rules directory. For these the string is
# an operand -- a directory to evaluate, or a diff path to test for --
# not a pointer the reader is expected to follow.
OPERAND_ALLOWLIST = {
    "plugins/abstract/commands/rules-eval.md",
    "plugins/abstract/skills/rules-eval/SKILL.md",
    "plugins/abstract/skills/rules-eval/modules/organization-patterns.md",
    "plugins/abstract/skills/hooks-eval/SKILL.md",
    "plugins/abstract/skills/plugin-review/modules/tier-pr.md",
}

# hookify ships the rule bodies themselves as a catalog, so its copies
# are the content rather than a reference to absent content.
ALLOWED_PREFIXES = ("plugins/hookify/skills/rule-catalog/",)


def _shipped_markdown() -> list[Path]:
    found: list[Path] = []
    for plugin in sorted((REPO_ROOT / "plugins").iterdir()):
        if not plugin.is_dir():
            continue
        for subtree in SHIPPED_SUBTREES:
            found.extend(sorted((plugin / subtree).rglob("*.md")))
    return found


def _citations(markdown: Path) -> list[str]:
    """Every line in ``markdown`` naming the repo-local rules directory."""
    return [
        f"  line {number}: {line.strip()}"
        for number, line in enumerate(markdown.read_text().splitlines(), start=1)
        if RULES_PATH.search(line)
    ]


@pytest.mark.parametrize(
    "markdown",
    _shipped_markdown(),
    ids=lambda path: str(path.relative_to(REPO_ROOT)),
)
def test_shipped_markdown_cites_no_repo_local_rule_path(markdown: Path) -> None:
    """A shipped document may not send its reader to `.claude/rules/`.

    An exemption applies only to a file that actually carries the path.
    Skipping every exempt file, which is what this gate did first,
    reported nothing for 21 of them, and 14 of those carried no citation
    at all: they were clean, and the gate said so by staying silent.

    The branch order below runs the ordinary assertion on those 14
    instead. Be precise about what that buys: under the prefix the
    assertion cannot go red, because a file that does cite the path
    takes the exempt branch. The pass is by policy, not by evidence.
    What guards the subtree is
    ``test_the_catalog_prefix_exemption_still_has_something_to_exempt``,
    and what guards the five named files is the staleness assertion
    here.
    """
    relative = str(markdown.relative_to(REPO_ROOT))
    offending = _citations(markdown)

    if relative in OPERAND_ALLOWLIST:
        # The rules directory is this file's operand, not a pointer the
        # reader follows. An entry that no longer cites it is stale.
        assert offending, (
            f"{relative} is listed in OPERAND_ALLOWLIST but no longer cites "
            "`.claude/rules/`. Drop the entry so the list keeps meaning "
            "what it says."
        )
        return

    if relative.startswith(ALLOWED_PREFIXES) and offending:
        # hookify ships the rule bodies themselves, so a copy carrying
        # the path is the content rather than a reference to absent
        # content.
        return

    assert not offending, (
        f"{relative} points a marketplace reader at `.claude/rules/`, which "
        "no install of this plugin contains. Move the substance into the "
        "plugin (inline it, or cite a module under the same plugin):\n"
        + "\n".join(offending)
    )


def test_the_catalog_prefix_exemption_still_has_something_to_exempt() -> None:
    """``ALLOWED_PREFIXES`` covers a subtree, so staleness is subtree-wide.

    The per-file branch above cannot notice that the whole prefix has
    stopped earning its keep, because every file under a dead prefix
    passes the ordinary assertion. This is the guard for that: if no
    file under the prefix cites the path any more, the prefix is
    carrying nothing and should go.
    """
    covered = [
        path
        for path in _shipped_markdown()
        if str(path.relative_to(REPO_ROOT)).startswith(ALLOWED_PREFIXES)
        and _citations(path)
    ]

    assert covered, (
        "no file under "
        + ", ".join(ALLOWED_PREFIXES)
        + " cites `.claude/rules/` any more, so the prefix exemption "
        "exempts nothing. Remove it."
    )
