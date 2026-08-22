"""Tests for delegation_executor.py following TDD/BDD principles."""

import json
import os
import re
import shlex
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
    _create_parser,
    _missing_required_fields,
    _print_result,
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
    def test_a_deep_path_cannot_push_the_prompt_past_the_ceiling(
        self, temp_config_dir, tmp_path
    ) -> None:
        """A file whose header outgrows its budget is skipped, not inverted.

        Given: enough context to leave a remainder smaller than one deeply
               nested file's own BEGIN/END markers
        When:  that file is inlined
        Then:  the prompt still fits the byte ceiling

        The per-file budget is the remainder minus the two markers, and the
        markers grow with the path. A remainder above the minimum but below
        the marker cost makes that budget negative, and a negative bound on
        a slice counts from the end of the file instead of the start, so the
        tighter the budget the more of the file it admits.
        """
        deep = tmp_path
        for _ in range(12):
            deep = deep / ("d" * 20)
        deep.mkdir(parents=True)
        nested = deep / ("n" * 40 + ".txt")
        nested.write_text("x" * (MAX_INLINE_CONTEXT_BYTES * 2))

        filler = tmp_path / "filler.txt"
        markers = len(f"--- BEGIN FILE: {filler} ---\n\n--- END FILE: {filler} ---")
        # Leave a remainder above _MIN_INLINE_FILE_BYTES but below the
        # nested file's own marker cost.
        filler.write_text("f" * (MAX_INLINE_CONTEXT_BYTES - 600 - markers - 1))

        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            "minimax", "summarize", files=[str(filler), str(nested)]
        )

        prompt = command[-1]
        assert len(prompt.encode("utf-8")) <= MAX_INLINE_CONTEXT_BYTES + 1024

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
        # gemini 0.26.0 documents no temperature flag and exits 1 on one.
        assert "--temperature" not in command
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

    def test_partial_override_keeps_the_rest_of_the_cli_contract(
        self,
        temp_config_dir,
    ) -> None:
        """Given a config that overrides one field of a known service.

        then every field it does not name keeps its default.

        Overriding minimax's quota used to rebuild ServiceConfig from five
        named fields, which reset subcommand to () and prompt_flag to "-p"
        and produced a bare `mmx -p <prompt>` that mmx does not accept.
        """
        config_file = temp_config_dir / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "services": {
                        "minimax": {
                            "quota_limits": {"requests_per_minute": 5},
                        },
                    },
                },
            ),
        )

        delegator = Delegator(config_dir=temp_config_dir)
        minimax = delegator.services["minimax"]

        assert minimax.quota_limits == {"requests_per_minute": 5}
        assert minimax.subcommand == Delegator.SERVICES["minimax"].subcommand
        assert minimax.prompt_flag == Delegator.SERVICES["minimax"].prompt_flag
        assert minimax.command == Delegator.SERVICES["minimax"].command

    def test_override_with_an_unknown_field_raises(
        self,
        temp_config_dir,
    ) -> None:
        """Given a config naming a field ServiceConfig does not have.

        then loading raises rather than ignoring it (CJR-003).
        """
        config_file = temp_config_dir / "config.json"
        config_file.write_text(
            json.dumps({"services": {"minimax": {"promt_flag": "--message"}}}),
        )

        with pytest.raises(TypeError, match="promt_flag"):
            Delegator(config_dir=temp_config_dir)

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
        # Passed but not emitted: gemini rejects --temperature outright, so
        # the contract drops it rather than failing the delegation.
        assert "--temperature" not in command
        assert "0.7" not in command

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

        assert mock_run.call_args.kwargs["env"]["DOWNSTREAM_TOKEN"] == "s3cret"  # noqa: S105 - fixture value, asserts the env is forwarded

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


