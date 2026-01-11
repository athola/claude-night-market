"""Test delegation error paths that were missing test coverage.

Addresses issue #32 - missing tests for error handling in delegation_executor.py
"""

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.delegation_executor import Delegator, ExecutionResult


class TestSmartDelegateNoServices:
    """Test smart_delegate() when no services are available."""

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_raises_when_no_services_available(
        self,
        mock_verify: MagicMock,
    ) -> None:
        """smart_delegate raises RuntimeError when no delegation services configured."""
        # Mock all services as unavailable
        mock_verify.return_value = (False, ["Service not available"])

        delegator = Delegator()

        # Should raise RuntimeError when trying to delegate with no available services
        with pytest.raises(RuntimeError, match="No delegation services available"):
            delegator.smart_delegate("test prompt", files=None, requirements=None)

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_tries_all_services_before_failing(
        self,
        mock_verify: MagicMock,
    ) -> None:
        """smart_delegate checks all services before raising error."""
        # Track which services were checked
        checked_services = []

        def track_verify(service_name: str) -> tuple[bool, list[str]]:
            checked_services.append(service_name)
            return False, [f"{service_name} not available"]

        mock_verify.side_effect = track_verify

        delegator = Delegator()

        with pytest.raises(RuntimeError):
            delegator.smart_delegate("test prompt")

        # Should have checked both gemini and qwen
        assert "gemini" in checked_services
        assert "qwen" in checked_services

    @patch.object(Delegator, "verify_service")
    @patch.object(Delegator, "execute")
    def test_smart_delegate_uses_first_available_service(
        self,
        mock_execute: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """smart_delegate uses first available service."""

        # Make gemini unavailable but qwen available
        def selective_verify(service_name: str) -> tuple[bool, list[str]]:
            if service_name == "gemini":
                return False, ["gemini not available"]
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

        # Should use qwen since gemini is unavailable
        assert service == "qwen"
        assert result.success


class TestTimeoutHandling:
    """Test timeout handling in delegation execution."""

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_delegation_timeout_returns_timeout_result(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Delegation properly handles and reports timeout errors."""
        # Simulate timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gemini", timeout=1)

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt", timeout=1)

        # Should return ExecutionResult indicating timeout
        assert not result.success
        assert result.exit_code == 124  # Standard timeout exit code
        assert "timed out" in result.stderr.lower()
        assert result.service == "gemini"

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_timeout_duration_is_measured(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Timeout duration is properly measured even when command times out."""

        def simulate_timeout(*_args: tuple, **_kwargs: dict) -> None:
            time.sleep(0.1)  # Simulate some execution time
            raise subprocess.TimeoutExpired(cmd="gemini", timeout=1)

        mock_run.side_effect = simulate_timeout

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt", timeout=1)

        # Duration should be measured despite timeout
        assert result.duration >= 0.1
        assert not result.success

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_timeout_boundary_handling(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Timeout is properly enforced at boundary conditions."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="gemini",
            timeout=0.001,
        )

        delegator = Delegator()

        # Very short timeout should still be handled
        result = delegator.execute("gemini", "test prompt", timeout=1)
        assert not result.success
        assert "timed out" in result.stderr.lower()


class TestMalformedConfigHandling:
    """Test graceful handling of malformed configuration."""

    def test_malformed_json_config_does_not_crash(self, tmp_path: Path) -> None:
        """Malformed JSON config is handled gracefully without crashing."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        # Write malformed JSON
        config_file.write_text("{invalid json content")

        # Should not raise exception during initialization
        delegator = Delegator(config_dir=config_dir)

        # Should still have default services available
        assert "gemini" in delegator.SERVICES
        assert "qwen" in delegator.SERVICES

    def test_config_with_missing_required_fields(self, tmp_path: Path) -> None:
        """Config with missing required fields is handled gracefully."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        # Write config with missing required fields
        config_file.write_text(
            json.dumps(
                {
                    "services": {
                        "custom": {
                            "name": "custom",
                            # Missing: command, auth_method
                        },
                    },
                },
            ),
        )

        # Should handle missing fields without crashing
        delegator = Delegator(config_dir=config_dir)

        # Default services should still be available
        assert "gemini" in delegator.SERVICES
        assert "qwen" in delegator.SERVICES

    def test_empty_config_file(self, tmp_path: Path) -> None:
        """Empty config file is handled gracefully."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text("{}")

        # Should initialize successfully with empty config
        delegator = Delegator(config_dir=config_dir)
        assert "gemini" in delegator.SERVICES
        assert "qwen" in delegator.SERVICES

    def test_config_with_invalid_service_structure(self, tmp_path: Path) -> None:
        """Config with invalid service structure doesn't break initialization."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        # Write config with invalid structure (services is a list instead of dict)
        config_file.write_text(json.dumps({"services": ["invalid", "structure"]}))

        # Should handle invalid structure gracefully
        delegator = Delegator(config_dir=config_dir)
        assert "gemini" in delegator.SERVICES


class TestConfigValidation:
    """Test configuration validation and error reporting."""

    def test_corrupted_usage_log_is_skipped(self, tmp_path: Path) -> None:
        """Corrupted usage log entries are skipped without crashing."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)
        usage_log = config_dir / "usage.jsonl"

        # Write mix of valid and invalid JSONL entries
        usage_log.write_text(
            "{invalid json}\n"
            + json.dumps(
                {
                    "timestamp": "2026-01-09T00:00:00",
                    "service": "gemini",
                    "success": True,
                    "duration": 1.0,
                    "tokens_used": 100,
                },
            )
            + "\n"
            + "{more invalid json}\n",
        )

        delegator = Delegator(config_dir=config_dir)
        summary = delegator.get_usage_summary(days=7)

        # Should have processed the valid entry
        assert summary["total_requests"] == 1
        assert "gemini" in summary["services"]

    def test_missing_config_directory_is_created(self, tmp_path: Path) -> None:
        """Missing config directory is created automatically."""
        config_dir = tmp_path / "nonexistent" / "delegation"

        # Directory doesn't exist yet
        assert not config_dir.exists()

        # Should create directory during initialization
        delegator = Delegator(config_dir=config_dir)
        assert config_dir.exists()
        assert delegator.config_dir == config_dir


class TestGeneralErrorHandling:
    """Test general error handling in delegation."""

    @patch("scripts.delegation_executor.subprocess.run")
    @patch.object(Delegator, "log_usage")
    def test_unexpected_exception_during_execution(
        self,
        _mock_log: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Unexpected exceptions during execution are caught and reported."""
        # Simulate unexpected exception
        mock_run.side_effect = RuntimeError("Unexpected error")

        delegator = Delegator()
        result = delegator.execute("gemini", "test prompt")

        # Should return ExecutionResult with error
        assert not result.success
        assert "Unexpected error" in result.stderr
        assert result.exit_code == 1

    def test_usage_log_write_failure_is_handled(self, tmp_path: Path) -> None:
        """Failure to write usage log doesn't crash execution."""
        config_dir = tmp_path / "delegation"
        config_dir.mkdir(parents=True)

        # Make usage log unwritable
        usage_log = config_dir / "usage.jsonl"
        usage_log.write_text("")
        usage_log.chmod(0o444)  # Read-only

        delegator = Delegator(config_dir=config_dir)

        # Should not raise exception when trying to log
        with patch("scripts.delegation_executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="result",
                stderr="",
            )

            # Execution should complete despite log write failure
            result = delegator.execute("gemini", "test prompt")
            assert result.success
