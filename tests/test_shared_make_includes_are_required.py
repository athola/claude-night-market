"""The shared ``.mk`` files are dependencies, not optional overrides.

Every plugin Makefile loaded them with ``-include``, whose leading dash
tells make to carry on when the file is missing. ``Makefile.local`` earns
that dash: it is an optional per-developer override that usually does not
exist. ``common.mk`` and ``python.mk`` do not.

What a silent miss costs: ``$(UV_RUN)``, ``$(PYTEST)`` and ``$(RUFF)``
become empty, so every recipe runs its arguments as a bare command, and
``.DEFAULT_GOAL`` becomes unset, so the default goal falls back to rule
order. That last one is the defect ``tests/test_makefile_default_goal.py``
guards, returning through the back door: ``python.mk``'s first rule is
``format``, which rewrites the tree.

The second test proves the distinction is load-bearing rather than
cosmetic, by pointing ``ABSTRACT_DIR`` at a path that does not exist and
watching make refuse to proceed.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"

OPTIONAL_INCLUDE = re.compile(r"^-include\s+(\S+)", re.MULTILINE)
# The one include that is genuinely optional.
ALLOWED_OPTIONAL = {"Makefile.local"}


def _plugin_makefiles() -> list[Path]:
    return sorted(PLUGINS.glob("*/Makefile"))


def test_discovery_finds_plugin_makefiles() -> None:
    """An empty parametrize list would make the guard below vacuous."""
    assert len(_plugin_makefiles()) > 15


@pytest.mark.parametrize("path", _plugin_makefiles(), ids=lambda p: p.parent.name)
def test_shared_mk_is_a_hard_include(path: Path) -> None:
    """Only Makefile.local may be loaded with a leading dash."""
    offenders = [
        target
        for target in OPTIONAL_INCLUDE.findall(path.read_text(encoding="utf-8"))
        if target not in ALLOWED_OPTIONAL
    ]
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} loads {offenders} with `-include`, so a "
        "missing or moved abstract plugin degrades the build silently instead "
        "of failing it."
    )


def test_a_missing_shared_mk_stops_the_build() -> None:
    """The hard include is what turns a missing dependency into an error."""
    env = os.environ.copy()
    result = subprocess.run(
        ["make", "-C", "plugins/pensive", "-n", "help", "ABSTRACT_DIR=/nonexistent"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )
    assert result.returncode != 0, (
        "make succeeded with the shared .mk files absent, which is the "
        "degraded state this guard exists to prevent"
    )
