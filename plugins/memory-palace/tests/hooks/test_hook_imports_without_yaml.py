"""SessionStart hooks must import with nothing but the standard library.

Hooks run under whatever ``python3`` the operator's PATH resolves, which
is a system or Homebrew interpreter with no project dependencies
installed, not the plugin's ``.venv``. PyYAML is the one that keeps
reappearing: a hook that only wants ``persistent_root`` from
``memory_palace.paths`` executes the package ``__init__`` first, and an
eager import there of any yaml-dependent module turns every session
start into a traceback.

``sys.modules["yaml"] = None`` is the isolation rather than the absence
of the package, because the interpreter running these tests has PyYAML
installed and the interpreter running the hook does not.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_HOOKS = _PLUGIN_ROOT / "hooks"
_SRC = _PLUGIN_ROOT / "src"


def _session_start_hooks() -> list[str]:
    """Return the SessionStart hook files this plugin registers.

    Read from ``hooks.json`` rather than listed here, so registering a
    second one does not quietly leave it unchecked.
    """
    config = json.loads((_HOOKS / "hooks.json").read_text(encoding="utf-8"))
    names = set()
    for group in config.get("hooks", {}).get("SessionStart", []):
        for hook in group.get("hooks", []):
            names.update(re.findall(r"hooks/(\S+\.py)", hook.get("command", "")))
    return sorted(names)


_SESSION_START_HOOKS = _session_start_hooks()


def _yaml_blocked_env(tmp_path: Path) -> dict[str, str]:
    """Return an environment whose interpreter cannot import yaml.

    ``sitecustomize`` runs before the script, so the block is in place
    for the hook's own imports rather than only for this process.
    """
    (tmp_path / "sitecustomize.py").write_text(
        'import sys\n\nsys.modules["yaml"] = None\n'
    )
    return {"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"}


def test_paths_imports_when_yaml_is_unavailable(tmp_path: Path) -> None:
    """``memory_palace.paths`` is stdlib-only and must stay reachable.

    Guards the data root that issue #661 stranded: a hook that cannot
    import this module cannot find where user captures live.
    """
    completed = subprocess.run(
        [sys.executable, "-c", "import memory_palace.paths"],
        cwd=_SRC,
        env=_yaml_blocked_env(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("hook_name", _SESSION_START_HOOKS)
def test_session_start_hook_reports_no_traceback_without_yaml(
    hook_name: str, tmp_path: Path
) -> None:
    """A SessionStart hook must not print a traceback on a clean start."""
    payload = json.dumps(
        {
            "session_id": "test-session",
            "transcript_path": str(tmp_path / "transcript.jsonl"),
            "cwd": str(tmp_path),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )

    completed = subprocess.run(
        [sys.executable, str(_HOOKS / hook_name)],
        cwd=str(tmp_path),
        env=_yaml_blocked_env(tmp_path),
        input=payload,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert "Traceback" not in completed.stderr, completed.stderr
