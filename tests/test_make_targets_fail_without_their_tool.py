"""`make validate-skills` and conjure's `make delegate-test` report failure.

Both targets used to print a notice and exit 0: validate-skills when
skrills was absent, delegate-test when an installed provider failed. A
gate that passes without running its check reads as a pass in CI.

Each recipe runs for real, with PATH reduced to stubs and the system
directories, so the tool the target needs is absent or scripted to fail.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = "/usr/bin:/bin"

#: Stands in for `uv run python scripts/delegation_executor.py ...`.
#: One provider, "fake", which is installed and fails the round trip.
FAKE_UV = """#!/bin/sh
case "$*" in
  *--list-services*) printf 'fake: a scripted provider\\n' ;;
  *"--verify fake"*) exit {verify} ;;
  *"fake Respond"*) exit 1 ;;
esac
exit 0
"""


def _make(path: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "--no-print-directory", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": path},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_validate_skills_fails_when_skrills_is_absent() -> None:
    result = _make(SYSTEM_PATH, "validate-skills", "SKRILLS_BIN=/nonexistent")
    assert result.returncode != 0
    assert "skrills not available" in result.stderr


def _fake_uv(tmp_path: Path, verify: int) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv = bin_dir / "uv"
    uv.write_text(FAKE_UV.format(verify=verify))
    uv.chmod(0o755)
    return f"{bin_dir}:{SYSTEM_PATH}"


def test_delegate_test_fails_when_an_installed_provider_fails(
    tmp_path: Path,
) -> None:
    result = _make(
        _fake_uv(tmp_path, verify=0), "-C", "plugins/conjure", "delegate-test"
    )
    assert result.returncode != 0
    assert "fake FAILED" in result.stdout


def test_delegate_test_passes_over_a_provider_that_is_not_installed(
    tmp_path: Path,
) -> None:
    result = _make(
        _fake_uv(tmp_path, verify=1), "-C", "plugins/conjure", "delegate-test"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "fake not available" in result.stdout
