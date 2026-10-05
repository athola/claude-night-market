"""Every tracked shell script is formatted the way the shell rules require.

`.claude/rules/shell-scripts.md` requires `shfmt -i 2 -ci`, and nothing
checked it: the 2026-10-05 shell review found 19 of 39 scripts out of
format. The dialect comes from each shebang, so bash scripts are not
parsed as POSIX sh. CI pins shfmt 3.13.1; 3.10.0, the previous pin,
formats every script here identically.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("shfmt") is None, reason="shfmt is not installed"
)


def _shell_scripts() -> list[str]:
    """Tracked *.sh files plus executables with a sh or bash shebang."""
    listing = subprocess.run(
        ["git", "ls-files", "-s"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    scripts = []
    for row in listing:
        mode, _sha, _stage, path = row.split(maxsplit=3)
        if path.endswith(".sh"):
            scripts.append(path)
        elif mode == "100755" and "." not in Path(path).name:
            first = (ROOT / path).read_text(errors="replace").split("\n", 1)[0]
            if re.match(r"#!.*([/ ]sh( |$)|bash)", first):
                scripts.append(path)
    return scripts


def test_every_shell_script_is_shfmt_clean() -> None:
    scripts = _shell_scripts()
    assert scripts
    result = subprocess.run(
        ["shfmt", "-i", "2", "-ci", "-l", *scripts],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stderr == ""
    assert result.stdout == "", "run `shfmt -i 2 -ci -w` on:\n" + result.stdout
