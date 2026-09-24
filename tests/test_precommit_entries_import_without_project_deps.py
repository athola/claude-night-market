"""Every bare-python3 pre-commit entry must import under PATH python.

A ``language: system`` hook whose entry begins ``python3`` runs under
whatever interpreter the operator's PATH resolves when ``git commit``
fires it. That interpreter carries the standard library and nothing
else. ``uv run pre-commit run`` hides the difference, because uv puts
the venv first on PATH, so a hook can pass every local dry run and
fail the first real commit.

Two entries failed that way on 2026-09-22 (``fix_descriptions.py`` and
``context_optimizer.py``), and a sweep found two more that would have
(``abstract_validator.py``, ``validate_knowledge_corpus.py``). An entry
that needs a project dependency says so by running through
``uv run --with <dep> python``, the form ``slop-ratchet`` uses.

Same isolation as ``test_hooks_import_without_project_deps.py``:
PyYAML is blocked through ``sitecustomize`` because the interpreter
running the tests has it and the one running the hook does not.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".pre-commit-config.yaml"

_BLOCKED_MODULES = ("yaml",)
_BARE_PYTHON_ENTRY = re.compile(r"^\s*entry:\s*python3\s+(\S+\.py)", re.M)

_PROBE = """
import importlib.util
import sys

path = sys.argv[1]
sys.path.insert(0, str(__import__("pathlib").Path(path).parent))
spec = importlib.util.spec_from_file_location("entry_under_test", path)
module = importlib.util.module_from_spec(spec)
sys.modules["entry_under_test"] = module
spec.loader.exec_module(module)
"""


def _bare_python_entries() -> list[str]:
    return sorted(set(_BARE_PYTHON_ENTRY.findall(CONFIG.read_text(encoding="utf-8"))))


_ENTRIES = _bare_python_entries()


def test_the_config_still_has_bare_python_entries_to_check() -> None:
    """GIVEN a config that runs scripts under PATH python.

    WHEN discovery finds none
    THEN every case below passes vacuously and the gate is decorative
    """
    assert len(_ENTRIES) > 5, f"only discovered {len(_ENTRIES)} entries"


@pytest.mark.parametrize("script", _ENTRIES, ids=_ENTRIES)
def test_entry_imports_with_project_dependencies_blocked(
    script: str, tmp_path: Path
) -> None:
    """GIVEN a pre-commit entry that runs a script under bare python3.

    WHEN the interpreter carries only the standard library
    THEN the script imports rather than raising ModuleNotFoundError
    """
    path = REPO_ROOT / script
    assert path.is_file(), f"config runs {script}, which is not on disk"

    blocks = "\n".join(f'sys.modules["{name}"] = None' for name in _BLOCKED_MODULES)
    (tmp_path / "sitecustomize.py").write_text(f"import sys\n\n{blocks}\n")

    completed = subprocess.run(
        [sys.executable, "-c", _PROBE, str(path)],
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, (
        f"{script} runs under bare python3 but cannot import without "
        f"{', '.join(_BLOCKED_MODULES)}; give the entry "
        f"`uv run --with pyyaml python`:\n{completed.stderr}"
    )
