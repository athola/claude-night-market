"""Skills a command tells the session to load must exist.

This file replaces ``test_wrapped_commands.py``, 402 lines and 20 tests
that imported no spec-kit code. Its assertions ran over list literals
declared inside the test bodies (``assert len(workflow_steps) == 5``
five lines after ``workflow_steps = [...]``), so deleting every command
in the plugin left it green. The ``.wrapped`` commands it named do not
exist on disk and never did.

The real behavior of the commands is covered by ``test_commands.py``,
and their frontmatter by ``test_frontmatter.py``. The one thing neither
checks is the skill references inside a command body, which is what a
command actually asks the session to do, so that is what is checked
here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = PLUGIN_ROOT / "commands"
PLUGINS_ROOT = PLUGIN_ROOT.parent

# A backticked skill reference: bare (same plugin) or plugin-qualified.
SKILL_REF = re.compile(r"`([a-z][a-z0-9-]*(?::[a-z0-9-]+)?)`")

# Backticked tokens in these command bodies that are field names, values or
# placeholders rather than skills. Listed explicitly so a genuinely missing
# skill cannot hide behind a loose pattern.
NON_SKILL_TOKENS = frozenset(
    {
        "action",
        "execute",
        "parallelizable",
        "phase",
        "plan",
        "user-can-upload-file",
    }
)


def _command_files() -> list[Path]:
    return sorted(COMMANDS.glob("*.md"))


def _skill_exists(reference: str) -> bool:
    """Whether a reference resolves, for references this repo can answer.

    A qualified reference to a plugin this repository does not ship, such
    as ``superpowers:writing-plans``, names an external marketplace plugin.
    Whether it is installed is the user's environment, not this repo's
    contract, so it is treated as resolved. A reference into a plugin that
    *is* here must resolve, which is what catches a rename or a typo.
    """
    if ":" in reference:
        plugin, name = reference.split(":", 1)
        plugin_dir = PLUGINS_ROOT / plugin
        if not plugin_dir.is_dir():
            return True
        return (plugin_dir / "skills" / name).is_dir()
    return (PLUGIN_ROOT / "skills" / reference).is_dir()


def test_command_discovery_is_not_empty() -> None:
    """An empty parametrize list would make the guard below vacuous."""
    assert len(_command_files()) > 5


@pytest.mark.parametrize("command", _command_files(), ids=lambda p: p.stem)
def test_every_skill_a_command_names_resolves(command: Path) -> None:
    """A command that loads a skill must name one that is installed."""
    body = command.read_text(encoding="utf-8")
    references = {
        ref
        for ref in SKILL_REF.findall(body)
        if ref not in NON_SKILL_TOKENS and not ref.startswith(("phase:", "risk:"))
    }
    missing = sorted(ref for ref in references if not _skill_exists(ref))
    assert not missing, (
        f"{command.name} tells the session to load {missing}, which is not "
        f"installed. The command still runs and the instruction silently "
        f"does nothing."
    )
