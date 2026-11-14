"""scripts/logging.sh must honor LOG_LEVEL values it does not expect.

A word such as `info` or `debug` is common in user environments. The
numeric test errored on it and returned early, so every line below CRIT
disappeared, errors included.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

LOGGING_SH = Path(__file__).resolve().parents[2] / "scripts" / "logging.sh"


def _log(level: str, message: str, log_level: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", "-c", f'. "{LOGGING_SH}"; log {level} {message}'],
        capture_output=True,
        text=True,
        env={**os.environ, "LOG_LEVEL": log_level},
        check=True,
    )


@pytest.mark.parametrize("log_level", ["info", "debug", "verbose", ""])
def test_an_error_prints_whatever_log_level_holds(log_level: str) -> None:
    result = _log("4", "boom", log_level)
    assert "[ERROR] boom" in result.stderr
    assert "integer expression" not in result.stderr


@pytest.mark.parametrize(("name", "shown"), [("debug", True), ("warn", False)])
def test_level_names_map_to_their_numbers(name: str, shown: bool) -> None:
    """The names the library documents select the same threshold as the digits."""
    assert ("[INFO]  hi" in _log("1", "hi", name).stdout) is shown
