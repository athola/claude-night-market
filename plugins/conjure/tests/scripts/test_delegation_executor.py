"""Tests for delegation_executor.py following TDD/BDD principles."""

import json
import os
import subprocess

# Import the module under test
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import (
    Delegator,
    ExecutionResult,
    ServiceConfig,
    main,
)

# Constants for magic values
DEFAULT_REQUESTS_PER_MINUTE = 60
DEFAULT_TEST_DURATION = 1.5
DEFAULT_TOKENS_USED = 100
MIN_TOKEN_COUNT_THRESHOLD = 50
TIMEOUT_EXIT_CODE = 124
TEST_USAGE_REQUESTS = 2
TEST_SUCCESS_RATE = 50.0
USAGE_DAYS = 30


class TestServiceConfig:
    """Test ServiceConfig dataclass."""

    def test_service_config_creation(self, delegation_service_config) -> None:
        """Given valid service config data when creating ServiceConfig.

        then should instantiate correctly.
        """
        config = ServiceConfig(**delegation_service_config)

        assert config.name == "test_service"
        assert config.command == "test"
        assert config.auth_method == "api_key"
        assert config.auth_env_var == "TEST_API_KEY"
        assert config.quota_limits["requests_per_minute"] == DEFAULT_REQUESTS_PER_MINUTE


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_execution_result_creation(self) -> None:
        """Given execution data when creating ExecutionResult.

        then should store all fields.
        """
        result = ExecutionResult(
            success=True,
            stdout="Test output",
            stderr="",
            exit_code=0,
            duration=DEFAULT_TEST_DURATION,
            tokens_used=DEFAULT_TOKENS_USED,
            service="gemini",
        )

        assert result.success is True
        assert result.stdout == "Test output"
        assert result.duration == DEFAULT_TEST_DURATION
        assert result.tokens_used == DEFAULT_TOKENS_USED
        assert result.service == "gemini"


