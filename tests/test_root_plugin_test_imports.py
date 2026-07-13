"""Test: plugin tests are importable when pytest runs from the repo root.

Each plugin's ``pyproject.toml`` sets ``pythonpath = [".", "src"]``, which is
what makes ``import pensive`` work when pytest runs inside ``plugins/pensive``
and takes that file as its rootdir.

Pass two plugin paths to pytest from the repo root and only one ini file wins:
the root ``pyproject.toml``. It has no ``pythonpath``, so every plugin test
that imports its own package dies at collection with ``ModuleNotFoundError``.
The natural command for "test the two plugins I touched" was the one command
that could not work, and it failed in a way that reads like the developer's own
change broke the build.

The root ``conftest.py`` now puts every ``plugins/*/src`` on ``sys.path``, so
the import resolves regardless of which rootdir pytest picked.

Per-plugin coverage gates (``--cov``, the 85% threshold) live in each plugin's
own ``addopts`` and still do NOT apply to a root-level run. ``make test``
remains the gate of record. This suite guards importability, not coverage.

Feature: plugin packages import cleanly under a root-level pytest run.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Note on what is NOT tested here. Handing pytest a single path under
# plugins/pensive makes it pick that plugin's pyproject.toml as rootdir, so
# the plugin's own pythonpath applies and the import resolves with or without
# the conftest wiring. A test asserting that would be green before the fix and
# green after it, which is a guard over nothing. Only the multi-plugin
# invocation below actually exercises the bug.


@pytest.mark.ecosystem
def test_plugin_src_dirs_are_on_sys_path() -> None:
    """
    Scenario: a developer runs pytest from the repo root
    Given the root conftest has been loaded
    When sys.path is inspected
    Then every plugin's src directory is present.
    """
    plugin_src_dirs = sorted(p for p in REPO_ROOT.glob("plugins/*/src") if p.is_dir())
    assert plugin_src_dirs, "expected at least one plugins/*/src directory"

    on_path = {Path(entry).resolve() for entry in sys.path}
    missing = [str(d) for d in plugin_src_dirs if d.resolve() not in on_path]

    assert not missing, (
        "root conftest must put every plugin src dir on sys.path so plugin "
        f"tests import under a root-level run; missing: {missing}"
    )


@pytest.mark.ecosystem
def test_cross_plugin_collection_succeeds() -> None:
    """
    Scenario: a developer tests the two plugins they touched, in one command
    Given two plugin test directories passed to pytest from the repo root
    When pytest collects them
    Then collection succeeds and no plugin package fails to import.

    This is the regression guard. Strip the sys.path wiring from the root
    conftest and this test goes red with the same ModuleNotFoundError a
    developer would have hit.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "plugins/archetypes/tests",
            "plugins/pensive/tests",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr

    assert "ModuleNotFoundError" not in output, (
        "a plugin package failed to import during a root-level run:\n" + output
    )
    assert result.returncode == 0, (
        f"cross-plugin collection failed (exit {result.returncode}):\n{output}"
    )
