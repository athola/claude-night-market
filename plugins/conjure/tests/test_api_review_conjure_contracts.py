"""Contract tests for API-review findings on conjure CLI scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import quota_tracker

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _run_module(module: str, *args: str, home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", f"scripts.{module}", *args],
        cwd=PLUGIN_ROOT,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_delegator_reports_unknown_service_without_traceback(tmp_path: Path) -> None:
    """An unknown service name exits 1 with a message, not a KeyError."""
    proc = _run_module("delegation_executor", "bogus", "hi", home=tmp_path)
    assert proc.returncode == 1
    assert "Unknown service: bogus" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr


def test_quota_validate_config_exits_one_on_non_positive_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--validate-config exits 1 and names a non-positive limit."""
    bad_limits = {
        "requests_per_minute": 0,
        "requests_per_day": 1000,
        "tokens_per_minute": 32000,
        "tokens_per_day": 1000000,
    }
    with (
        patch.object(
            quota_tracker.GeminiQuotaTracker,
            "limits",
            new=bad_limits,
        ),
        patch.object(sys, "argv", ["quota-tracker", "--validate-config"]),
        pytest.raises(SystemExit) as exit_info,
    ):
        quota_tracker.main()
    assert exit_info.value.code == 1
    assert "requests_per_minute" in capsys.readouterr().err


def test_quota_validate_config_passes_for_default_limits(tmp_path: Path) -> None:
    """The shipped default limits validate cleanly."""
    proc = _run_module("quota_tracker", "--validate-config", home=tmp_path)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("token", ["maybe", "yes", "True1", "1"])
def test_usage_logger_rejects_non_boolean_success_token(
    token: str, tmp_path: Path
) -> None:
    """A success token other than true or false is an argument error."""
    proc = _run_module("usage_logger", "--log", "c", "5", token, "1", home=tmp_path)
    assert proc.returncode == 1
    assert "--log: invalid argument" in proc.stderr


@pytest.mark.parametrize("token", ["true", "False", "TRUE"])
def test_usage_logger_accepts_true_false_case_insensitive(
    token: str, tmp_path: Path
) -> None:
    """Lowercase, capitalized and uppercase booleans are accepted."""
    proc = _run_module("usage_logger", "--log", "c", "5", token, "1", home=tmp_path)
    assert proc.returncode == 0, proc.stderr
