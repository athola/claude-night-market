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
    MAX_INLINE_CONTEXT_BYTES,
    VERIFIED_BINARIES,
    Delegator,
    ExecutionResult,
    ServiceConfig,
    _missing_required_fields,
    estimate_tokens,
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

    @pytest.mark.bdd
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

    @pytest.mark.bdd
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

    @pytest.mark.bdd
    def test_delegator_initialization_default_config_dir(self) -> None:
        """Given no config dir when initializing Delegator.

        then should use default path.
        """
        delegator = Delegator()

        expected_path = Path.home() / ".claude" / "hooks" / "delegation"
        assert delegator.config_dir == expected_path
        assert delegator.config_file == expected_path / "config.json"
        assert delegator.usage_log == expected_path / "usage.jsonl"

    @pytest.mark.bdd
    def test_delegator_initialization_custom_config_dir(self, temp_config_dir) -> None:
        """Given custom config dir when initializing Delegator.

        then should use provided path.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.config_dir == temp_config_dir
        assert delegator.config_file == temp_config_dir / "config.json"
        assert delegator.usage_log == temp_config_dir / "usage.jsonl"

    @pytest.mark.bdd
    def test_delegator_registers_minimax_service(self, temp_config_dir) -> None:
        """Given default config when initializing Delegator.

        then MiniMax is registered against the official ``mmx`` binary.

        The official MiniMax CLI is published as npm ``mmx-cli`` and installs
        a binary named ``mmx``. A service named ``minimax`` would resolve to
        an unaffiliated third-party package of that name.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        assert "minimax" in delegator.services
        minimax = delegator.services["minimax"]
        assert minimax.command == "mmx"
        assert minimax.quota_limits is not None

    @pytest.mark.bdd
    def test_minimax_authenticates_through_the_cli(self, temp_config_dir) -> None:
        """Given the MiniMax service when inspecting its auth method.

        then it verifies through ``mmx auth status`` rather than an env var.

        ``mmx`` stores OAuth or API-key credentials in ``~/.mmx/config.json``
        and reads no ``MINIMAX_API_KEY``. Checking an env var would report a
        logged-in user as unauthenticated and vice versa.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        minimax = delegator.services["minimax"]

        assert minimax.auth_method == "cli"
        assert minimax.auth_env_var is None

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_verify_minimax_runs_mmx_auth_status(
        self, mock_run, temp_config_dir
    ) -> None:
        """Given an unauthenticated CLI when verifying MiniMax then report it."""
        mock_run.return_value.returncode = 1

        delegator = Delegator(config_dir=temp_config_dir)
        is_available, issues = delegator.verify_service("minimax")

        auth_calls = [
            call.args[0]
            for call in mock_run.call_args_list
            if call.args and call.args[0][:1] == ["mmx"] and "auth" in call.args[0]
        ]
        assert ["mmx", "auth", "status"] in auth_calls
        assert is_available is False
        assert any("not authenticated" in issue for issue in issues)

    @pytest.mark.bdd
    def test_build_minimax_command_matches_mmx_contract(self, temp_config_dir) -> None:
        """Given a model option when building the MiniMax command.

        then the argv matches ``mmx text chat --model M --message P``.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command(
            "minimax",
            "summarize this",
            options={"model": "MiniMax-M3"},
        )

        assert command == [
            "mmx",
            "text",
            "chat",
            "--model",
            "MiniMax-M3",
            "--message",
            "summarize this",
        ]

    @pytest.mark.bdd
    def test_build_minimax_command_uses_output_flag(self, temp_config_dir) -> None:
        """MiniMax takes ``--output``, not Gemini's ``--output-format``."""
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command(
            "minimax",
            "extract",
            options={"output_format": "json"},
        )

        assert "--output" in command
        assert "--output-format" not in command
        assert command[command.index("--output") + 1] == "json"

    @pytest.mark.bdd
    def test_build_minimax_command_drops_unsupported_temperature(
        self, temp_config_dir
    ) -> None:
        """``mmx text chat`` documents no temperature flag, so none is emitted."""
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command(
            "minimax",
            "extract",
            options={"temperature": 0.2},
        )

        assert "--temperature" not in command

    @pytest.mark.bdd
    def test_build_minimax_command_inlines_file_contents(
        self, temp_config_dir, tmp_path
    ) -> None:
        """Given files when building a MiniMax command then inline them.

        ``mmx`` has no ``@path`` context syntax, so a bare reference would
        reach the model as literal text with the file contents missing.
        """
        target = tmp_path / "sample.py"
        target.write_text("def marker_function():\n    return 42\n")

        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            "minimax",
            "summarize",
            files=[str(target)],
        )

        prompt = command[-1]
        assert "marker_function" in prompt
        assert f"@{target}" not in prompt
        assert "summarize" in prompt

    @pytest.mark.bdd
    def test_build_minimax_command_truncates_oversized_inline_context(
        self, temp_config_dir, tmp_path
    ) -> None:
        """Inlined context stays under the single-argument limit of execve."""
        target = tmp_path / "big.txt"
        target.write_text("x" * (MAX_INLINE_CONTEXT_BYTES * 2))

        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command("minimax", "summarize", files=[str(target)])

        prompt = command[-1]
        assert len(prompt.encode("utf-8")) <= MAX_INLINE_CONTEXT_BYTES + 1024
        assert "truncated" in prompt.lower()
        # A file too large for the budget is carried in part, not dropped: a
        # prompt with no context at all would delegate nothing and report
        # success.
        assert "x" * 1000 in prompt

    @pytest.mark.bdd
    def test_oversized_file_does_not_starve_the_prompt(
        self, temp_config_dir, tmp_path
    ) -> None:
        """A single file larger than the budget still contributes context."""
        target = tmp_path / "huge.txt"
        target.write_text("y" * (MAX_INLINE_CONTEXT_BYTES * 3))

        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command("minimax", "summarize", files=[str(target)])

        prompt = command[-1]
        assert prompt.count("y") > MAX_INLINE_CONTEXT_BYTES // 2
        assert "summarize" in prompt

    @pytest.mark.bdd
    def test_build_gemini_command_still_uses_at_references(
        self, temp_config_dir, tmp_path
    ) -> None:
        """Regression guard: the Gemini/Qwen ``@path`` contract is unchanged."""
        target = tmp_path / "sample.py"
        target.write_text("print('hi')\n")

        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            "gemini",
            "summarize",
            files=[str(target)],
            options={"output_format": "json", "temperature": 0.5},
        )

        assert command[0] == "gemini"
        assert "--output-format" in command
        assert "--temperature" in command
        assert command[-2] == "-p"
        assert f"@{target}" in command[-1]

    def test_load_configurations_with_custom_config(
        self,
        temp_config_dir,
    ) -> None:
        """Given custom config file when loading configurations.

        then should merge with defaults.
        """
        config_file = temp_config_dir / "config.json"
        custom_config = {
            "services": {
                "custom_service": {
                    "name": "custom_service",
                    "command": "custom",
                    "auth_method": "api_key",
                    "auth_env_var": "CUSTOM_API_KEY",
                    "quota_limits": {
                        "requests_per_minute": 30,
                        "requests_per_day": 500,
                        "tokens_per_day": 500000,
                    },
                },
            },
        }
        config_file.write_text(json.dumps(custom_config))

        delegator = Delegator(config_dir=temp_config_dir)

        # Check that custom service was added
        assert "custom_service" in delegator.services
        custom_service = delegator.services["custom_service"]
        assert custom_service.command == "custom"
        assert custom_service.auth_env_var == "CUSTOM_API_KEY"

    @pytest.mark.bdd
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

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_verify_service_command_not_found(self, mock_run, temp_config_dir) -> None:
        """Given missing command when verifying then should return error."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        delegator = Delegator(config_dir=temp_config_dir)
        is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any("not found" in issue for issue in issues)

    @pytest.mark.bdd
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

    def test_estimate_tokens_with_files(
        self,
        sample_files,
    ) -> None:
        """Given files when estimating tokens then should count chars/4 heuristic."""
        file_paths = [str(f) for f in sample_files]
        tokens = estimate_tokens(file_paths, "test prompt")

        # Should count prompt tokens + file content tokens via heuristic
        assert isinstance(tokens, int)
        assert tokens > 0
        # Tokens from files should exceed prompt-only estimate
        prompt_only = estimate_tokens([], "test prompt")
        assert tokens > prompt_only

    def test_estimate_tokens_prompt_only(self) -> None:
        """Given prompt only when estimating tokens then should use heuristic."""
        tokens = estimate_tokens([], "test prompt with some words here")

        # Should use heuristic estimation (len // 4)
        assert isinstance(tokens, int)
        assert tokens > 0

    @pytest.mark.bdd
    def test_build_command_basic(self, temp_config_dir) -> None:
        """Given basic parameters when building command.

        then should create correct structure.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command("gemini", "test prompt")

        assert command == ["gemini", "-p", "test prompt"]

    @pytest.mark.bdd
    def test_build_command_with_options(self, temp_config_dir) -> None:
        """Given options when building command.

        then should include service-specific flags.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        options = {"model": "gemini-3-pro", "output_format": "json", "temperature": 0.7}

        command = delegator.build_command("gemini", "test prompt", options=options)

        assert "gemini" in command
        assert "--model" in command
        assert "gemini-3-pro" in command
        assert "--output-format" in command
        assert "json" in command
        assert "--temperature" in command
        assert "0.7" in command

    @pytest.mark.bdd
    def test_build_command_with_files(self, sample_files, temp_config_dir) -> None:
        """Given files when building command then should include file references."""
        delegator = Delegator(config_dir=temp_config_dir)

        file_paths = [str(f) for f in sample_files]
        command = delegator.build_command("gemini", "test prompt", files=file_paths)

        # Check that files are referenced in command
        command_str = " ".join(command)
        for file_path in file_paths:
            assert f"@{file_path}" in command_str

    @pytest.mark.bdd
    @patch("subprocess.run")
    @patch("delegation_executor.estimate_tokens")
    def test_execute_success(self, mock_estimate, mock_run, temp_config_dir) -> None:
        """Given successful command when executing.

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

    @pytest.mark.bdd
    @patch("subprocess.run")
    @patch("delegation_executor.estimate_tokens")
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

    @pytest.mark.bdd
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
    @patch("delegation_executor.estimate_tokens")
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

    @pytest.mark.bdd
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

    @pytest.mark.bdd
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
        mock_delegator.services = {
            "gemini": ServiceConfig("gemini", "gemini", "api_key"),
            "qwen": ServiceConfig("qwen", "qwen", "cli"),
        }
        mock_delegator_class.return_value = mock_delegator

        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_any_call("  gemini: gemini (auth: api_key)")

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

        mock_print.assert_any_call("Total requests: 10")

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

    @pytest.mark.bdd
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


