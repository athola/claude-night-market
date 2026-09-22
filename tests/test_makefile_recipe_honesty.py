"""Recipes must not report a verdict their commands cannot produce.

Four shapes, all found live, all of which make a target's output say
something its exit status does not.

**A test whose status never reaches the shell.** Six plugins printed
skill coverage like this::

    @echo "  api-review: $$(test -f skills/api-review/SKILL.md && echo '[OK]' || echo '[X]')"

``test`` runs inside a command substitution whose output ``echo`` prints,
so ``echo`` exits 0 whatever ``test`` found. Measured against a tree with
three of pensive's five skills removed, the old recipe exited 0 and the
rewritten one exits 2.

**A stopping failure announced as advisory.** ``python.mk`` wrapped seven
checkers in ``|| { echo "[WARN] ..."; exit 1; }``. The ``exit 1`` is what
the reader scanning CI output does not see; the ``[WARN]`` is what they
do. ``test-coverage`` at the same indent omits the wrapper entirely and
behaves identically, which is the proof the wrapper buys nothing beyond
its label.

**A fallback the shell can never reach.** Nine recipes ended a pipeline
in ``head`` or ``tail`` and then hung an ``||`` arm off it::

    @git diff --stat HEAD~3..HEAD 2>/dev/null | head -10 || git diff --stat HEAD~1..HEAD

A pipeline's status is its last command's, and ``head`` exits 0 whatever
reached it, so the fallback was dead code. Measured on a one-commit
repository, where ``HEAD~3`` does not resolve: the old recipe printed an
empty line under "Change summary" and reported success, the rewritten one
prints its fallback. This compounds the missing ``-o pipefail``, which is
what the shape relied on.

**A banner that prints only on success.** The root ``plugin-check`` ends
its loop line with ``exit $$fail``, and the root ``Makefile`` sets no
``.ONESHELL``, so each recipe line is its own shell. Trailing ``@echo``
lines therefore ran when ``fail`` was 0 and were skipped when it was 1: a
completion banner that appears only when nothing failed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"

# `... && echo '[OK]' || echo '[X]'` inside a command substitution.
LAUNDERED_VERDICT = re.compile(r"\$\$\([^)]*\|\|\s*echo\s*'?\[X\]'?[^)]*\)")

# A label that says "advisory" on a line that stops the build.
ADVISORY_FAILURE = re.compile(r"\[WARN\][^\n]*exit\s+1")

# A pipeline ending in head/tail with an `||` arm hung off it. The class
# excludes `)` and `"` so a filter used inside `$( )`, where the `||`
# belongs to the enclosing `&&` and is reachable, is not swept up:
# `plugins/scry/Makefile:48` is that shape and is correct.
UNREACHABLE_FALLBACK = re.compile(r"\|\s*(?:head|tail)\b[^|)\"]*\|\|")


def _make_files() -> list[Path]:
    found = [REPO_ROOT / "Makefile"]
    found += list(PLUGINS.rglob("Makefile"))
    found += list(PLUGINS.rglob("*.mk"))
    return sorted({p for p in found if p.is_file()})


def test_discovery_finds_make_files() -> None:
    """An empty parametrize list would make the guards below vacuous."""
    assert len(_make_files()) > 20


@pytest.mark.parametrize(
    "path", _make_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_no_verdict_is_laundered_through_a_command_substitution(path: Path) -> None:
    """A failed check has to be able to fail the recipe."""
    text = path.read_text(encoding="utf-8")
    offenders = [
        line.strip() for line in text.splitlines() if LAUNDERED_VERDICT.search(line)
    ]
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} prints a [X] verdict from inside a "
        "command substitution, so the recipe exits 0 whatever the test found:"
        "\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize(
    "path", _make_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_a_build_stopping_failure_is_not_labelled_a_warning(path: Path) -> None:
    """[WARN] on a line that exits 1 misreports the severity."""
    text = path.read_text(encoding="utf-8")
    offenders = [
        line.strip() for line in text.splitlines() if ADVISORY_FAILURE.search(line)
    ]
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} labels a build-stopping failure [WARN]:"
        "\n  " + "\n  ".join(offenders)
    )


def test_plugin_check_banner_is_reachable_on_failure() -> None:
    """A completion banner after `exit $$fail` prints only when nothing failed."""
    lines = (REPO_ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    exits = [i for i, line in enumerate(lines) if line.strip().endswith("exit $$fail")]
    assert exits, "the plugin-check accumulation loop is gone; update this guard"
    for index in exits:
        trailing = []
        for line in lines[index + 1 :]:
            if not line.startswith("\t"):
                break
            trailing.append(line.strip())
        assert not trailing, (
            "these recipe lines follow `exit $$fail` in the root Makefile and "
            "so run only on the success path:\n  " + "\n  ".join(trailing)
        )


@pytest.mark.parametrize(
    "path", _make_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_no_fallback_hangs_off_a_filter_that_launders_the_status(path: Path) -> None:
    """`cmd | head || fallback` never takes the fallback."""
    text = path.read_text(encoding="utf-8")
    offenders = [
        line.strip() for line in text.splitlines() if UNREACHABLE_FALLBACK.search(line)
    ]
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} pipes into a filter and then offers a "
        "fallback the shell cannot reach, because the pipeline's status is the "
        "filter's:\n  " + "\n  ".join(offenders)
    )
