"""``debug-variables`` must not report a value the recipes do not have.

``common.mk`` carried ``PYTHONPATH ?= src``. Make hands a variable to a
recipe's environment only when it arrived from the environment or is
marked ``export``, and a plain assignment is neither, so no recipe in any
of the 22 plugins that include the file ever saw ``PYTHONPATH=src``.

The declaration was not merely inert. Every plugin's ``debug-variables``
target echoes ``$(PYTHONPATH)``, so the value printed while debugging was
``src`` and the value a recipe ran under was empty. The tell was already
in the tree: ``plugins/abstract/Makefile:99`` sets it inline, right beside
the shared declaration that was supposed to have covered it.

With the declaration gone, the reported value is whatever the caller's
environment holds, which is exactly what a recipe inherits. Restoring
``PYTHONPATH ?= src`` makes this test red.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _debug_variables(plugin: str, env: dict[str, str]) -> str:
    result = subprocess.run(
        ["make", "-C", f"plugins/{plugin}", "debug-variables"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for line in result.stdout.splitlines():
        if line.strip().startswith("PYTHONPATH:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(
        f"debug-variables printed no PYTHONPATH line:\n{result.stdout}"
    )


def test_pythonpath_is_not_reported_when_no_recipe_would_see_it() -> None:
    """An unset PYTHONPATH must read as unset, not as a phantom default."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    assert _debug_variables("abstract", env) == ""


def test_pythonpath_from_the_environment_is_reported() -> None:
    """An environment value does reach recipes, so it should be shown."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "from-the-caller"
    assert _debug_variables("abstract", env) == "from-the-caller"
