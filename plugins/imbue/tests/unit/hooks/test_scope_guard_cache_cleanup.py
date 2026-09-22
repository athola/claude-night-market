"""The scope-guard hook must not strand its cache temp file.

``user-prompt-submit.sh`` writes its rendered output to a ``mktemp`` file
in the cache directory and renames it into place. There was no ``trap``
anywhere in the script, so every path that did not reach the rename left
the temp file behind. This hook runs on every prompt submission, which
makes the accumulation rate the rate of the failure path: six
``scope-guard-cache.XXXXXX`` files were sitting in the author's own
``~/.cache/imbue`` when the finding was written.

The reproduction replaces the destination with a non-empty directory, so
``mv`` fails while ``mktemp`` still succeeds. Making the directory
unwritable instead would stop ``mktemp`` too and prove nothing.
"""

from __future__ import annotations

import glob
import os
import subprocess
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[3] / "hooks" / "user-prompt-submit.sh"
REPO_ROOT = Path(__file__).parents[5]


def _run(cache_home: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache_home)
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input="{}\n",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=120,
        check=False,
    )


@pytest.mark.unit
def test_failed_cache_rename_leaves_no_temp_file(tmp_path: Path) -> None:
    """Scenario: the rename into place fails
    Given a cache destination that `mv` cannot overwrite
    When the hook runs
    Then no `scope-guard-cache.XXXXXX` temp file survives the exit.
    """
    cache_home = tmp_path / "cache"
    cache_dir = cache_home / "imbue"

    first = _run(cache_home)
    assert first.returncode == 0, first.stderr

    written = glob.glob(str(cache_dir / "scope-guard-cache-*.txt"))
    assert written, "the hook wrote no cache file, so the rename path was not taken"

    # Turn the destination into a non-empty directory: mktemp still
    # succeeds, mv cannot replace it.
    destination = Path(written[0])
    destination.unlink()
    destination.mkdir()
    (destination / "occupied").write_text("x", encoding="utf-8")

    second = _run(cache_home)
    assert second.returncode == 0, second.stderr

    stranded = glob.glob(str(cache_dir / "scope-guard-cache.*"))
    assert not stranded, f"temp files left behind after a failed rename: {stranded}"
