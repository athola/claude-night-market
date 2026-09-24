"""Every registered hook must import under the operator's interpreter.

Hooks do not run under a plugin's ``.venv``. They run under whatever
``python3`` the operator's PATH resolves, which carries the standard
library and nothing else. A hook that imports a project dependency at
module scope raises before it reads its payload, and the operator sees
a traceback on every tool call, prompt, or session boundary that fires
it.

This gate caught four: ``hookify/rule_guard.py`` on three events,
``abstract/pre_skill_execution.py``,
``abstract/skill_execution_logger.py``, and
``memory-palace/web_research_handler.py``. The memory-palace family had
already cost a traceback at every session start, through an eager
re-export in a package ``__init__`` that a leaf-module import had to
execute first.

PyYAML is the only dependency this has ever found, so it is the only
one blocked. Widening the list is one entry, but a blocked module that
nothing imports is a gate that tests its own fixture.

The probe registers the module in ``sys.modules`` before executing it.
Without that, ``dataclasses`` on Python 3.14 resolves a field type
through ``sys.modules[cls.__module__]`` and raises an ``AttributeError``
that has nothing to do with the hook.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Dependencies an operator's interpreter is not expected to carry.
_BLOCKED_MODULES = ("yaml",)

_PLUGIN_ROOT_COMMAND = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+\.py)")

_PROBE = """
import importlib.util
import sys

path = sys.argv[1]
sys.path.insert(0, str(__import__("pathlib").Path(path).parent))
spec = importlib.util.spec_from_file_location("hook_under_test", path)
module = importlib.util.module_from_spec(spec)
sys.modules["hook_under_test"] = module
spec.loader.exec_module(module)
"""


def _registered_hooks() -> list[tuple[str, str, str]]:
    """Return (plugin, relative path, events) for every python hook."""
    found: dict[tuple[str, str], set[str]] = {}
    for manifest in sorted(REPO_ROOT.glob("plugins/*/hooks/hooks.json")):
        plugin = manifest.parts[-3]
        config = json.loads(manifest.read_text(encoding="utf-8"))
        for event, groups in config.get("hooks", {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    for relative in _PLUGIN_ROOT_COMMAND.findall(
                        hook.get("command", "")
                    ):
                        found.setdefault((plugin, relative), set()).add(event)
    return [
        (plugin, relative, ",".join(sorted(events)))
        for (plugin, relative), events in sorted(found.items())
    ]


_HOOKS = _registered_hooks()


def test_the_sweep_found_hooks_to_check() -> None:
    """GIVEN a repository that registers hooks.

    WHEN the discovery finds none
    THEN every case below passes vacuously and the gate is decorative
    """
    assert len(_HOOKS) > 20, f"only discovered {len(_HOOKS)} hook registrations"


@pytest.mark.parametrize(
    ("plugin", "relative", "events"),
    _HOOKS,
    ids=[f"{plugin}/{relative}" for plugin, relative, _ in _HOOKS],
)
def test_hook_imports_with_project_dependencies_blocked(
    plugin: str, relative: str, events: str, tmp_path: Path
) -> None:
    """GIVEN a hook the plugin registers for a Claude Code event.

    WHEN the interpreter running it carries only the standard library
    THEN the hook imports rather than raising ModuleNotFoundError
    """
    hook = REPO_ROOT / "plugins" / plugin / relative
    assert hook.is_file(), f"{plugin} registers {relative}, which is not on disk"

    blocks = "\n".join(f'sys.modules["{name}"] = None' for name in _BLOCKED_MODULES)
    (tmp_path / "sitecustomize.py").write_text(f"import sys\n\n{blocks}\n")

    completed = subprocess.run(
        [sys.executable, "-c", _PROBE, str(hook)],
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, (
        f"{plugin}/{relative} (registered for {events}) "
        f"cannot import without {', '.join(_BLOCKED_MODULES)}:\n{completed.stderr}"
    )
