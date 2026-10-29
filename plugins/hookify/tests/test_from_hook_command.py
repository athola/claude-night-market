"""/hookify:from-hook runs the converter instead of describing it.

The command listed what scripts/hook_to_hookify.py does and never named
the script, so a session converted hooks by reading them itself while a
tested converter sat unreachable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PLUGIN_ROOT / "commands" / "from-hook.md"
SCRIPT = PLUGIN_ROOT / "scripts" / "hook_to_hookify.py"


def _documented_example() -> str:
    text = COMMAND.read_text()
    start = text.index("```python\n") + len("```python\n")
    return text[start : text.index("```", start)]


def test_command_invokes_the_converter_script() -> None:
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/hook_to_hookify.py" in COMMAND.read_text()


def test_the_documented_example_converts_to_a_bash_rule(
    tmp_path: Path,
) -> None:
    hook_file = tmp_path / "guard.py"
    hook_file.write_text(_documented_example())
    rules = tmp_path / "rules.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), str(hook_file), "-o", str(rules)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = rules.read_text()
    assert "event: bash" in text
    assert "rm -rf /" in text
    assert "action: warn" in text


_NETWORK_HOOK = """# PreToolUse
import requests
def hook(context):
    return requests.get("http://api.example.com").json()
"""


def _convert(hooks: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scan", str(hooks), "-o", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_unconvertible_hooks_are_named_with_their_reason_without_v(
    tmp_path: Path,
) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "guard.py").write_text(_documented_example())
    (hooks / "fetcher.py").write_text(_NETWORK_HOOK)

    run = _convert(hooks, tmp_path / "rules.md")

    assert run.returncode == 0
    assert "fetcher.py" in run.stderr
    assert "network" in run.stderr.lower()
    assert "guard.py" not in run.stderr


def test_a_run_that_converts_nothing_exits_nonzero(tmp_path: Path) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "fetcher.py").write_text(_NETWORK_HOOK)

    run = _convert(hooks, tmp_path / "rules.md")

    assert run.returncode == 1
    assert "fetcher.py" in run.stderr
