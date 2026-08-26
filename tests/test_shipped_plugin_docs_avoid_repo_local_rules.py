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


def _is_exempt(relative: str) -> bool:
    if relative in OPERAND_ALLOWLIST:
        return True
    return relative.startswith(ALLOWED_PREFIXES)


@pytest.mark.parametrize(
    "markdown",
    _shipped_markdown(),
    ids=lambda path: str(path.relative_to(REPO_ROOT)),
)
def test_shipped_markdown_cites_no_repo_local_rule_path(markdown: Path) -> None:
    """A shipped document may not send its reader to `.claude/rules/`."""
    relative = str(markdown.relative_to(REPO_ROOT))
    if _is_exempt(relative):
        pytest.skip(f"{relative} operates on the rules directory")

    offending = [
        f"  line {number}: {line.strip()}"
        for number, line in enumerate(markdown.read_text().splitlines(), start=1)
        if RULES_PATH.search(line)
    ]

    assert not offending, (
        f"{relative} points a marketplace reader at `.claude/rules/`, which "
        "no install of this plugin contains. Move the substance into the "
        "plugin (inline it, or cite a module under the same plugin):\n"
        + "\n".join(offending)
    )
