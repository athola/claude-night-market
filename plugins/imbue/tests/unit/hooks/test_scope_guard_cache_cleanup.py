"""The scope-guard hook must not strand its cache temp file.

``user-prompt-submit.sh`` writes its rendered output to a ``mktemp`` file
in the cache directory and renames it into place. There was no ``trap``
anywhere in the script, so every path that did not reach the rename left
the temp file behind. This hook runs on every prompt submission, which
makes the accumulation rate the rate of the failure path: six
``scope-guard-cache.XXXXXX`` files were sitting in the author's own
``~/.cache/imbue`` when the finding was written.

The reproduction replaces the destination with a read-only directory, so
``mv`` fails while ``mktemp`` still succeeds. A writable directory there
does not work: ``mv`` moves the file into it and exits 0, which is how an
earlier version of this test passed with the trap deleted. Making the
cache directory unwritable instead would stop ``mktemp`` too and prove
nothing.

The hook runs in a repository the test builds. It only reaches the cache
write when a ``main`` or ``master`` branch resolves, and a CI checkout of
a pull request has neither, so running it in this repository left the
outcome to how the checkout was made.
"""

from __future__ import annotations

import glob
import os
import subprocess
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[3] / "hooks" / "user-prompt-submit.sh"


def _make_repo(root: Path) -> Path:
    """Build a one-commit repository on ``master`` for the hook to measure."""
    root.mkdir()
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    for args in (
        ["init", "-q"],
        ["checkout", "-q", "-b", "master"],
        ["commit", "-q", "--allow-empty", "-m", "initial"],
    ):
        subprocess.run([*git, *args], cwd=str(root), check=True)
    return root


def _run(cache_home: Path, repo: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache_home)
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input="{}\n",
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
        timeout=120,
        check=False,
    )


@pytest.mark.unit
@pytest.mark.skipif(os.geteuid() == 0, reason="root writes through a 0555 directory")
def test_failed_cache_rename_leaves_no_temp_file(tmp_path: Path) -> None:
    """Scenario: the rename into place fails
    Given a cache destination that `mv` cannot overwrite
    When the hook runs
    Then no `scope-guard-cache.XXXXXX` temp file survives the exit.
    """
    cache_home = tmp_path / "cache"
    cache_dir = cache_home / "imbue"
    repo = _make_repo(tmp_path / "repo")

    first = _run(cache_home, repo)
    assert first.returncode == 0, first.stderr

    written = glob.glob(str(cache_dir / "scope-guard-cache-*.txt"))
    assert written, "the hook wrote no cache file, so the rename path was not taken"

    # Turn the destination into a read-only directory: mktemp still
    # succeeds in the cache directory, and mv can neither replace the
    # directory nor move the file into it.
    destination = Path(written[0])
    destination.unlink()
    destination.mkdir()
    destination.chmod(0o555)
    try:
        second = _run(cache_home, repo)
    finally:
        destination.chmod(0o755)
    assert second.returncode == 0, second.stderr

    stranded = glob.glob(str(cache_dir / "scope-guard-cache.*"))
    assert not stranded, f"temp files left behind after a failed rename: {stranded}"
