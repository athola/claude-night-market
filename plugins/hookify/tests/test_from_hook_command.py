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
