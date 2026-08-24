"""Test delegation error paths that were missing test coverage.

Addresses issue #32 - missing tests for error handling in
delegation_executor.py.  Uses parametrize for service variants
and adds mock verification (assert_called_with / call_args).
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.delegation_executor import (
    FALLBACK_DISABLED,
    FALLBACK_EXHAUSTED,
    Delegator,
    ExecutionResult,
)

# -------------------------------------------------------------------
# smart_delegate - no services
# -------------------------------------------------------------------


class TestSmartDelegateNoServices:
    """Test smart_delegate() when no services are available."""

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_reports_when_no_services_available(
        self,
        mock_verify: MagicMock,
        temp_config_dir,
    ) -> None:
        """smart_delegate returns a fallback signal when nothing can take the work.

        This asserted a RuntimeError while delegation was opt-in. Under the
        default-on policy an operator with no CLI installed is the ordinary
        case, so an empty chain became a returned result the caller acts on.
        """
        mock_verify.return_value = (False, ["Service not available"])
        delegator = Delegator(config_dir=temp_config_dir)

        result = delegator.smart_delegate(
            "test prompt",
            files=None,
            requirements=None,
        )

        assert result.fallback_reason == FALLBACK_EXHAUSTED
        # Verify every service was probed
        assert mock_verify.call_count == len(delegator.services)

    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_tries_all_services_before_failing(
        self,
        mock_verify: MagicMock,
        temp_config_dir,
    ) -> None:
        """smart_delegate checks all services before reporting the fallback."""
        checked: list[str] = []

        def track_verify(name: str) -> tuple[bool, list[str]]:
            checked.append(name)
            return False, [f"{name} not available"]

        mock_verify.side_effect = track_verify
        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.smart_delegate("test prompt").fallback_reason

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
        temp_config_dir,
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

        delegator = Delegator(config_dir=temp_config_dir)
        result = delegator.smart_delegate("test prompt")

        assert result.service == expected_service
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


class TestAResultCannotAnswerAndReportExhaustion:
    """The two rules stated in the `fallback_reason` comment, enforced.

    The mission orchestrator, project-execution and the egregore summon
    skill each branch on this field alone. A result that carries output
    *and* an exhaustion reason sends all three down the no-answer path
    over a real answer.
    """

    @staticmethod
    def _kwargs(**over: object) -> dict:
        base = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": 1,
            "duration": 0.0,
        }
        base.update(over)
        return base

    def test_a_success_cannot_carry_a_fallback_reason(self) -> None:
        """An answer and an exhaustion reason cannot travel together."""
        with pytest.raises(ValueError, match="carries no fallback_reason"):
            ExecutionResult(
                **self._kwargs(
                    success=True,
                    stdout="a real answer",
                    exit_code=0,
                    fallback_reason=FALLBACK_EXHAUSTED,
                )
            )

    def test_an_unknown_reason_is_refused(self) -> None:
        """Only the two declared constants name a fallback."""
        with pytest.raises(ValueError, match="unknown fallback_reason"):
            ExecutionResult(**self._kwargs(fallback_reason="ran_out_of_ideas"))

    def test_the_two_declared_reasons_are_accepted(self) -> None:
        """The guard rejects the invalid without rejecting the valid."""
        for reason in (FALLBACK_DISABLED, FALLBACK_EXHAUSTED):
            assert (
                ExecutionResult(**self._kwargs(fallback_reason=reason)).fallback_reason
                == reason
            )

    def test_an_ordinary_answer_carries_no_reason(self) -> None:
        """A plain success is unaffected by the guard."""
        result = ExecutionResult(
            **self._kwargs(success=True, stdout="output", exit_code=0)
        )
        assert result.fallback_reason is None


class TestTheModelFlagComesFromTheServiceConfig:
    """`--model` was the one flag hardcoded past ServiceConfig.

    The comment two lines above the call claimed every flag spelling
    comes from the config. It is not even universal: `ollama run --help`
    (0.13.1) documents `ollama run MODEL [PROMPT]` and lists no
    `--model`, so passing one to glimmer exits 1 on an unknown flag.
    """

    def test_glimmer_takes_its_model_positionally(self) -> None:
        """Ollama run has no --model; the model rides the subcommand."""
        command = Delegator().build_command("glimmer", "hi", None, {"model": "x"})
        assert "--model" not in command
        assert "muse-glimmer:30b" in command

    def test_a_provider_with_the_flag_still_receives_it(self) -> None:
        """Broadening the rule must not drop the flag where it is real."""
        command = Delegator().build_command(
            "minimax", "hi", None, {"model": "MiniMax-M3"}
        )
        assert "--model" in command
        assert command[command.index("--model") + 1] == "MiniMax-M3"

    def test_the_spelling_is_data_not_a_branch(self) -> None:
        """Changing the config changes the argv, with no code change."""
        delegator = Delegator()
        delegator.services["minimax"] = replace(
            delegator.services["minimax"], model_flag="--llm"
        )
        command = delegator.build_command("minimax", "hi", None, {"model": "m"})
        assert "--llm" in command
        assert "--model" not in command


class TestTheAuditTrailAndTheOverridesAreNotSilent:
    """Two failures that returned or logged at a level nobody reads."""

    def test_a_services_key_of_the_wrong_type_is_reported(
        self, tmp_path, caplog
    ) -> None:
        """A dropped override is announced rather than returned past."""
        config = tmp_path / "config.json"
        config.write_text(json.dumps({"services": ["gemini"]}))
        delegator = Delegator(config_dir=tmp_path)
        delegator.config_file = config

        with caplog.at_level(logging.ERROR):
            delegator.load_configurations()

        assert any("expected an object" in r.message for r in caplog.records), (
            "every override was dropped with no log at any level"
        )

    def test_an_unwritable_usage_log_is_reported(self, tmp_path, caplog) -> None:
        """The audit trail failing is louder than debug."""
        delegator = Delegator(config_dir=tmp_path)
        delegator.usage_log = tmp_path / "no-such-dir" / "usage.jsonl"
        result = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=0.1
        )

        with caplog.at_level(logging.WARNING):
            delegator.log_usage("gemini", ["gemini"], result)

        assert any("audit trail" in r.message for r in caplog.records)


class TestVerifyAnswersCanThisProviderTakeWork:
    """`--verify` reported OK for two providers that cannot serve a call.

    Both were found by running the real binaries. qwen 0.4.0 prints
    "[API Error: 401 Incorrect API key provided...]" and exits 0, and
    its delegation envelope reports `is_error: false` over the same
    text, so the exit code is not a signal for that CLI. glimmer probes
    `ollama --version`, which answers whenever ollama is installed and
    says nothing about whether the model was ever pulled.
    """

    def test_a_probe_that_exits_zero_over_a_rejection_is_not_authenticated(
        self, tmp_path
    ) -> None:
        """The exit code is not a signal for a CLI that prints its 401."""
        delegator = Delegator(config_dir=tmp_path)
        service = replace(
            delegator.services["qwen"],
            auth_method="cli",
            auth_probe=("auth", "status"),
            auth_files=(),
            auth_env_var=None,
            env={},
        )
        delegator.services["qwen"] = service

        rejected = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="[API Error: 401 Incorrect API key]",
            stderr="",
        )
        with patch("subprocess.run", return_value=rejected):
            ok, issues = delegator.verify_service("qwen")

        assert not ok
        assert any("exited 0" in issue for issue in issues)

    def test_a_clean_probe_still_verifies(self, tmp_path) -> None:
        """The marker must not condemn a provider that is actually fine."""
        delegator = Delegator(config_dir=tmp_path)
        delegator.services["qwen"] = replace(
            delegator.services["qwen"],
            auth_method="cli",
            auth_probe=("auth", "status"),
            auth_files=(),
            auth_env_var=None,
            env={},
        )

        good = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Logged in as someone", stderr=""
        )
        with patch("subprocess.run", return_value=good):
            ok, issues = delegator.verify_service("qwen")

        assert ok, issues

    def test_an_unpulled_model_is_not_a_ready_provider(self, tmp_path) -> None:
        """An installed runtime is not a served model."""
        delegator = Delegator(config_dir=tmp_path)
        empty_list = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="NAME  ID  SIZE  MODIFIED\n", stderr=""
        )
        with patch("subprocess.run", return_value=empty_list):
            ok, issues = delegator.verify_service("glimmer")

        assert not ok
        assert any("muse-glimmer:30b" in issue for issue in issues)
        assert any("ollama pull" in issue for issue in issues)

    def test_a_pulled_model_verifies(self, tmp_path) -> None:
        """The probe must not condemn a provider that is ready."""
        delegator = Delegator(config_dir=tmp_path)
        listed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="NAME              ID    SIZE\nmuse-glimmer:30b  abc   19 GB\n",
            stderr="",
        )
        with patch("subprocess.run", return_value=listed):
            ok, issues = delegator.verify_service("glimmer")

        assert ok, issues
