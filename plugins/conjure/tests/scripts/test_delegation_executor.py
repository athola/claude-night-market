"""Tests for delegation_executor.py following TDD/BDD principles."""

import json
import os
import re
import shlex
import subprocess

# Import the module under test
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import (
    FALLBACK_DISABLED,
    FALLBACK_EXHAUSTED,
    MAX_INLINE_CONTEXT_BYTES,
    VERIFIED_BINARIES,
    Delegator,
    ExecutionResult,
    ServiceConfig,
    _create_parser,
    _delivered_prompt,
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
        self, mock_run, temp_config_dir, tmp_path
    ) -> None:
        """Given an unauthenticated CLI when verifying MiniMax then report it.

        The credential file is planted because the cheaper checks now run
        first and short-circuit. minimax declares ~/.mmx/config.json, and
        an absent one answers the question without spawning anything,
        which is the point of the reorder. This test is about the probe
        that runs when the file is there, so it puts one there.
        """
        mock_run.return_value.returncode = 1
        credential = tmp_path / "config.json"
        credential.write_text("{}")

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["minimax"] = replace(
            delegator.services["minimax"],
            auth_files=(str(credential),),
        )
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
        """Given missing command when verifying then should return error.

        The key is supplied because verification now answers the cheapest
        question first: an unset GEMINI_API_KEY settles availability
        without spawning anything, so a test about a missing binary has
        to get past the variable to reach the binary.
        """
        mock_run.side_effect = FileNotFoundError("Command not found")

        delegator = Delegator(config_dir=temp_config_dir)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
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
            stdout="gemini answered",
            stderr="",
            exit_code=0,
            duration=1.0,
        )

        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.smart_delegate("test prompt")

        assert result.service == "gemini"
        mock_execute.assert_called_once()

    @pytest.mark.bdd
    @patch("delegation_executor.Delegator.verify_service")
    def test_smart_delegate_no_services(self, mock_verify, temp_config_dir) -> None:
        """Given no services available when smart delegating then should report it.

        This asserted a RuntimeError while delegation was opt-in, when an
        empty chain meant a caller had asked for something the machine
        could not do. Delegation now runs by default, which makes an
        operator with no CLI installed the ordinary case, so the empty
        chain became a returned fallback signal instead of a traceback.
        """
        mock_verify.return_value = (False, ["Service not available"])

        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.smart_delegate("test prompt")

        assert result.success is False
        assert result.fallback_reason == FALLBACK_EXHAUSTED


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
            success=True, stdout="answered", stderr="", exit_code=0, duration=1.0
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

        result = delegator.smart_delegate("p", requirements={"large_context": True})

        assert result.service == "newcomer"
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
            success=True, stdout="answered", stderr="", exit_code=0, duration=1.0
        )
        delegator = Delegator(config_dir=temp_config_dir)
        mock_verify.side_effect = lambda name: (name == "muse", [])

        result = delegator.smart_delegate("p", requirements={"large_context": True})

        assert result.service == "muse"
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


MAX_ARG_STRLEN = 128 * 1024
POSITIONAL_PROMPT_SERVICES = ("muse", "codex", "opencode")


