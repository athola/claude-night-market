"""Guard that no recipe deletes a path the environment can redirect.

`plugins/memory-palace/Makefile` assigned `PALACES_DIR ?= $(PWD)/.demo-palaces`
and `demo-reset` ran `rm -rf $(PALACES_DIR)`. `?=` yields to an exported
variable of the same name, and the plugin's own CLI reads exactly that
variable to locate a user's real palace store
(`scripts/memory_palace_cli.py`, `src/memory_palace/palace_manager.py`).
A contributor with `PALACES_DIR` exported who ran `make plugin-check`
reached `demo-import`, whose prerequisite is `demo-reset`, and lost the
store. Nothing printed a warning, and `demo-reset` carries no `##`
comment so it never appeared in `make help`.

The invariant: a variable that names a deletion target must be assigned
so the environment cannot supply it. `:=` and `=` both take precedence
over the environment; `?=` does not.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

# `rm -rf $(VAR)` or `rm -rf ${VAR}`, with optional flags in any order.
_RM_VAR = re.compile(r"rm\s+-[a-zA-Z]*r[a-zA-Z]*\s+.*?[$][({](\w+)[)}]")


def _makefiles() -> list[Path]:
    """Every plugin Makefile, the shared includes, and the root Makefile."""
    found = sorted(PLUGINS_DIR.glob("*/Makefile"))
    found += sorted((PLUGINS_DIR / "abstract" / "config" / "make").glob("*.mk"))
    found.append(REPO_ROOT / "Makefile")
    return found


def _soft_assigned(makefile: Path) -> set[str]:
    """Variables assigned with `?=`, which an exported value overrides."""
    names = set()
    for line in makefile.read_text().splitlines():
        match = re.match(r"^\s*(\w+)\s*\?=", line)
        if match:
            names.add(match.group(1))
    return names


def _deleted_variables(makefile: Path) -> set[str]:
    """Variables appearing as the target of an `rm -r` in a recipe."""
    names = set()
    for line in makefile.read_text().splitlines():
        if not line.startswith("\t"):
            continue
        for match in _RM_VAR.finditer(line):
            names.add(match.group(1))
    return names


@pytest.mark.unit
@pytest.mark.parametrize("makefile", _makefiles(), ids=lambda p: str(p.name))
def test_no_recipe_deletes_an_environment_overridable_path(makefile: Path) -> None:
    """Scenario: a deletion target cannot be redirected by an env var."""
    overridable = _soft_assigned(makefile) & _deleted_variables(makefile)
    assert not overridable, (
        f"{makefile.relative_to(REPO_ROOT)} runs `rm -r` on "
        f"{sorted(overridable)}, assigned with `?=` so an exported value of "
        "the same name redirects the delete. Assign it with `:=`, or give "
        "the deletion target a name nothing else reads."
    )


@pytest.mark.unit
def test_the_guard_would_catch_the_memory_palace_shape() -> None:
    """Guard: the detector matches the pattern that motivated it.

    Without this, a regex that silently stopped matching would leave
    every parametrised case passing vacuously.
    """
    sample = "PALACES_DIR     ?= $(PWD)/.demo-palaces\ndemo-reset:\n\trm -rf $(PALACES_DIR)\n"
    scratch = Path(__file__).parent / "_destructive_sample.mk"
    scratch.write_text(sample, encoding="utf-8")
    try:
        assert _soft_assigned(scratch) == {"PALACES_DIR"}
        assert _deleted_variables(scratch) == {"PALACES_DIR"}
    finally:
        scratch.unlink()