class TestRegisteredProviders:
    """Each provider's argv is the contract its vendor documents."""

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        ("service", "expected"),
        [
            ("muse", ["muse", "exec", "PROMPT"]),
            ("codex", ["codex", "exec", "PROMPT"]),
            ("opencode", ["opencode", "run", "PROMPT"]),
        ],
        ids=["muse-exec", "codex-exec", "opencode-run"],
    )
    def test_native_clis_take_the_prompt_positionally(
        self, service, expected, temp_config_dir
    ) -> None:
        """``muse exec <prompt>`` has no prompt flag to emit.

        All three vendors document a bare positional argument. Emitting a
        ``-p`` ahead of it would make the prompt look like a flag value and
        the CLI would reject the invocation.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.build_command(service, "PROMPT") == expected

    @pytest.mark.bdd
    def test_glm_reaches_zai_by_environment_not_argv(self, temp_config_dir) -> None:
        """GLM is the stock claude binary pointed at a different base URL.

        Z.ai serves an Anthropic-compatible endpoint, so there is no GLM CLI
        to install. The redirection is environment, which is why it must not
        appear in the command.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        service = delegator.services["glm"]

        assert service.command == "claude"
        assert service.env["ANTHROPIC_BASE_URL"] == "https://api.z.ai/api/anthropic"
        # The documented variable is ANTHROPIC_AUTH_TOKEN. ANTHROPIC_API_KEY
        # is the common wrong guess and yields a 401 against Z.ai.
        assert service.env["ANTHROPIC_AUTH_TOKEN"] == "${ZAI_API_KEY}"  # noqa: S105 - asserts the literal placeholder, not a secret
        assert "z.ai" not in " ".join(delegator.build_command("glm", "PROMPT"))

    @pytest.mark.bdd
    def test_glimmer_keeps_the_prompt_on_stdin(self, temp_config_dir) -> None:
        """A local 30B model is fed inlined context that argv cannot hold."""
        delegator = Delegator(config_dir=temp_config_dir)

        command = delegator.build_command("glimmer", "PROMPT")

        assert command == ["ollama", "run", "muse-glimmer:30b"]
        assert "PROMPT" not in command

    @pytest.mark.bdd
    def test_candidate_order_follows_declared_priority(self, temp_config_dir) -> None:
        """Selection order is data, so it cannot drift from the registry."""
        delegator = Delegator(config_dir=temp_config_dir)

        order = delegator.candidate_order()

        assert order[:3] == ["gemini", "qwen", "minimax"]
        assert set(order) == set(delegator.services)

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_a_newly_registered_provider_is_selectable(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """Registering a service is the only step needed to make it usable.

        This is the regression guard for the three hardcoded lists that used
        to govern selection. A provider added to SERVICES but missing from
        them was either never chosen or raised KeyError on the model lookup.
        """
        mock_execute.return_value = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=1.0
        )
        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["newcomer"] = ServiceConfig(
            name="newcomer",
            command="newcomer-bin",
            auth_method="none",
            priority=1,
            large_context_model="newcomer-xl",
        )
        mock_verify.side_effect = lambda name: (name == "newcomer", [])

        service, _ = delegator.smart_delegate("p", requirements={"large_context": True})

        assert service == "newcomer"
        assert mock_execute.call_args.args[3]["model"] == "newcomer-xl"

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_a_provider_without_model_ids_uses_the_cli_default(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """Declaring no model id must degrade, not raise.

        muse, codex and opencode document no --model flag for their headless
        subcommand, so passing one would be inventing a contract.
        """
        mock_execute.return_value = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=1.0
        )
        delegator = Delegator(config_dir=temp_config_dir)
        mock_verify.side_effect = lambda name: (name == "muse", [])

        service, _ = delegator.smart_delegate("p", requirements={"large_context": True})

        assert service == "muse"
        assert "model" not in mock_execute.call_args.args[3]