class TestProviderContractMechanics:
    """The provider contract is data, so each axis is independently testable."""

    @pytest.mark.bdd
    def test_optional_fields_with_factories_are_not_required(self) -> None:
        """A field with a default_factory must not read as required.

        ``_missing_required_fields`` decides whether a custom config entry is
        incomplete. Treating a defaulted field as required would silently skip
        valid user configs.
        """
        assert (
            _missing_required_fields(
                {"name": "x", "command": "x", "auth_method": "cli"}
            )
            == set()
        )

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_env_overlay_reaches_the_child_process(
        self, mock_run, temp_config_dir
    ) -> None:
        """A service env overlay is applied to the child, not the parent.

        Endpoint-swap harnesses run a stock binary against a different base
        URL. The overlay is how that is expressed without mutating the
        delegating process's own environment.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ok"
        mock_run.return_value.stderr = ""

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            env={"PROBE_BASE_URL": "https://example.invalid"},
        )

        delegator.execute("probe", "hello")

        passed_env = mock_run.call_args.kwargs["env"]
        assert passed_env["PROBE_BASE_URL"] == "https://example.invalid"
        assert "PATH" in passed_env, (
            "overlay must extend the environment, not replace it"
        )
        assert "PROBE_BASE_URL" not in os.environ

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_env_overlay_expands_references_to_real_variables(
        self, mock_run, temp_config_dir
    ) -> None:
        """``${VAR}`` in an overlay resolves from the caller's environment.

        Credentials must not be written into config files, so an overlay
        names the variable that holds the secret instead of the secret.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ok"
        mock_run.return_value.stderr = ""

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            env={"DOWNSTREAM_TOKEN": "${PROBE_SECRET}"},
        )

        with patch.dict(os.environ, {"PROBE_SECRET": "s3cret"}):
            delegator.execute("probe", "hello")

        assert mock_run.call_args.kwargs["env"]["DOWNSTREAM_TOKEN"] == "s3cret"

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_missing_overlay_variable_fails_verification(
        self, mock_run, temp_config_dir
    ) -> None:
        """An overlay referencing an unset variable is reported, not guessed."""
        mock_run.return_value.returncode = 0

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            env={"DOWNSTREAM_TOKEN": "${PROBE_SECRET_ABSENT}"},
        )

        is_available, issues = delegator.verify_service("probe")

        assert is_available is False
        assert any("PROBE_SECRET_ABSENT" in issue for issue in issues)

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_stdin_delivery_keeps_the_prompt_out_of_argv(
        self, mock_run, temp_config_dir
    ) -> None:
        """A stdin-delivering service sends the prompt on stdin.

        argv entries are capped at 128 KiB by execve, so a large inlined
        context has to travel on stdin rather than as an argument.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ok"
        mock_run.return_value.stderr = ""

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            stdin_prompt=True,
        )

        command = delegator.build_command("probe", "secret prompt text")
        assert "secret prompt text" not in command

        delegator.execute("probe", "secret prompt text")
        assert mock_run.call_args.kwargs["input"] == "secret prompt text"

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_version_probe_is_part_of_the_contract(
        self, mock_run, temp_config_dir
    ) -> None:
        """Not every CLI answers ``--version``; the probe is configurable."""
        mock_run.return_value.returncode = 0

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            version_probe=("--help",),
        )

        delegator.verify_service("probe")

        assert ["probe-bin", "--help"] in [
            call.args[0] for call in mock_run.call_args_list if call.args
        ]

    @pytest.mark.bdd
    @patch("subprocess.run")
    def test_missing_binary_reports_the_install_command(
        self, mock_run, temp_config_dir
    ) -> None:
        """A missing CLI names its install command instead of stranding the user."""
        mock_run.side_effect = FileNotFoundError("probe-bin")

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["probe"] = ServiceConfig(
            name="probe",
            command="probe-bin",
            auth_method="none",
            install_hint="npm install -g probe-cli",
        )

        _, issues = delegator.verify_service("probe")

        assert any("npm install -g probe-cli" in issue for issue in issues)


class TestBinaryProvenance:
    """Every binary we spawn is one whose publisher we checked."""

    @pytest.mark.bdd
    def test_every_registered_binary_has_declared_provenance(self) -> None:
        """A binary name is a dependency: spawning it by name trusts PATH.

        #655 shipped a service that spawned ``minimax``, a name owned by an
        unaffiliated npm package. This test makes that class of mistake fail
        in CI rather than in a user's shell.
        """
        for name, config in Delegator.SERVICES.items():
            assert config.command in VERIFIED_BINARIES, (
                f"service {name!r} spawns {config.command!r}, which has no entry "
                f"in VERIFIED_BINARIES. Add the official package and source URL."
            )

    @pytest.mark.bdd
    def test_provenance_entries_cite_a_source(self) -> None:
        """Each provenance record names a package and a URL to check it."""
        for binary, record in VERIFIED_BINARIES.items():
            assert record.get("package"), f"{binary} has no package name"
            assert record.get("source", "").startswith("https://"), (
                f"{binary} has no verifiable source URL"
            )
