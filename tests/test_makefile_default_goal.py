"""Guard that a bare `make` never mutates the working tree.

`plugins/abstract/config/make/python.mk` declares `format:` as its
first rule, and every plugin includes it above its own `help:`. With no
explicit `.DEFAULT_GOAL`, Make takes the first rule it saw, so `make` in
19 of 23 plugins ran `ruff format` and `ruff check --fix` over the
source. The root `Makefile`'s `make <plugin>` delegation invoked exactly
that. A contributor inspecting an unfamiliar plugin rewrote it.

The root `Makefile` has the same defect from a different cause: its
per-plugin delegation rules are generated with `$(eval)` before `all:`
is declared, so the first rule Make saw was `abstract:` and a bare
`make` at the repository root ran `make -C plugins/abstract`.

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
ROOT_MAKEFILE = REPO_ROOT / "Makefile"
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


@pytest.mark.unit
def test_the_root_makefile_pins_the_default_goal() -> None:
    """Scenario: the root Makefile does not let rule order pick the goal.

    Its delegation rules are generated with `$(eval)` ahead of `all:`,
    so the first rule is whichever plugin sorts first. A comment naming
    `all` the default is not what Make reads.
    """
    text = ROOT_MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^\.DEFAULT_GOAL\s*:=\s*help\s*$", text, re.MULTILINE), (
        "the root Makefile must set .DEFAULT_GOAL, or a bare `make` "
        "resolves to the first generated delegation rule"
    )
    assert re.search(r"^help:", text, re.MULTILINE), (
        "the root Makefile pins .DEFAULT_GOAL := help but defines no help target"
    )


@pytest.mark.integration
def test_a_bare_make_at_the_root_delegates_to_no_plugin() -> None:
    """Scenario: `make` at the repository root prints its own help.

    Before the goal was pinned this printed `make -C plugins/abstract`
    and then that plugin's default goal, so inspecting the repository
    ran a plugin's recipes.
    """
    completed = subprocess.run(
        ["make", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = completed.stdout + completed.stderr
    # The help text itself mentions `make -C <plugin-dir>` as advice, so
    # only lines Make would execute count. Everything help prints is an
    # echo, and a delegation is a bare sub-make invocation.
    executed = [
        line
        for line in combined.splitlines()
        if not re.match(r"\s*(echo|printf|@?#)", line)
    ]
    delegating = [line for line in executed if "make -C" in line]
    assert not delegating, (
        "a bare `make` at the root delegates to a plugin instead of "
        f"printing help: {delegating}"
    )
    mutating = ("Formatting code", "ruff format", "check --fix")
    offending = [token for token in mutating if token in combined]
    assert not offending, f"a bare `make` at the root runs mutating recipes {offending}"
    assert "Claude Night Market - Make Targets" in combined, (
        f"a bare `make` at the root did not print the root help:\n{combined[:400]}"
    )
