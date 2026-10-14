"""Scripts that need leyline say so when it is missing, instead of crashing.

ADR-0001 asks a plugin to turn a feature off cleanly when a peer is absent.
These scripts imported leyline unguarded, so running one without leyline
(or in an install where the old repo-only path could not find it) ended in
an ImportError traceback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "plugins/abstract/scripts/promote_discussion_to_issue.py",
    "plugins/conserve/scripts/coordination_workspace.py",
    "plugins/conserve/scripts/safe_replacer.py",
    "plugins/conserve/scripts/area_agent_registry.py",
    "plugins/sanctum/scripts/quality_checker.py",
    "plugins/sanctum/scripts/test_generator.py",
]

_RUN_WITHOUT_LEYLINE = """
import importlib.abc
import runpy
import sys


class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] == "leyline":
            raise ModuleNotFoundError(f"No module named {name!r}")
        return None


sys.meta_path.insert(0, _Block())
sys.argv = [sys.argv[1], "--help"]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_reports_missing_leyline_without_a_traceback(script: str) -> None:
    proc = subprocess.run(
        [sys.executable, "-c", _RUN_WITHOUT_LEYLINE, str(REPO / script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1, proc.stderr
    assert "requires the leyline plugin" in proc.stderr
    assert "Traceback" not in proc.stderr


_IMPORT_WITHOUT_LEYLINE = """
import importlib.abc
import runpy
import sys


class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] == "leyline":
            raise ModuleNotFoundError(f"No module named {name!r}")
        return None


sys.meta_path.insert(0, _Block())
try:
    runpy.run_path(sys.argv[1], run_name="imported_as_library")
except ImportError:
    print("import-error")
except SystemExit:
    print("system-exit")
"""


@pytest.mark.parametrize("script", SCRIPTS)
def test_importing_script_without_leyline_raises_import_error(script: str) -> None:
    """An importer gets ImportError to handle; only a direct run exits."""
    proc = subprocess.run(
        [sys.executable, "-c", _IMPORT_WITHOUT_LEYLINE, str(REPO / script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.stdout.strip() == "import-error", proc.stdout + proc.stderr
