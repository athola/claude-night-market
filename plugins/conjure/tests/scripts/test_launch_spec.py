"""PLR0913 regression tests for LaunchSpec in delegation_executor.py.

The PLR0913 refactor replaced six individual arguments to
_launch_process() with a single frozen LaunchSpec dataclass.
These tests assert that _launch_process() correctly unpacks
each field from the spec and that ExecutionResult reflects them.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import Delegator, LaunchSpec


@pytest.fixture()
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary delegation config directory."""
    config_dir = tmp_path / "delegation"
    config_dir.mkdir(parents=True)
    return config_dir


class TestLaunchSpec:
    """Feature: LaunchSpec drives _launch_process() field unpacking.

    As a delegation service maintainer
    I want _launch_process() to unpack all fields from a LaunchSpec
    So that ExecutionResult accurately reflects the spec's service and timeout.
    """

    @patch("delegation_executor.subprocess.run")
    @patch("delegation_executor.estimate_tokens", return_value=42)
    def test_launch_process_uses_spec_service_name(
        self,
        mock_estimate: MagicMock,
        mock_run: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Scenario: _launch_process() sets result.service from spec.service_name.

        Given a LaunchSpec with service_name="gemini"
        When _launch_process() is called with that spec
        Then the returned ExecutionResult.service equals "gemini".
        And ExecutionResult.success reflects the subprocess return code.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "delegated output"
        mock_run.return_value.stderr = ""

        delegator = Delegator(config_dir=temp_config_dir)
        spec = LaunchSpec(
            cmd=["gemini", "--prompt", "hello"],
            service_name="gemini",
            prompt="hello",
            files=None,
            timeout=60,
            start_time=time.time(),
        )

        result = delegator._launch_process(spec)

        assert result.service == "gemini"
        assert result.success is True
        assert result.stdout == "delegated output"
        assert result.tokens_used == 42

    @patch("delegation_executor.subprocess.run")
    def test_launch_process_timeout_uses_spec_timeout(
        self,
        mock_run: MagicMock,
        temp_config_dir: Path,
    ) -> None:
        """Scenario: TimeoutExpired produces exit_code=124 and stderr with duration.

        Given a LaunchSpec with timeout=60
        When the subprocess raises TimeoutExpired
        Then the returned ExecutionResult reports exit_code=124.
        And stderr contains the timeout duration from spec.timeout.
        """
        mock_run.side_effect = subprocess.TimeoutExpired("gemini", 60)

        delegator = Delegator(config_dir=temp_config_dir)
        spec = LaunchSpec(
            cmd=["gemini", "slow"],
            service_name="gemini",
            prompt="slow task",
            files=None,
            timeout=60,
            start_time=time.time(),
        )

        result = delegator._launch_process(spec)

        assert result.success is False
        assert result.exit_code == 124
        assert "60" in result.stderr
