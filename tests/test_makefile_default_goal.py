"""Guard that a bare `make` never mutates the working tree.

`plugins/abstract/config/make/python.mk` declares `format:` as its
first rule, and every plugin includes it above its own `help:`. With no
explicit `.DEFAULT_GOAL`, Make takes the first rule it saw, so `make` in
19 of 23 plugins ran `ruff format` and `ruff check --fix` over the
source. The root `Makefile`'s `make <plugin>` delegation invoked exactly
that. A contributor inspecting an unfamiliar plugin rewrote it.

`Skill(pensive:makefile-review)` module `best-practices.md` already
prescribes `.DEFAULT_GOAL := help`. This is the contract that keeps it
true.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"
COMMON_MK = PLUGINS_DIR / "abstract" / "config" / "make" / "common.mk"


def _plugin_makefiles() -> list[Path]:
    return sorted(PLUGINS_DIR.glob("*/Makefile"))


@pytest.mark.unit
def test_the_shared_include_pins_the_default_goal() -> None:
    """Scenario: the include every plugin loads sets a read-only default."""
    text = COMMON_MK.read_text(encoding="utf-8")
    assert re.search(r"^\.DEFAULT_GOAL\s*:=\s*help\s*$", text, re.MULTILINE), (
        "common.mk must set .DEFAULT_GOAL, or Make falls through to "
        "python.mk's first rule, which is the mutating `format` target"
    )


@pytest.mark.unit
@pytest.mark.parametrize("makefile", _plugin_makefiles(), ids=lambda p: p.parent.name)
def test_every_plugin_defines_the_default_goal_target(makefile: Path) -> None:
    """Guard: the pinned goal exists in each plugin that inherits it.

    Pinning `.DEFAULT_GOAL := help` in a shared include turns a missing
    `help:` from a working (if destructive) default into a hard error,
    so the target has to be there.
    """
    text = makefile.read_text(encoding="utf-8")
    assert re.search(r"^help:", text, re.MULTILINE), (
        f"{makefile.parent.name} inherits .DEFAULT_GOAL := help from "
        "common.mk but defines no help target"
    )


@pytest.mark.integration
@pytest.mark.parametrize("makefile", _plugin_makefiles(), ids=lambda p: p.parent.name)
def test_a_bare_make_runs_no_mutating_recipe(makefile: Path) -> None:
    """Scenario: `make` with no target rewrites nothing.

    GIVEN the file-content test above proves the assignment is present
    WHEN Make resolves includes, overrides and `.DEFAULT_GOAL` itself
    THEN only Make can say what a bare invocation actually runs, so
    this asks it. `--dry-run` prints the recipe without running it.

    A plugin that reintroduces a mutating first rule, or overrides
    `.DEFAULT_GOAL` locally, fails here and not in the reader's
    working tree.
    """
    completed = subprocess.run(
        ["make", "--dry-run"],
        cwd=makefile.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    mutating = ("Formatting code", "ruff format", "check --fix")
    offending = [
        line
        for line in completed.stdout.splitlines()
        if any(marker in line for marker in mutating)
    ]
    assert not offending, (
        f"a bare `make` in {makefile.parent.name} would run: {offending[:3]}"
    )