class TestDelegator:
    """Test Delegator class functionality."""

    def test_delegator_initialization_default_config_dir(self) -> None:
        """Given no config dir when initializing Delegator.

        then should use default path.
        """
        delegator = Delegator()

        expected_path = Path.home() / ".claude" / "hooks" / "delegation"
        assert delegator.config_dir == expected_path
        assert delegator.config_file == expected_path / "config.json"
        assert delegator.usage_log == expected_path / "usage.jsonl"

    def test_delegator_initialization_custom_config_dir(self, temp_config_dir) -> None:
        """Given custom config dir when initializing Delegator.

        then should use provided path.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.config_dir == temp_config_dir
        assert delegator.config_file == temp_config_dir / "config.json"
        assert delegator.usage_log == temp_config_dir / "usage.jsonl"

    def test_load_configurations_with_custom_config(
        self,
        temp_config_dir,
        sample_config_file,
    ) -> None:
        """Given custom config file when loading configurations.

        then should merge with defaults.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        # Check that custom service was added
        assert "custom_service" in delegator.SERVICES
        custom_service = delegator.SERVICES["custom_service"]
        assert custom_service.command == "custom"
        assert custom_service.auth_env_var == "CUSTOM_API_KEY"

    @patch("subprocess.run")
    def test_verify_service_success(self, mock_run, temp_config_dir) -> None:
        """Given available service when verifying then should return success."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "version 1.0.0"

        delegator = Delegator(config_dir=temp_config_dir)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            is_available, issues = delegator.verify_service("gemini")

        assert is_available is True
        assert len(issues) == 0

    @patch("subprocess.run")
    def test_verify_service_command_not_found(self, mock_run, temp_config_dir) -> None:
        """Given missing command when verifying then should return error."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        delegator = Delegator(config_dir=temp_config_dir)
        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any("not found" in issue for issue in issues)

    @patch("subprocess.run")
    def test_verify_service_missing_auth(self, mock_run, temp_config_dir) -> None:
        """Given missing auth env var when verifying then should return error."""
        mock_run.return_value.returncode = 0

        delegator = Delegator(config_dir=temp_config_dir)

        with patch.dict(os.environ, {}, clear=False):
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any("GEMINI_API_KEY" in issue for issue in issues)

    @patch("delegation_executor.tiktoken.get_encoding")
    def test_estimate_tokens_with_encoder(
        self,
        mock_get_encoding,
        sample_files,
        temp_config_dir,
    ) -> None:
        """Given tiktoken available when estimating tokens then should use encoder."""
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = list(range(50))  # 50 tokens
        mock_get_encoding.return_value = mock_encoder

        delegator = Delegator(config_dir=temp_config_dir)

        file_paths = [str(f) for f in sample_files]
        tokens = delegator.estimate_tokens(file_paths, "test prompt")

        # Should count prompt tokens + file tokens + overhead
        assert tokens > MIN_TOKEN_COUNT_THRESHOLD  # More than just the prompt
        mock_get_encoding.assert_called_once_with("cl100k_base")

    @patch("delegation_executor.tiktoken.get_encoding")
    def test_estimate_tokens_without_encoder(
        self,
        mock_get_encoding,
        sample_files,
        temp_config_dir,
    ) -> None:
        """Given no tiktoken when estimating tokens then should use heuristic."""
        mock_get_encoding.side_effect = Exception("tiktoken not available")

        delegator = Delegator(config_dir=temp_config_dir)

        file_paths = [str(f) for f in sample_files]
        tokens = delegator.estimate_tokens(file_paths, "test prompt")

        # Should use heuristic estimation
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_build_command_basic(self, temp_config_dir) -> None:
        """Given basic parameters when building command.

        then should create correct structure.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command("gemini", "test prompt")

        assert command == ["gemini", "-p", "test prompt"]

    def test_build_command_with_options(self, temp_config_dir) -> None:
        """Given options when building command.

        then should include service-specific flags.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        options = {"model": "gemini-pro", "output_format": "json", "temperature": 0.7}

        command = delegator.build_command("gemini", "test prompt", options=options)

        assert "gemini" in command
        assert "--model" in command
        assert "gemini-pro" in command
        assert "--output-format" in command
        assert "json" in command
        assert "--temperature" in command
        assert "0.7" in command

    def test_build_command_with_files(self, sample_files, temp_config_dir) -> None:
        """Given files when building command then should include file references."""
        delegator = Delegator(config_dir=temp_config_dir)

        file_paths = [str(f) for f in sample_files]
        command = delegator.build_command("gemini", "test prompt", files=file_paths)

        # Check that files are referenced in command
        command_str = " ".join(command)
        for file_path in file_paths:
            assert f"@{file_path}" in command_str

    @patch("subprocess.run")
    @patch("delegation_executor.Delegator.estimate_tokens")
    def test_execute_success(self, mock_estimate, mock_run, temp_config_dir) -> None:
        """Given successful command when executing
        then should return positive result.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success output"
        mock_run.return_value.stderr = ""
        mock_estimate.return_value = 100

        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.execute("gemini", "test prompt")

        assert result.success is True
        assert result.stdout == "Success output"
        assert result.exit_code == 0
        assert result.service == "gemini"
        assert result.tokens_used == DEFAULT_TOKENS_USED

    @patch("subprocess.run")
    @patch("delegation_executor.Delegator.estimate_tokens")
    def test_execute_failure(self, mock_estimate, mock_run, temp_config_dir) -> None:
        """Given failed command when executing then should return negative result."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Error message"
        mock_estimate.return_value = 50

        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.execute("gemini", "test prompt")

        assert result.success is False
        assert result.stderr == "Error message"
        assert result.exit_code == 1
        assert result.service == "gemini"

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run, temp_config_dir) -> None:
        """Given command timeout when executing then should return timeout result."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.execute("gemini", "test prompt", timeout=300)

        assert result.success is False
        assert "timed out" in result.stderr.lower()
        assert result.exit_code == TIMEOUT_EXIT_CODE

    @patch("subprocess.run")
    @patch("delegation_executor.Delegator.estimate_tokens")
    @patch("builtins.open", new_callable=mock_open)
    def test_log_usage(
        self, mock_file, mock_estimate, mock_run, temp_config_dir
    ) -> None:
        """Given execution result when logging usage then should write to log file."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        mock_estimate.return_value = 100

        delegator = Delegator(config_dir=temp_config_dir)

        delegator.execute("gemini", "test prompt")

        # Verify log file was opened and written to
        mock_file.assert_called_with(delegator.usage_log, "a")
        handle = mock_file()
        written_data = handle.write.call_args[0][0]

        # Parse and verify log entry
        log_entry = json.loads(written_data.strip())
        assert log_entry["service"] == "gemini"
        assert log_entry["success"] is True
        assert "timestamp" in log_entry
        assert "duration" in log_entry

    def test_get_usage_summary_no_log(self, temp_config_dir) -> None:
        """Given no usage log when getting summary then should return empty stats."""
        delegator = Delegator(config_dir=temp_config_dir)

        summary = delegator.get_usage_summary()

        assert summary["total_requests"] == 0
        assert summary["success_rate"] == 0
        assert len(summary["services"]) == 0

    def test_get_usage_summary_with_log(
        self, sample_usage_log, temp_config_dir
    ) -> None:
        """Given usage log when getting summary then should calculate correct stats."""
        delegator = Delegator(config_dir=temp_config_dir)

        summary = delegator.get_usage_summary(days=USAGE_DAYS)

        assert summary["total_requests"] == TEST_USAGE_REQUESTS
        assert summary["success_rate"] == TEST_SUCCESS_RATE  # 1 success out of 2
        assert "gemini" in summary["services"]
        assert "qwen" in summary["services"]

        gemini_stats = summary["services"]["gemini"]
        assert gemini_stats["requests"] == 1
        assert gemini_stats["successful"] == 1
        assert gemini_stats["tokens_used"] == 100

    @patch("delegation_executor.Delegator.verify_service")
    @patch("delegation_executor.Delegator.execute")
    def test_smart_delegate_gemini_available(
        self,
        mock_execute,
        mock_verify,
        temp_config_dir,
    ) -> None:
        """Given gemini available when smart delegating then should select gemini."""
        mock_verify.return_value = (True, [])
        mock_execute.return_value = ExecutionResult(
            success=True,
            stdout="",
            stderr="",
            exit_code=0,
            duration=1.0,
        )

        delegator = Delegator(config_dir=temp_config_dir)

        service, _result = delegator.smart_delegate("test prompt")

        assert service == "gemini"
        mock_execute.assert_called_once()

    @patch("delegation_executor.Delegator.verify_service")
    def test_smart_delegate_no_services(self, mock_verify, temp_config_dir) -> None:
        """Given no services available when smart delegating then should raise error."""
        mock_verify.return_value = (False, ["Service not available"])

        delegator = Delegator(config_dir=temp_config_dir)

        with pytest.raises(RuntimeError, match="No delegation services available"):
            delegator.smart_delegate("test prompt")


