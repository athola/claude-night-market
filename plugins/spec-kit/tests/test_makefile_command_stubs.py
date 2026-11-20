"""The generated ``test-<command>`` targets must not read as passing tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make is not installed")
def test_a_command_stub_target_fails_instead_of_passing() -> None:
    """GIVEN a command with no automated test.

    WHEN its ``test-<command>`` target runs
    THEN make exits nonzero and says the command is untested

    The stub used to print "Validating: /<command>" and exit 0, which read
    as a passing test for a command nothing tests.
    """
    command = sorted(PLUGIN.glob("commands/*.md"))[0].stem
    result = subprocess.run(
        ["make", "-C", str(PLUGIN), f"test-{command}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode != 0
    assert "No automated test" in result.stdout
    assert "Validating" not in result.stdout
