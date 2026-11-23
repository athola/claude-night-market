"""Skills run the capture wrapper from the plugin root, not the cwd.

A bare `python3 scripts/deferred_capture.py` resolves against the user's
project, where no such file exists, and each module's "skip if not present"
note turned that into a silent skip (ARCH-7).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BARE_CALL = re.compile(r"python3\s+scripts/deferred_capture\.py")


def test_no_skill_calls_the_capture_wrapper_by_a_cwd_relative_path() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{lineno}"
        for path in sorted((ROOT / "plugins").rglob("*.md"))
        for lineno, line in enumerate(path.read_text().splitlines(), 1)
        if BARE_CALL.search(line)
    ]
    assert offenders == []


MODULE_CALL = re.compile(
    r"python3\s+\"\$\{CLAUDE_PLUGIN_ROOT[^}]*\}/scripts/deferred_capture"
)


def test_a_module_call_stops_when_the_plugin_root_is_unset() -> None:
    """A module is read, not substituted like a SKILL.md body.

    In the Bash tool ``${CLAUDE_PLUGIN_ROOT}`` is unset, so the call ran
    ``/scripts/deferred_capture.py``, which is absent, and the module's
    "skip if not present" rule skipped the capture without a word.
    """
    calls = [
        (path, line)
        for path in sorted((ROOT / "plugins").glob("*/skills/*/modules/*.md"))
        for line in path.read_text().splitlines()
        if MODULE_CALL.search(line)
    ]
    assert calls
    unguarded = [
        str(path.relative_to(ROOT))
        for path, line in calls
        if "${CLAUDE_PLUGIN_ROOT:?" not in line
    ]
    assert unguarded == []


def test_an_unset_plugin_root_stops_the_module_call(tmp_path: Path) -> None:
    """Run each module's call line with the variable unset."""
    env = {"PATH": "/usr/bin:/bin"}
    for path in sorted((ROOT / "plugins").glob("*/skills/*/modules/*.md")):
        for line in path.read_text().splitlines():
            if not MODULE_CALL.search(line):
                continue
            command = line.rstrip(" \\") + " --help"
            result = subprocess.run(
                ["/bin/sh", "-c", command],
                cwd=tmp_path,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode != 0, path
            assert "CLAUDE_PLUGIN_ROOT" in result.stderr, result.stderr