class TestDelegatorCli:
    """Test CLI functionality of delegation executor."""

    @patch("delegation_executor.Delegator")
    @patch("sys.argv", ["delegation_executor.py", "--list-services"])
    def test_cli_list_services(self, mock_delegator_class) -> None:
        """Given --list-services flag when running CLI then should list services."""
        mock_delegator = MagicMock()
        mock_delegator.SERVICES = {
            "gemini": ServiceConfig("gemini", "gemini", "api_key"),
            "qwen": ServiceConfig("qwen", "qwen", "cli"),
        }
        mock_delegator_class.return_value = mock_delegator

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("Available services:")

    @patch("delegation_executor.Delegator")
    @patch("sys.argv", ["delegation_executor.py", "--usage"])
    def test_cli_show_usage(self, mock_delegator_class) -> None:
        """Given --usage flag when running CLI then should show usage summary."""
        mock_delegator = MagicMock()
        mock_delegator.get_usage_summary.return_value = {
            "total_requests": 10,
            "success_rate": 80.0,
            "services": {},
        }
        mock_delegator_class.return_value = mock_delegator

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("Delegation Usage Summary")

    @patch("delegation_executor.Delegator")
    @patch("sys.argv", ["delegation_executor.py", "--verify", "gemini"])
    def test_cli_verify_service(self, mock_delegator_class) -> None:
        """Given --verify flag when running CLI then should verify service."""
        mock_delegator = MagicMock()
        mock_delegator.verify_service.return_value = (True, [])
        mock_delegator_class.return_value = mock_delegator

        with patch("builtins.print"):
            main()

        mock_delegator.verify_service.assert_called_once_with("gemini")

    @patch("delegation_executor.Delegator")
    @patch("sys.argv", ["delegation_executor.py", "gemini", "test prompt"])
    def test_cli_execute_delegation(self, mock_delegator_class) -> None:
        """Given service and prompt when running CLI then should execute delegation."""
        mock_delegator = MagicMock()
        mock_result = ExecutionResult(
            success=True,
            stdout="Test output",
            stderr="",
            exit_code=0,
            duration=1.0,
            service="gemini",
        )
        mock_delegator.execute.return_value = mock_result
        mock_delegator_class.return_value = mock_delegator

        with patch("builtins.print"):
            main()

        mock_delegator.execute.assert_called_once_with(
            "gemini",
            "test prompt",
            None,
            {},
            300,
        )


# Import os for environment variable mocking
