"""The pre-commit maintenance hook runs on a host without md5sum.

Shell review S1-12. hash_of called md5sum, which macOS lacks before 14
and BSD does not ship. With the index present, set -e ended the hook
with 127, and every commit was blocked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
SCRIPT = PLUGIN / "scripts" / "precommit_palace_maintenance.sh"


def test_the_hook_runs_without_md5sum(tmp_path: Path) -> None:
    hooks = tmp_path / "plugins" / "memory-palace" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "memory-palace-index.yaml").write_text("entries: {}\n")
    shims = tmp_path / "shims"
    shims.mkdir()
    (shims / "uv").write_text("#!/bin/sh\nexit 0\n")
    (shims / "uv").chmod(0o755)
    git = shutil.which("git", path="/usr/bin:/opt/homebrew/bin:/usr/local/bin")
    assert git is not None
    (shims / "git").symlink_to(git)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = f"{shims}:/usr/bin:/bin"
    assert shutil.which("md5sum", path=env["PATH"]) is None
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
