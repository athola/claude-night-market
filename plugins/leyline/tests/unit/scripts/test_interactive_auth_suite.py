"""Run the interactive_auth.sh suite, which nothing else executes.

The suite drives the sourced library end to end under ``set -u``. It
stopped at Test 13 for as long as it has existed, because looking up an
unknown service in an associative array is fatal there, and no gate ran
it to notice.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SUITE = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "authentication-patterns"
    / "tests"
    / "test-interactive-auth.sh"
)
# The library uses `declare -A`, which bash 4 introduced.
MIN_BASH_MAJOR = 4


def _modern_bash() -> str | None:
    for candidate in (shutil.which("bash"), "/opt/homebrew/bin/bash", "/bin/bash"):
        if not candidate or not Path(candidate).exists():
            continue
        major = subprocess.run(
            [candidate, "-c", "printf %s ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if major.isdigit() and int(major) >= MIN_BASH_MAJOR:
            return candidate
    return None


def test_interactive_auth_suite_runs_to_completion(tmp_path: Path) -> None:
    bash = _modern_bash()
    if bash is None:
        pytest.skip("interactive_auth.sh needs bash 4 or newer")

    result = subprocess.run(
        [bash, str(SUITE)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "CI": ""},
    )

    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    assert "Correctly rejected unsupported service" in result.stdout
