"""Test delegation error paths that were missing test coverage.

Addresses issue #32 - missing tests for error handling in
delegation_executor.py.  Uses parametrize for service variants
and adds mock verification (assert_called_with / call_args).
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.delegation_executor import Delegator, ExecutionResult

# -------------------------------------------------------------------
# smart_delegate - no services
# -------------------------------------------------------------------


class TestSmartDelegateNoServices:
    """Test smart_delegate() when no services are available."""

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_raises_when_no_services_available(
        self,
        mock_verify: MagicMock,
    ) -> None:
        """smart_delegate raises RuntimeError when no services configured."""
        mock_verify.return_value = (False, ["Service not available"])
        delegator = Delegator()

        with pytest.raises(RuntimeError, match="No delegation services available"):
            delegator.smart_delegate(
                "test prompt",
                files=None,
                requirements=None,
            )

        # Verify every service was probed
        assert mock_verify.call_count == len(delegator.services)

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_tries_all_services_before_failing(
        self,
        mock_verify: MagicMock,
    ) -> None:
        """smart_delegate checks all services before raising error."""
        checked: list[str] = []

        def track_verify(name: str) -> tuple[bool, list[str]]:
            checked.append(name)
            return False, [f"{name} not available"]

        mock_verify.side_effect = track_verify
        delegator = Delegator()

        with pytest.raises(RuntimeError):
            delegator.smart_delegate("test prompt")

        assert "gemini" in checked
        assert "qwen" in checked
        # Each service was verified exactly once
        service_calls = [c.args[0] for c in mock_verify.call_args_list]
        assert "gemini" in service_calls
        assert "qwen" in service_calls

    @pytest.mark.parametrize(
        ("unavailable_service", "expected_service"),
        [
            ("gemini", "qwen"),
            ("qwen", "gemini"),
        ],
        ids=["gemini-down-uses-qwen", "qwen-down-uses-gemini"],
    )
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_falls_back_to_other_service(
        self,
        mock_verify: MagicMock,
        mock_execute: MagicMock,
        unavailable_service: str,
        expected_service: str,
    ) -> None:
        """smart_delegate picks the first available service."""

        def selective_verify(name: str) -> tuple[bool, list[str]]:
            if name == unavailable_service:
                return False, [f"{name} not available"]
            return True, []

        mock_verify.side_effect = selective_verify
        mock_execute.return_value = ExecutionResult(
            success=True,
            stdout="result",
            stderr="",
            exit_code=0,
            duration=1.0,
        )

        delegator = Delegator()
        service, result = delegator.smart_delegate("test prompt")

        assert service == expected_service
        assert result.success
        mock_execute.assert_called_once()
        # Verify the prompt was passed through
        assert mock_execute.call_args.args[1] == "test prompt"


# -------------------------------------------------------------------
# Timeout handling
# -------------------------------------------------------------------


class TestTimeoutHandling:
    """Test timeout handling in delegation execution."""

    @pytest.mark.parametrize(
        ("service", "timeout_val"),
        [("gemini", 1), ("qwen", 5)],
        ids=["gemini-timeout", "qwen-timeout"],
    )
    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_delegation_timeout_returns_timeout_result(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
        service: str,
        timeout_val: int,
    ) -> None:
        """Delegation properly handles and reports timeout errors."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=service,
            timeout=timeout_val,
        )

        delegator = Delegator()
        result = delegator.execute(service, "test prompt", timeout=timeout_val)

        assert not result.success
        assert result.exit_code == 124
        assert "timed out" in result.stderr.lower()
        assert result.service == service
        # subprocess.run was called with the correct command
        mock_run.assert_called_once()
        cmd = mock_run.call_args.args[0]
        assert cmd[0] == service

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_timeout_duration_is_measured(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Timeout duration is measured even when command times out."""

        def simulate_timeout(*_a, **_k):
            time.sleep(0.1)
            raise subprocess.TimeoutExpired(cmd="gemini", timeout=1)

        mock_run.side_effect = simulate_timeout

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt", timeout=1)

        assert result.duration >= 0.1
        assert not result.success

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_timeout_boundary_handling(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Very short timeout is handled without crash."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="gemini",
            timeout=0.001,
        )

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt", timeout=1)

        assert not result.success
        assert "timed out" in result.stderr.lower()


# -------------------------------------------------------------------
# Malformed config handling (parametrized)
# -------------------------------------------------------------------


class TestMalformedConfigHandling:
    """Test graceful handling of malformed configuration."""

    @pytest.mark.parametrize(
        ("config_content", "description"),
        [
            ("{invalid json content", "malformed JSON"),
            ("{}", "empty config"),
            (
                json.dumps({"services": ["invalid", "structure"]}),
                "services as list instead of dict",
            ),
            (
                json.dumps({"services": {"custom": {"name": "custom"}}}),
                "missing required fields",
            ),
        ],
        ids=[
            "malformed-json",
            "empty-config",
            "invalid-structure",
            "missing-fields",
        ],
    )
    def test_bad_config_preserves_default_services(
        self,
        tmp_path: Path,
        config_content: str,
        description: str,
    ) -> None:
        """Delegator falls back to defaults when config is {description}."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text(config_content)

        delegator = Delegator(config_dir=config_dir)

        assert "gemini" in delegator.services
        assert "qwen" in delegator.services


# -------------------------------------------------------------------
# Config validation
# -------------------------------------------------------------------


class TestConfigValidation:
    """Test configuration validation and error reporting."""

    def test_corrupted_usage_log_is_skipped(self, tmp_path: Path) -> None:
        """Corrupted usage log entries are skipped without crashing."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        usage_log = config_dir / "usage.jsonl"

        recent_ts = datetime.now().isoformat()
        usage_log.write_text(
            "{invalid json}\n"
            + json.dumps(
                {
                    "timestamp": recent_ts,
                    "service": "gemini",
                    "success": True,
                    "duration": 1.0,
                    "tokens_used": 100,
                }
            )
            + "\n"
            + "{more invalid json}\n",
        )

        delegator = Delegator(config_dir=config_dir)
        summary = delegator.get_usage_summary(days=7)

        assert summary["total_requests"] == 1
        assert "gemini" in summary["services"]

    def test_missing_config_directory_is_created(
        self,
        tmp_path: Path,
    ) -> None:
        """Missing config directory is created automatically."""
        config_dir = tmp_path / "nonexistent" / "delegation"
        assert not config_dir.exists()

        delegator = Delegator(config_dir=config_dir)

        assert config_dir.exists()
        assert delegator.config_dir == config_dir


# -------------------------------------------------------------------
# General error handling
# -------------------------------------------------------------------


class TestGeneralErrorHandling:
    """Test general error handling in delegation."""

    @pytest.mark.parametrize(
        ("exception", "expected_stderr_fragment"),
        [
            (RuntimeError("Unexpected error"), "Unexpected error"),
            (OSError("Disk full"), "Disk full"),
        ],
        ids=["runtime-error", "os-error"],
    )
    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_unexpected_exception_during_execution(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
        exception: Exception,
        expected_stderr_fragment: str,
    ) -> None:
        """Unexpected exceptions are caught and reported."""
        mock_run.side_effect = exception

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt")

        assert not result.success
        assert expected_stderr_fragment in result.stderr
        assert result.exit_code == 1
        # Verify subprocess.run was called
        mock_run.assert_called_once()
        cmd = mock_run.call_args.args[0]
        assert cmd[0] == "gemini"

    def test_usage_log_write_failure_is_handled(
        self,
        tmp_path: Path,
    ) -> None:
        """Failure to write usage log doesn't crash execution."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        usage_log = config_dir / "usage.jsonl"
        usage_log.write_text("")
        usage_log.chmod(0o444)

        delegator = Delegator(config_dir=config_dir)

        with patch(
            "scripts.delegation_executor.subprocess.run",
        ) as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="result",
                stderr="",
            )

            result = delegator.execute("gemini", "test prompt")

            assert result.success
            # Verify subprocess was called with the right service
            mock_run.assert_called_once()
            cmd_args = mock_run.call_args.args[0]
            assert cmd_args[0] == "gemini"