class TestFlagSpellingsMatchTheRealClis:
    """Every flag spelling below was probed against the installed binary.

    The ServiceConfig defaults reproduce the Gemini dialect and a provider
    declares only where it differs. Nothing verified that a declared flag
    exists in the CLI it targets, and for four of eight providers it did
    not. `delegation_executor.py <svc> "<prompt>" --format json` is a
    documented invocation, and it reached the CLI as an unknown argument.

    Probe results, 2026-08-22, from the installed versions:

        gemini 0.26.0   --temperature      -> exit 1 Unknown argument
        qwen 0.4.0      --format           -> exit 1 Unknown argument
        qwen 0.4.0      --temperature      -> exit 1 Unknown argument
        mmx 1.0.19      --temperature <n>  -> documented and accepted
        muse 0.2.1      --output-format    -> exit 2 unknown option
        codex-cli 0.77  --output-format    -> exit 2 unexpected argument
        opencode 1.18   --output-format    -> exit 1; --format json parses
        ollama 0.13.1   --output-format    -> exit 1 unknown flag

    These assert on argv rather than spawning anything, so the suite stays
    hermetic. The binaries are the source; this is the pin.
    """

    @pytest.mark.bdd
    def test_qwen_takes_the_default_output_format_spelling(
        self, temp_config_dir
    ) -> None:
        """GIVEN qwen 0.4.0, whose flag is -o/--output-format.

        WHEN a caller asks for JSON
        THEN --output-format is emitted and --format is not

        `qwen --format json` exits 1 with "Unknown argument: format".
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            "qwen", "extract", options={"output_format": "json"}
        )

        assert "--output-format" in command
        assert "--format" not in command
        assert command[command.index("--output-format") + 1] == "json"

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", ["gemini", "qwen"])
    def test_a_cli_without_a_temperature_flag_is_sent_none(
        self, temp_config_dir, service: str
    ) -> None:
        """GIVEN a CLI that documents no temperature flag.

        WHEN a caller passes a temperature
        THEN no temperature token reaches argv

        Both CLIs reject the flag outright, so emitting it turns a tuning
        hint into a failed delegation.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            service, "extract", options={"temperature": 0.5}
        )

        assert "--temperature" not in command
        assert "0.5" not in command

    @pytest.mark.bdd
    def test_minimax_carries_the_temperature_it_supports(self, temp_config_dir) -> None:
        """GIVEN `mmx text chat`, which documents --temperature <n>.

        WHEN a caller passes a temperature
        THEN it is emitted rather than dropped

        The registry declared None here, so the one provider in the fleet
        that accepts a temperature was the one silently denied it.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            "minimax", "extract", options={"temperature": 0.2}
        )

        assert "--temperature" in command
        assert command[command.index("--temperature") + 1] == "0.2"

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", ["opencode", "glimmer"])
    def test_a_cli_spelling_it_format_gets_format(
        self, temp_config_dir, service: str
    ) -> None:
        """GIVEN opencode and ollama, which both spell the flag --format.

        WHEN a caller asks for JSON
        THEN --format is emitted and --output-format is not
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            service, "extract", options={"output_format": "json"}
        )

        assert "--format" in command
        assert "--output-format" not in command
        assert command[command.index("--format") + 1] == "json"

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", ["muse", "codex"])
    def test_a_cli_with_only_a_boolean_json_flag_emits_no_format_token(
        self, temp_config_dir, service: str
    ) -> None:
        """GIVEN a CLI whose only JSON control is a boolean --json.

        WHEN a caller asks for JSON
        THEN no format flag and no format value reach argv

        `--json` takes no value, so the key-and-value shape build_command
        emits cannot express it: `--json json` would land "json" as a
        positional and displace the prompt. Suppressing is the honest
        answer until the contract can carry a valueless flag, tracked in
        issue #684. Emitting --output-format is not the honest answer:
        muse exits 2 on it, and so does codex.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            service, "extract", options={"output_format": "json"}
        )

        assert "--output-format" not in command
        assert "--json" not in command
        assert "json" not in command


def _plugin_root() -> Path:
    """Return the conjure plugin root that holds skills/ and scripts/."""
    return Path(__file__).resolve().parents[2]


_INVOCATION = re.compile(
    r"python\s+(?P<path>\S*delegation_executor\.py)(?P<rest>(?:\\\n|[^\n`])*)"
)

_INSTALL = re.compile(
    r"^\s*(?:[-*]\s*)?`?((?:pip|npm|brew|cargo)\s+install[^`\n]*|curl\s+[^`\n]*install[^`\n]*)`?\s*$",
    re.MULTILINE,
)


def _documented_invocations() -> list[tuple[Path, str, list[str]]]:
    """Collect every `python ... delegation_executor.py ...` line in the docs.

    Returns (file, script path as written, argv after the script path).
    """
    found: list[tuple[Path, str, list[str]]] = []
    for doc in sorted(_plugin_root().rglob("*.md")):
        for match in _INVOCATION.finditer(doc.read_text(encoding="utf-8")):
            rest = match.group("rest").replace("\\\n", " ")
            found.append(
                (
                    doc.relative_to(_plugin_root()),
                    match.group("path"),
                    shlex.split(rest),
                )
            )
    return found


class TestDocumentedInvocationsRunAsWritten:
    """The docs are the interface; a reader pastes them verbatim.

    Nothing checked that a documented command reached a flag the parser
    accepts or a service the registry knows, and for one skill it did
    neither. Probed against the parser on 2026-08-22:

        auto "..." --files src/ --requirement large_context -> exit 2,
            "unrecognized arguments: --requirement large_context"
        verify qwen -> exit 1, unhandled traceback; `verify` parses as
            the service name and `qwen` as the prompt

    The second is the worse failure: argparse accepts it, so the command
    looks like it ran. These parse argv rather than spawning anything,
    so the suite stays hermetic.
    """

    @pytest.mark.bdd
    def test_the_docs_invoke_a_path_that_exists(self) -> None:
        """GIVEN a documented invocation of the shared executor.

        WHEN the reader pastes it from the plugin root
        THEN the script path it names is a file on disk

        `~/conjure/tools/delegation_executor.py` names an install layout
        this plugin has never had.
        """
        invocations = _documented_invocations()
        assert invocations, "extractor found nothing; the regex has drifted"

        missing = [
            (str(doc), path)
            for doc, path, _ in invocations
            if not (_plugin_root() / path).is_file()
        ]

        assert missing == []

    @pytest.mark.bdd
    def test_the_docs_pass_only_flags_the_parser_declares(self) -> None:
        """GIVEN a documented invocation of the shared executor.

        WHEN argparse reads its flags
        THEN none are left over as unrecognized

        `--requirement large_context` exits 2 before any delegation runs.
        """
        rejected = []
        for doc, _, argv in _documented_invocations():
            _, unknown = _create_parser().parse_known_args(argv)
            if unknown:
                rejected.append((str(doc), unknown))

        assert rejected == []

    @pytest.mark.bdd
    def test_the_docs_name_a_service_the_registry_knows(self) -> None:
        """GIVEN a documented invocation that names a positional service.

        WHEN the registry is asked for it
        THEN the name resolves, or is the `auto` sentinel

        `verify qwen` parses cleanly and then dies in `execute`, because
        the real spelling is the `--verify` flag.
        """
        known = set(Delegator().services) | {"auto"}
        unknown_services = []
        for doc, _, argv in _documented_invocations():
            namespace, _ = _create_parser().parse_known_args(argv)
            if namespace.service is not None and namespace.service not in known:
                unknown_services.append((str(doc), namespace.service))

        assert unknown_services == []


class TestDocumentedInstallsMatchProvenance:
    """`VERIFIED_BINARIES` is the provenance record; the docs must agree.

    #655 shipped a service naming a binary an unaffiliated npm package
    publishes, which is why that map exists. A skill that documents a
    different install command than the map records reintroduces the same
    exposure through prose instead of code.
    """

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "skill_dir",
        sorted(p.name for p in (_plugin_root() / "skills").glob("*-delegation")),
    )
    def test_a_provider_skill_documents_its_verified_install(
        self, skill_dir: str
    ) -> None:
        """GIVEN a provider skill that documents how to install its CLI.

        WHEN the command is compared to the provenance record
        THEN it is the command that record names

        qwen documents `pip install qwen-cli`; the verified install is
        `npm install -g @qwen-code/qwen-code` from Alibaba / QwenLM.
        """
        service = skill_dir.removesuffix("-delegation")
        binary = Delegator().services[service].command
        verified = VERIFIED_BINARIES[binary]["install"]

        divergent = []
        for doc in sorted((_plugin_root() / "skills" / skill_dir).rglob("*.md")):
            for match in _INSTALL.finditer(doc.read_text(encoding="utf-8")):
                if match.group(1).strip() != verified:
                    divergent.append((doc.name, match.group(1).strip()))

        assert divergent == []


RESULT_STDOUT_TRUNCATION = 200


def _result(*, success: bool, stdout: str = "", stderr: str = "") -> ExecutionResult:
    """Build an ExecutionResult carrying only what _print_result reads."""
    return ExecutionResult(
        success=success,
        stdout=stdout,
        stderr=stderr,
        exit_code=0 if success else 1,
        duration=0.0,
        tokens_used=0,
    )


class TestPrintResultTruncatesOnlyTheQuietPath:
    """What a caller sees is not what the CLI wrote, and the cut is uneven.

    Dogfooded through the executor on 2026-08-22. `_print_result` cuts a
    successful stdout at 200 characters and prints a failed stderr whole:

        codex "Reply with: pong" -> exit 1, 123571 bytes of stderr, all
            of it printed, 594 lines of unrelated skill-load errors
            ahead of the sentence that names the failure
        glm  "Reply with: pong" -> exit 0, "pong", well under the cut

    Both halves matter and pull opposite ways. A provider that answers
    at length loses the tail of its answer, while a provider that fails
    noisily delivers every byte. Every CLI in the registry puts its
    diagnosis last, which is the half a head-truncation removes.

    These pass an ExecutionResult straight to the printer, so the suite
    stays hermetic while the numbers stay the source.
    """

    @pytest.mark.bdd
    def test_a_long_successful_answer_is_cut_at_two_hundred_characters(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """GIVEN a delegation that succeeded with a long answer.

        WHEN the executor prints the result
        THEN only the first 200 characters of stdout reach the caller

        Documented in shared-shell-execution.md. A provider answering at
        length loses its tail, so a caller needing the whole answer must
        read `ExecutionResult.stdout` rather than the printed line.
        """
        answer = "".join(str(index % 10) for index in range(500))

        _print_result(_result(success=True, stdout=answer))

        printed = capsys.readouterr().out
        assert answer[:RESULT_STDOUT_TRUNCATION] in printed
        assert answer[RESULT_STDOUT_TRUNCATION:] not in printed
        assert answer not in printed

    @pytest.mark.bdd
    def test_a_failed_delegation_prints_every_byte_of_stderr(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """GIVEN a delegation that failed with noisy diagnostics.

        WHEN the executor prints the result
        THEN the whole stderr reaches the caller, tail included

        codex reached 123 KB here for a four-word prompt. The line that
        explains the failure is the last one, so a truncation added for
        tidiness would remove the only useful part.
        """
        noise = "\n".join(f"unrelated warning {index}" for index in range(600))
        diagnosis = "your refresh token was already used"

        _print_result(_result(success=False, stderr=f"{noise}\n{diagnosis}"))

        printed = capsys.readouterr().out
        assert diagnosis in printed
        assert "unrelated warning 0" in printed
        assert "unrelated warning 599" in printed

    @pytest.mark.bdd
    def test_an_empty_successful_stdout_is_reported_as_no_output(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """GIVEN a delegation that exited 0 without writing anything.

        WHEN the executor prints the result
        THEN the caller is told there was no output

        No provider reached this branch on 2026-08-22, and qwen missed
        it by one byte: a rejected credential left `stdout` holding a
        bare newline, which is truthy, so it printed as `Success:` and a
        blank line instead. The branch is guarded because that byte is
        the whole difference between a named absence and a silent one.
        """
        _print_result(_result(success=True, stdout=""))

        assert "No output" in capsys.readouterr().out
