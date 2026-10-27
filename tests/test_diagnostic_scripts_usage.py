"""The restyled diagnostic scripts keep the shell-rules help contract.

`.claude/rules` shell rules ask `-h` and any `*usage`/`*help` argument
to print usage starting with "Usage:" and exit 0. The structural gates
(shfmt, shellcheck, main) do not run a script, so nothing exercised it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    ROOT / "scripts" / "capabilities-sync-check.sh",
    ROOT
    / ".claude"
    / "skills"
    / "night-market-diagnostics-toolkit"
    / "scripts"
    / "health-snapshot.sh",
)


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
@pytest.mark.parametrize("flag", ["-h", "--help", "usage"])
def test_help_prints_usage_and_exits_zero(script: Path, flag: str) -> None:
    run = _run(script, flag)

    assert run.returncode == 0, run.stderr
    assert "Usage:" in run.stdout + run.stderr


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_unknown_option_is_rejected(script: Path) -> None:
    """A mistyped flag must fail, not run the check as if absent."""
    run = _run(script, "--bogus")

    assert run.returncode == 1
    assert "Unknown option: --bogus" in run.stdout + run.stderr