class TestAPromptIsDataAndNeverArgv:
    """A prompt is attacker-shaped input; argv is the place that forgets it.

    Dogfooded on 2026-08-22. Two entry points disagree about a prompt that
    begins with a dash, and only one of them is guarded by argparse:

        CLI:    delegation_executor.py gemini "--usage" -> exit 0, prints
                the usage report, delegates nothing
        Python: Delegator.execute("muse", "--help") -> success=True,
                exit 0, and muse's own help text arrives as the answer

    The CLI path is argparse's to own. The Python path reaches the child's
    parser, and every positional-prompt provider will read a leading dash
    as its own flag. No credential is needed to trigger it and both report
    success, so a caller cannot tell an answer from a help page.

    These build argv rather than spawning, so the suite stays hermetic.
    """

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", POSITIONAL_PROMPT_SERVICES)
    def test_a_positional_provider_separates_a_dash_leading_prompt(
        self,
        service: str,
    ) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a positional-prompt provider builds its argv
        THEN an end-of-options separator precedes the prompt

        Replaces the tripwire this file used to carry, which pinned the
        exposure and said in its own docstring to rewrite it once the
        hole was closed. Probed on 2026-08-22:

            muse exec --provider echo -- "--help" -> `echo: --help`
            muse exec --provider echo    "--help" -> the help page

        The separator is emitted only for a dash-leading prompt, so every
        ordinary invocation keeps the argv it had.
        """
        command = Delegator().build_command(service, "--help")

        assert command[-2:] == ["--", "--help"]

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", POSITIONAL_PROMPT_SERVICES)
    def test_an_ordinary_prompt_gains_no_separator(self, service: str) -> None:
        """GIVEN a prompt that does not begin with a dash.

        WHEN the argv is built
        THEN no separator is added

        The fix is scoped to the shape that needs it. A separator on every
        call would be a change to eight CLI contracts at once, and only
        three of them were probed for it.
        """
        command = Delegator().build_command(service, "Reply with: pong")

        assert "--" not in command
        assert command[-1] == "Reply with: pong"

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        ("service", "long_flag"),
        [("gemini", "--prompt"), ("qwen", "--prompt"), ("minimax", "--message")],
    )
    def test_a_value_flag_provider_attaches_a_dash_leading_prompt(
        self,
        service: str,
        long_flag: str,
    ) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a provider that passes the prompt as a flag value builds argv
        THEN the value is attached to the long flag with an equals sign

        A separator does not help here, and assuming it did is why the
        first version of this documentation called these providers safe.
        Probed on 2026-08-22:

            gemini -p    "--help" -> the help page
            gemini -p -- "--help" -> the help page
            gemini --prompt="--help" -> reached authentication

        `mmx --message=` and `qwen --prompt=` behave the same way.
        """
        command = Delegator().build_command(service, "--help")

        assert f"{long_flag}=--help" in command
        assert "--help" not in command[:-1] or command[-1].startswith(long_flag)

    @pytest.mark.bdd
    def test_a_stdin_provider_is_structurally_immune(self) -> None:
        """GIVEN a prompt that begins with a dash.

        WHEN a stdin-delivering provider builds its argv
        THEN the prompt is absent from argv entirely

        glimmer is the one provider no escaping applies to, because the
        prompt never reaches a parser that reads flags.
        """
        command = Delegator().build_command("glimmer", "--help")

        assert "--help" not in command

    @pytest.mark.bdd
    def test_shell_metacharacters_survive_as_one_literal_argument(self) -> None:
        """GIVEN a prompt carrying command substitution and a semicolon.

        WHEN the argv is built
        THEN the whole prompt is a single unsplit argument

        Verified against the filesystem on 2026-08-22: the substitution
        did not run. This pins argv assembly only. Whether a shell ever
        sees the list is decided at spawn time, and is guarded by
        `test_the_child_is_spawned_without_a_shell` below.
        """
        evil = "$(touch /tmp/pwned); `id`; rm -rf /nothing"

        command = Delegator().build_command("minimax", evil)

        assert command.count(evil) == 1
        assert all(";" not in part for part in command if part != evil)

    @pytest.mark.bdd
    def test_the_child_is_spawned_without_a_shell(self) -> None:
        """GIVEN any delegation.

        WHEN the child process is spawned
        THEN argv is passed as a list and no shell interprets it

        Assembling argv safely is undone by spawning it through a shell,
        and the two live in different functions. Adding `shell=True` to
        `_launch_process` leaves every argv-level assertion green, so
        this reads the spawn call's own arguments.
        """
        captured: dict[str, object] = {}

        def fake_run(cmd: object, **kwargs: object) -> MagicMock:
            captured["cmd"] = cmd
            captured["shell"] = kwargs.get("shell", False)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("delegation_executor.subprocess.run", side_effect=fake_run):
            Delegator().execute("minimax", "$(id); echo hi", timeout=5)

        assert captured["shell"] is False
        assert isinstance(captured["cmd"], list)

    @pytest.mark.bdd
    def test_the_context_ceiling_does_not_bound_the_prompt(self) -> None:
        """GIVEN a prompt larger than the inline-context ceiling.

        WHEN the argv is built
        THEN the prompt is carried whole, uncapped

        MAX_INLINE_CONTEXT_BYTES bounds what file context adds, not what
        the caller passes. Past MAX_ARG_STRLEN the spawn fails E2BIG:
        measured on 2026-08-22, 127 KiB spawned and 128 KiB did not.
        The executor reports that as a named failure rather than
        truncating, which is the behavior worth keeping.
        """
        oversized = "x" * (MAX_INLINE_CONTEXT_BYTES * 2)

        command = Delegator().build_command("minimax", oversized)

        assert oversized in command
        assert len(oversized) > MAX_INLINE_CONTEXT_BYTES


class TestMissingContextIsDroppedWithoutASignal:
    """Truncated context is named; absent context is not.

    Dogfooded on 2026-08-22 against a real filesystem. A file that cannot
    be found contributes nothing and says nothing, at any log level:

        _delivered_prompt(minimax, "ASK", ["/nope.txt"]) -> "ASK"

    An oversized file is the opposite: it arrives cut and labelled
    `[context truncated at 98304 bytes; N file(s) included]`. Both are
    context loss, and only one reaches the caller as a fact. The mixed
    case is the one that bites, because a caller passing several paths
    gets a plausible prompt built from the subset that resolved.
    """

    @pytest.mark.bdd
    def test_an_unresolvable_path_contributes_nothing_and_says_nothing(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN a context file that does not exist.

        WHEN the prompt is assembled for an inlining provider
        THEN the prompt is returned unchanged, with no marker

        Pinning the current behavior so that adding a signal later is a
        deliberate change rather than an accident.
        """
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(service, "ASK", [str(tmp_path / "nope.txt")])

        assert delivered == "ASK"

    @pytest.mark.bdd
    def test_a_resolvable_path_survives_beside_an_unresolvable_one(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN one context file that exists and one that does not.

        WHEN the prompt is assembled
        THEN the good file is inlined and the bad one leaves no trace

        The prompt looks complete. Nothing in it distinguishes "one file
        was requested" from "two were requested and one vanished".
        """
        good = tmp_path / "good.txt"
        good.write_text("KEEPME")
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(
            service,
            "ASK",
            [str(good), str(tmp_path / "nope.txt")],
        )

        assert "KEEPME" in delivered
        assert "nope.txt" not in delivered

    @pytest.mark.bdd
    def test_oversized_context_arrives_cut_and_labelled(
        self,
        tmp_path: Path,
    ) -> None:
        """GIVEN a context file past the inline ceiling.

        WHEN the prompt is assembled
        THEN it is capped and carries a marker naming the ceiling

        The contrast with an unresolvable path is the point: this loss is
        reported, and it stays under MAX_ARG_STRLEN so the spawn survives.
        """
        huge = tmp_path / "huge.txt"
        huge.write_text("A" * (MAX_INLINE_CONTEXT_BYTES * 2))
        service = Delegator().services["minimax"]

        delivered = _delivered_prompt(service, "ASK", [str(huge)])

        assert "truncated" in delivered
        assert str(MAX_INLINE_CONTEXT_BYTES) in delivered
        assert len(delivered) < MAX_ARG_STRLEN


class TestDelegationIsOnUnlessRefused:
    """Delegation runs by default, and every way out of it is explicit.

    The opt-in framing put the burden on the caller to remember an
    external CLI existed. These tests pin the inverted default: a caller
    that says nothing gets delegation, and the two ways to decline it
    both leave a reason a reader can act on.
    """

    @pytest.mark.bdd
    def test_an_operator_who_configured_nothing_gets_delegation(
        self, temp_config_dir
    ) -> None:
        """GIVEN no config file and no environment variable.

        WHEN the delegator reports its policy
        THEN delegation is on

        This is the whole inversion in one assertion. Under the previous
        framing there was no policy to read at all, which is what made
        delegation opt-in: it happened only where a caller spelled it out.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is True
        assert delegator.delegation_off_reason is None

    @pytest.mark.bdd
    def test_a_config_file_can_turn_delegation_off_for_a_machine(
        self, temp_config_dir
    ) -> None:
        """GIVEN a config file declaring ``"enabled": false``.

        WHEN the delegator loads it
        THEN delegation is off and names the config as the source

        The persistent opt-out. Named so a caller reporting the fallback
        can say which of the two switches was thrown.
        """
        (temp_config_dir / "config.json").write_text(json.dumps({"enabled": False}))

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is False
        assert delegator.delegation_off_reason is not None
        assert "config" in delegator.delegation_off_reason

    @pytest.mark.bdd
    def test_a_config_that_cannot_be_parsed_does_not_re_enable_delegation(
        self, temp_config_dir
    ) -> None:
        """GIVEN a config file with a trailing comma after ``"enabled": false``.

        WHEN the delegator loads it
        THEN delegation is off and names the unreadable config

        A switch an operator threw must not be undone by a typo in the
        file that carries it. The parse used to be wrapped whole, so a
        JSONDecodeError left ``_config_disables_delegation`` at its
        initial False and delegation ran: prompts and up to 96 KiB of
        inlined source would ship to an external CLI after the operator
        turned delegation off. The failure was logged at debug, which is
        off in every default configuration, so nothing reached any stream.
        """
        (temp_config_dir / "config.json").write_text('{"enabled": false,}')

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is False
        assert delegator.delegation_off_reason is not None
        assert "config" in delegator.delegation_off_reason

    @pytest.mark.bdd
    def test_an_absent_config_is_not_treated_as_an_unreadable_one(
        self, temp_config_dir
    ) -> None:
        """GIVEN no config file at all.

        WHEN the delegator loads its policy
        THEN delegation is on

        The counterpart to the test above, and the reason failing closed
        on a parse error is safe. Never having written a config is not
        the same event as writing one that cannot be read, so the two
        must not collapse into the same answer.
        """
        assert not (temp_config_dir / "config.json").exists()

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is True
        assert delegator.delegation_off_reason is None

    @pytest.mark.bdd
    @pytest.mark.parametrize("value", ["off", "0", "false", "no", "OFF"])
    def test_an_environment_variable_turns_delegation_off_for_one_session(
        self, temp_config_dir, value: str
    ) -> None:
        """GIVEN CONJURE_DELEGATION set to a falsy spelling.

        WHEN the delegator loads its policy
        THEN delegation is off and names the environment as the source

        The per-session opt-out, for the run where a prompt should not
        leave the machine. Case and spelling vary because an operator
        typing this at a shell prompt should not have to guess.
        """
        with patch.dict(os.environ, {"CONJURE_DELEGATION": value}):
            delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is False
        assert delegator.delegation_off_reason is not None
        assert "CONJURE_DELEGATION" in delegator.delegation_off_reason

    @pytest.mark.bdd
    def test_the_environment_can_re_enable_what_the_config_turned_off(
        self, temp_config_dir
    ) -> None:
        """GIVEN a config file that disables delegation.

        WHEN CONJURE_DELEGATION says on
        THEN delegation is on

        Precedence runs environment over file, so the narrower scope
        wins. Without this the persistent switch would strand an operator
        who wanted delegation back for a single command.
        """
        (temp_config_dir / "config.json").write_text(json.dumps({"enabled": False}))

        with patch.dict(os.environ, {"CONJURE_DELEGATION": "on"}):
            delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is True

    @pytest.mark.bdd
    @patch.object(Delegator, "verify_service")
    def test_an_opted_out_delegator_probes_no_provider(
        self, mock_verify, temp_config_dir
    ) -> None:
        """GIVEN delegation turned off.

        WHEN smart_delegate is called anyway
        THEN no provider is probed and the result names the opt-out

        Opting out has to cost nothing, or it is not an opt-out. A
        disabled delegator that still shells out to eight CLIs to
        discover it should not have would be the worst of both.
        """
        with patch.dict(os.environ, {"CONJURE_DELEGATION": "off"}):
            delegator = Delegator(config_dir=temp_config_dir)
            result = delegator.smart_delegate("test prompt")

        mock_verify.assert_not_called()
        assert result.success is False
        assert result.fallback_reason == FALLBACK_DISABLED


class TestTheProviderChainRunsToExhaustion:
    """A single provider's failure is not the end of the delegation.

    Selection used to stop at the first available provider and run it
    once. Availability is not the same as answering, so a provider that
    was installed and authenticated but broke on the call ended the
    attempt with a failure the caller had to notice on its own.
    """

    @staticmethod
    def _answer(stdout: str, exit_code: int = 0) -> ExecutionResult:
        return ExecutionResult(
            success=exit_code == 0,
            stdout=stdout,
            stderr="",
            exit_code=exit_code,
            duration=0.1,
        )

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_a_failed_provider_hands_the_work_to_the_next_one(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """GIVEN the first provider in the order exits non-zero.

        WHEN smart_delegate runs
        THEN the second provider is tried and its answer is returned

        The behaviour the opt-out default depends on: with delegation on
        for every eligible task, a provider that is merely installed
        should not be able to sink the task on its own.
        """
        mock_verify.return_value = (True, [])
        mock_execute.side_effect = [
            self._answer("", exit_code=1),
            self._answer("second provider answered"),
        ]

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        assert result.success is True
        assert result.stdout == "second provider answered"
        assert result.service == delegator.candidate_order()[1]

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_an_empty_answer_counts_as_a_failure_worth_advancing_past(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """GIVEN a provider that exits 0 and prints nothing.

        WHEN smart_delegate runs
        THEN the chain advances rather than returning the silence

        Exit code alone is not the failure signal here. This repository
        already recorded `opencode run` returning success with an empty
        stdout, and a help page printed at exit 0 for a dash-leading
        prompt. Both are answers to nobody.
        """
        mock_verify.return_value = (True, [])
        mock_execute.side_effect = [
            self._answer("   \n"),
            self._answer("a real answer"),
        ]

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        assert result.stdout == "a real answer"

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_exhausting_every_provider_asks_the_caller_to_do_it_locally(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """GIVEN no provider is installed.

        WHEN smart_delegate runs
        THEN it returns a fallback signal instead of raising

        Turning delegation on by default makes "nothing installed" the
        ordinary path, not the exceptional one: it is what every operator
        who has not set up a CLI will hit on their first mission. A
        traceback is the wrong shape for a state the caller is expected
        to recover from by doing the work itself.
        """
        mock_verify.return_value = (False, ["not installed"])

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        assert result.success is False
        assert result.fallback_reason == FALLBACK_EXHAUSTED
        mock_execute.assert_not_called()

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_the_exhausted_result_records_what_each_provider_did(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """GIVEN every provider fails for a different reason.

        WHEN the chain is exhausted
        THEN each attempt is named in the result

        A bare "delegation failed" gives an operator nothing to fix. The
        trail distinguishes a machine with nothing installed from one
        where every CLI is present and every credential has expired.
        """
        mock_verify.side_effect = lambda name: (
            (True, []) if name == "gemini" else (False, ["not installed"])
        )
        mock_execute.return_value = self._answer("", exit_code=1)

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        attempted = {attempt.service: attempt.reason for attempt in result.attempts}
        assert set(attempted) == set(delegator.services)
        assert "exit 1" in attempted["gemini"]
        assert "not installed" in attempted["qwen"]

    @pytest.mark.bdd
    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_a_provider_that_answers_ends_the_chain(
        self, mock_verify, mock_execute, temp_config_dir
    ) -> None:
        """GIVEN the first provider answers.

        WHEN smart_delegate runs
        THEN no further provider is probed or executed

        The chain is a fallback, not a fan-out. Running all eight on
        every task would multiply the cost of the new default by eight.
        """
        mock_verify.return_value = (True, [])
        mock_execute.return_value = self._answer("first answered")

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        assert result.service == delegator.candidate_order()[0]
        mock_execute.assert_called_once()
        assert len(result.attempts) == 1


class TestTheCliSaysWhenNothingRan:
    """An absent answer must not read like an empty one.

    The `auto` path used to raise out of selection and the CLI caught it.
    Now it returns a result, and the risk moves: a fallback result printed
    on stdout at exit 0 is indistinguishable from a provider that answered
    with nothing.
    """

    @pytest.mark.bdd
    @patch.object(Delegator, "verify_service")
    @patch("sys.argv", ["delegation_executor.py", "auto", "summarize this"])
    def test_an_exhausted_chain_exits_non_zero_and_names_each_provider(
        self, mock_verify, capsys, temp_config_dir
    ) -> None:
        """GIVEN no provider is installed.

        WHEN the CLI runs an auto delegation
        THEN it exits 1 and reports every provider it tried on stderr

        The trail is the actionable half. A bare failure line cannot tell
        an operator whether to install a CLI or renew a credential.
        """
        mock_verify.return_value = (False, ["binary not found"])

        with (
            patch.object(Delegator, "__init__", _init_with(temp_config_dir)),
            pytest.raises(SystemExit) as exit_info,
        ):
            main()

        assert exit_info.value.code == 1
        stderr = capsys.readouterr().err
        assert FALLBACK_EXHAUSTED in stderr
        assert "gemini: binary not found" in stderr

    @pytest.mark.bdd
    @patch.object(Delegator, "verify_service")
    @patch("sys.argv", ["delegation_executor.py", "auto", "summarize this"])
    def test_an_opted_out_run_says_which_switch_was_thrown(
        self, mock_verify, capsys, temp_config_dir
    ) -> None:
        """GIVEN delegation turned off in the environment.

        WHEN the CLI runs an auto delegation
        THEN stderr names the variable rather than blaming the providers

        Someone who forgot the variable was exported should not spend the
        afternoon reinstalling CLIs that were never consulted.
        """
        with (
            patch.dict(os.environ, {"CONJURE_DELEGATION": "off"}),
            patch.object(Delegator, "__init__", _init_with(temp_config_dir)),
            pytest.raises(SystemExit),
        ):
            main()

        stderr = capsys.readouterr().err
        assert "CONJURE_DELEGATION" in stderr
        mock_verify.assert_not_called()


def _init_with(config_dir):
    """Pin a Delegator built by main() to the test's config directory."""
    real_init = Delegator.__init__

    def _init(self, config_dir_arg=None):
        real_init(self, config_dir=config_dir)

    return _init


class TestAuthIsSettledBeforeAProviderIsSpawned:
    """Verification must cost less than the delegation it decides against.

    The chain skips a provider that fails verification, so verification is
    the only thing standing between an unauthenticated CLI and a full
    delegation round trip. It was not doing that job: three of the four
    CLI-auth probes exit 0 whatever the credential state, and one of them
    was not an auth command at all.
    """

    @pytest.mark.bdd
    def test_qwen_asks_its_api_nothing_to_learn_whether_it_is_authenticated(
        self, temp_config_dir
    ) -> None:
        """GIVEN qwen, which has no auth subcommand.

        WHEN its authentication is verified
        THEN no probe argv is spawned

        `qwen --help` lists no auth command, so `qwen auth status` was
        delivered to the model as the prompt "auth status" and billed as
        a completion. Probed on 2026-08-22 it answered
        `[API Error: 401 Incorrect API key provided]` and exited 0, so
        the probe reported success while paying for a rejected call.
        Every chain walk paid it before reaching a provider that answers.
        """
        service = Delegator(config_dir=temp_config_dir).services["qwen"]

        assert service.auth_probe == ()

    @pytest.mark.bdd
    def test_a_provider_with_no_credential_file_is_ruled_out_without_spawning(
        self, temp_config_dir, tmp_path
    ) -> None:
        """GIVEN a provider whose credential files are all absent.

        WHEN it is verified
        THEN it is unauthenticated and nothing was executed

        The cheapest honest signal available. A CLI that stores
        credentials in a file it names cannot be authenticated when the
        file is not there, and learning that costs a stat rather than a
        process.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["filebound"] = replace(
            delegator.services["opencode"],
            name="filebound",
            auth_files=(str(tmp_path / "nothing-here.json"),),
        )

        with patch("subprocess.run") as spawn:
            is_available, issues = delegator.verify_service("filebound")

        assert is_available is False
        assert any("credential" in issue.lower() for issue in issues)
        spawn.assert_not_called()

    @pytest.mark.bdd
    def test_a_credential_file_that_exists_does_not_prove_authentication(
        self, temp_config_dir, tmp_path
    ) -> None:
        """GIVEN a provider whose credential file is present.

        WHEN it is verified
        THEN the file check clears it to continue, and nothing more

        The check is one-directional on purpose. `opencode auth list`
        exits 0 listing a credentials path that does not exist, and
        `codex login status` prints "Logged in using ChatGPT" over a
        refresh token that has already been spent. Presence of a file is
        the same class of evidence: it rules a provider out, never in.
        """
        credential = tmp_path / "auth.json"
        credential.write_text("{}")

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["filebound"] = replace(
            delegator.services["opencode"],
            name="filebound",
            auth_files=(str(credential),),
            auth_probe=(),
            version_probe=(),
        )

        with patch("subprocess.run") as spawn:
            spawn.return_value = subprocess.CompletedProcess([], 0, "", "")
            _, issues = delegator.verify_service("filebound")

        assert not any("credential" in issue.lower() for issue in issues)

    @pytest.mark.bdd
    def test_muse_accepts_a_credential_file_in_place_of_the_variable(
        self, temp_config_dir, tmp_path, monkeypatch
    ) -> None:
        """GIVEN muse authenticated by file rather than by variable.

        WHEN it is verified
        THEN the missing variable is not reported as missing credentials

        muse says so itself: "run `muse login` or set META_API_KEY, or
        save credentials at ~/.config/muse/auth.json". The check knew
        only the variable, so an operator who ran `muse login` was told
        their working install was unauthenticated.
        """
        monkeypatch.delenv("META_API_KEY", raising=False)
        credential = tmp_path / "auth.json"
        credential.write_text("{}")

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["muse"] = replace(
            delegator.services["muse"],
            auth_files=(str(credential),),
        )

        _, issues = delegator.verify_service("muse")

        assert not any("META_API_KEY" in issue for issue in issues)

    @pytest.mark.bdd
    def test_the_variable_still_authenticates_when_no_file_is_written(
        self, temp_config_dir, monkeypatch
    ) -> None:
        """GIVEN muse authenticated by variable, with no credential file.

        WHEN it is verified
        THEN the absent file is not reported as missing credentials

        The mirror of the file-in-place-of-variable case, and the one a
        file check gets wrong if it forgets the other route exists. Both
        routes are muse's own: "run `muse login` or set META_API_KEY, or
        save credentials at ~/.config/muse/auth.json". Either satisfies
        it, so neither absence is a finding on its own.
        """
        monkeypatch.setenv("META_API_KEY", "test-key")
        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["muse"] = replace(
            delegator.services["muse"],
            auth_files=("/nonexistent/muse/auth.json",),
            version_probe=(),
        )

        _, issues = delegator.verify_service("muse")

        assert not any("credential" in issue.lower() for issue in issues)

    @pytest.mark.bdd
    def test_a_credential_that_states_its_own_expiry_is_read_not_spawned(
        self, temp_config_dir, tmp_path
    ) -> None:
        """GIVEN a credential file whose stated expiry has passed.

        WHEN the provider is verified
        THEN it is ruled out without spawning anything

        The case that started this. qwen's oauth_creds.json on this
        machine expired 2026-03-25 and was still on disk in August, so a
        presence check cleared it, the chain executed it, and it answered
        an empty string at exit 0. The expiry was in the file the whole
        time.
        """
        credential = tmp_path / "oauth_creds.json"
        credential.write_text(json.dumps({"expiry_date": 1_000_000_000_000}))

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["qwen"] = replace(
            delegator.services["qwen"],
            auth_files=(str(credential),),
        )

        with patch("subprocess.run") as spawn:
            is_available, issues = delegator.verify_service("qwen")

        assert is_available is False
        assert any("expired" in issue.lower() for issue in issues)
        spawn.assert_not_called()

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "payload",
        [
            {"last_refresh": "2025-12-26T19:01:43Z"},
            {"expiry_date": "not a number"},
            {"access_token": "x"},
            "not json at all",
        ],
        ids=["no-expiry-field", "unparseable-expiry", "bare-token", "not-json"],
    )
    def test_a_credential_that_states_no_expiry_is_not_called_expired(
        self, temp_config_dir, tmp_path, payload
    ) -> None:
        """GIVEN a credential file with no readable expiry.

        WHEN the provider is verified
        THEN nothing is claimed about it either way

        codex writes `last_refresh` and no expiry, which says when a
        token was renewed and nothing about when it dies. Reading that as
        an expiry would rule out a working provider, which is worse than
        the round trip this check exists to save.
        """
        credential = tmp_path / "auth.json"
        credential.write_text(
            payload if isinstance(payload, str) else json.dumps(payload)
        )

        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["codex"] = replace(
            delegator.services["codex"],
            auth_files=(str(credential),),
            version_probe=(),
            auth_probe=(),
        )

        _, issues = delegator.verify_service("codex")

        assert not any("expired" in issue.lower() for issue in issues)

    @pytest.mark.bdd
    def test_a_missing_variable_is_reported_without_spawning_the_binary(
        self, temp_config_dir, monkeypatch
    ) -> None:
        """GIVEN a provider whose required variable is unset.

        WHEN it is verified
        THEN the answer arrives before any subprocess

        Verification ran the version probe first, so gemini paid a node
        process start to confirm a binary exists before reading the
        environment variable that already decided the question. Ordering
        the checks by cost is the whole of "settle auth before trying".
        """
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        delegator = Delegator(config_dir=temp_config_dir)

        with patch("subprocess.run") as spawn:
            is_available, issues = delegator.verify_service("gemini")

        assert is_available is False
        assert any("GEMINI_API_KEY" in issue for issue in issues)
        spawn.assert_not_called()
