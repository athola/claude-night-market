"""Test delegation error paths that were missing test coverage.

Addresses issue #32 - missing tests for error handling in
delegation_executor.py.  Uses parametrize for service variants
and adds mock verification (assert_called_with / call_args).
"""

from __future__ import annotations

import json
import logging
import subprocess
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
        clock = [1000.0]

        def simulate_timeout(*_a, **_k):
            clock[0] += 12.5
            raise subprocess.TimeoutExpired(cmd="gemini", timeout=1)

        mock_run.side_effect = simulate_timeout

        delegator = Delegator()
        with patch("scripts.delegation_executor.time") as fake_time:
            fake_time.time.side_effect = lambda: clock[0]
            result = delegator.execute("gemini", "test prompt", timeout=1)

        assert result.duration == 12.5
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


class TestRefusedCredentialIsNotAnAnswer:
    """A provider's refusal text at exit 0 is not an answer.

    qwen prints its 401 and exits 0. The markers were read only by the
    auth probe, which qwen does not have.
    """

    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_smart_delegate_skips_qwen_when_exit0_stdout_carries_auth_failure_marker(
        self, mock_verify: MagicMock, mock_execute: MagicMock, temp_config_dir
    ) -> None:
        """The chain records the refusal and does not stop at qwen."""
        mock_verify.side_effect = lambda name: (name == "qwen", [])
        mock_execute.return_value = ExecutionResult(
            success=True,
            stdout="[API Error: 401 Incorrect API key provided: sk-xx]",
            stderr="",
            exit_code=0,
            duration=1.0,
        )

        result = Delegator(config_dir=temp_config_dir).smart_delegate("p")

        assert not result.success
        qwen_attempt = next(a for a in result.attempts if a.service == "qwen")
        assert "credential refused" in qwen_attempt.reason


class TestAnswerQuotingAMarkerIsStillAnAnswer:
    """The refusal check reads where the CLI puts its error, not the body."""

    @patch.object(Delegator, "execute")
    @patch.object(Delegator, "verify_service")
    def test_answer_that_quotes_an_auth_error_is_kept(
        self, mock_verify: MagicMock, mock_execute: MagicMock, temp_config_dir
    ) -> None:
        """An explanation of a 401 is an answer, not a refusal."""
        mock_verify.side_effect = lambda name: (name == "qwen", [])
        mock_execute.return_value = ExecutionResult(
            success=True,
            stdout="The log shows:\n\n    API Error: 401 Incorrect API key\n",
            stderr="",
            exit_code=0,
            duration=1.0,
        )

        result = Delegator(config_dir=temp_config_dir).smart_delegate("p")

        assert result.success
        assert result.service == "qwen"


class TestEndpointSwapChildEnvironment:
    """An endpoint-swap child does not inherit the real vendor's key.

    glm runs the stock claude binary against Z.ai.
    """

    def test_glm_child_env_excludes_anthropic_api_key(
        self, temp_config_dir, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The overlay token stays; the parent's Anthropic credentials go."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-parent")
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-parent")
        zai_key = "zai-test-value"
        monkeypatch.setenv("ZAI_API_KEY", zai_key)
        delegator = Delegator(config_dir=temp_config_dir)
        launched = []

        def capture(spec):
            launched.append(spec)
            return ExecutionResult(
                success=True, stdout="ok", stderr="", exit_code=0, duration=0.1
            )

        with patch.object(Delegator, "_launch_process", side_effect=capture):
            delegator.execute("glm", "p")

        env = launched[0].env
        assert "ANTHROPIC_API_KEY" not in env
        assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
        assert env["ANTHROPIC_AUTH_TOKEN"] == zai_key


class TestUsageLogRedaction:
    """The usage log keeps no prompt text (CNJ-5).

    It joined the whole argv, prompt and inlined files included.
    """

    def test_usage_log_does_not_contain_prompt_text(self, temp_config_dir) -> None:
        """The log keeps the shape of the command, not the prompt."""
        delegator = Delegator(config_dir=temp_config_dir)
        result = ExecutionResult(
            success=False, stdout="", stderr="e" * 5000, exit_code=1, duration=0.1
        )
        delegator.log_usage(
            "gemini",
            ["gemini", "-p", "SECRET-PROMPT-TEXT and more"],
            result,
            prompt="SECRET-PROMPT-TEXT and more",
        )

        logged = delegator.usage_log.read_text()
        assert "SECRET-PROMPT-TEXT" not in logged
        assert "<prompt: 27 chars>" in logged
        assert len(json.loads(logged.splitlines()[-1])["error"]) <= 500

    def test_a_short_prompt_blanks_only_the_argument_that_carries_it(
        self, temp_config_dir
    ) -> None:
        """Prompt "hi" blanked `--thinking-budget`, which contains it (U8)."""
        delegator = Delegator(config_dir=temp_config_dir)
        finished = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=0.1
        )
        delegator.log_usage(
            "gemini",
            ["gemini", "--thinking-budget", "1024", "-p", "hi"],
            finished,
            prompt="hi",
        )
        logged = json.loads(delegator.usage_log.read_text().splitlines()[-1])
        assert logged["command"] == "gemini --thinking-budget 1024 -p <prompt: 2 chars>"

    def test_a_stdin_service_logs_its_argv_unredacted(self, temp_config_dir) -> None:
        """Its prompt never enters argv, so no argument is the prompt."""
        delegator = Delegator(config_dir=temp_config_dir)
        finished = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=0.1
        )
        delegator.log_usage(
            "glimmer", ["ollama", "run", "muse-glimmer:30b"], finished, prompt="muse"
        )
        logged = json.loads(delegator.usage_log.read_text().splitlines()[-1])
        assert logged["command"] == "ollama run muse-glimmer:30b"

    def test_an_unregistered_service_still_has_its_prompt_redacted(
        self, temp_config_dir
    ) -> None:
        """Only a service known to read stdin is logged unredacted."""
        delegator = Delegator(config_dir=temp_config_dir)
        finished = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0, duration=0.1
        )
        delegator.log_usage(
            "unlisted",
            ["tool", "-p", "SECRET-PROMPT"],
            finished,
            prompt="SECRET-PROMPT",
        )
        assert "SECRET-PROMPT" not in delegator.usage_log.read_text()

    def test_execute_redacts_the_prompt_in_the_usage_log(self, temp_config_dir) -> None:
        """execute() must hand log_usage the prompt, or the log keeps it."""
        delegator = Delegator(config_dir=temp_config_dir)
        launched = ExecutionResult(
            success=True, stdout="ok", stderr="", exit_code=0, duration=0.1
        )
        with patch.object(Delegator, "_launch_process", return_value=launched):
            delegator.execute("gemini", "SECRET-PROMPT")

        logged = delegator.usage_log.read_text()
        assert "SECRET-PROMPT" not in logged
        assert "<prompt: 13 chars>" in logged


class TestExecuteRefusesUnsetOverlay:
    """A direct execute() refuses an unset overlay variable (CNJ-3).

    It skipped verify_service and spawned glm with an empty auth token.
    """

    def test_execute_refuses_to_spawn_when_overlay_variable_unset(
        self, temp_config_dir, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No process starts, and the result names the variable."""
        monkeypatch.delenv("ZAI_API_KEY", raising=False)
        launch = MagicMock()
        with patch.object(Delegator, "_launch_process", launch):
            result = Delegator(config_dir=temp_config_dir).execute("glm", "p")
        launch.assert_not_called()
        assert not result.success
        assert "ZAI_API_KEY" in result.stderr


def test_usage_summary_tolerates_null_tokens(temp_config_dir) -> None:
    """A null tokens_used lost that call's duration from the total (CNJ-11)."""
    now = datetime.now().isoformat()
    delegator = Delegator(config_dir=temp_config_dir)
    delegator.usage_log.write_text(
        json.dumps(
            {
                "timestamp": now,
                "service": "gemini",
                "success": False,
                "tokens_used": None,
                "duration": 5,
            }
        )
        + "\n"
        + json.dumps(
            {
                "timestamp": now,
                "service": "gemini",
                "success": True,
                "tokens_used": 7,
                "duration": 2,
            }
        )
        + "\n"
    )
    summary = delegator.get_usage_summary()
    assert summary["services"]["gemini"]["tokens_used"] == 7
    assert summary["services"]["gemini"]["total_duration"] == 7


@patch.object(Delegator, "verify_service", return_value=(True, []))
@patch.object(Delegator, "execute")
def test_smart_delegate_passes_the_timeout_to_each_provider(
    mock_execute: MagicMock, _verify: MagicMock, temp_config_dir
) -> None:
    """`auto` dropped --timeout, so each of up to eight providers got 300 s (CNJ-12)."""
    mock_execute.return_value = ExecutionResult(
        success=True, stdout="ok", stderr="", exit_code=0, duration=0.1
    )
    Delegator(config_dir=temp_config_dir).smart_delegate("p", timeout=30)
    assert mock_execute.call_args.kwargs.get("timeout") == 30


@patch("scripts.delegation_executor.refused_credential_output", return_value=True)
@patch.object(Delegator, "verify_service", return_value=(True, []))
@patch.object(Delegator, "execute")
def test_a_refused_credential_is_recorded_in_the_provider_ledger(
    mock_execute: MagicMock, _verify: MagicMock, _refused: MagicMock, temp_config_dir
) -> None:
    """record_failure had no caller, so a 401 never reached it (CNJ-13)."""
    mock_execute.return_value = ExecutionResult(
        success=True,
        stdout="401 Incorrect API key provided",
        stderr="",
        exit_code=0,
        duration=0.1,
    )
    delegator = Delegator(config_dir=temp_config_dir)
    delegator.smart_delegate("p")

    ledger = json.loads((temp_config_dir / "provider-state.json").read_text())
    errors = [entry["last_error"] for entry in ledger["providers"].values()]
    assert errors and all(errors), ledger


@patch.object(Delegator, "verify_service", return_value=(True, []))
@patch.object(Delegator, "execute")
def test_total_timeout_bounds_the_whole_chain(
    mock_execute: MagicMock, _verify: MagicMock, temp_config_dir
) -> None:
    """Eight providers at 300 s each could run 40 minutes (CNJ-12)."""
    mock_execute.return_value = ExecutionResult(
        success=False, stdout="", stderr="boom", exit_code=1, duration=0.1
    )
    # start, before provider 1, before provider 2, before provider 3
    clock = iter([0.0, 0.0, 250.0, 400.0, 400.0, 400.0, 400.0, 400.0])
    with patch("scripts.delegation_executor.time.monotonic", lambda: next(clock)):
        Delegator(config_dir=temp_config_dir).smart_delegate(
            "p", timeout=300, total_timeout=300
        )
    timeouts = [c.kwargs["timeout"] for c in mock_execute.call_args_list]
    assert timeouts[0] == 300
    assert timeouts[1] == 50
    assert len(timeouts) == 2


@patch.object(Delegator, "verify_service", return_value=(True, []))
@patch.object(Delegator, "execute")
def test_no_availability_probe_runs_after_the_total_timeout(
    mock_execute: MagicMock, mock_verify: MagicMock, temp_config_dir
) -> None:
    """A probe for a provider past the deadline ran, and its result was dropped."""
    clock = iter([0.0, 400.0, 400.0])
    with patch("scripts.delegation_executor.time.monotonic", lambda: next(clock)):
        result = Delegator(config_dir=temp_config_dir).smart_delegate(
            "p", timeout=300, total_timeout=300
        )
    mock_verify.assert_not_called()
    mock_execute.assert_not_called()
    assert result.attempts[-1].reason == "total timeout reached"


@patch("scripts.delegation_executor.refused_credential_output", return_value=True)
@patch.object(Delegator, "verify_service", return_value=(True, []))
@patch.object(Delegator, "execute")
def test_an_unwritable_ledger_does_not_stop_the_chain(
    mock_execute: MagicMock, _verify: MagicMock, _refused: MagicMock, temp_config_dir
) -> None:
    """Recording a refusal must not turn a disk error into a lost fallback (CNJ-13)."""
    mock_execute.return_value = ExecutionResult(
        success=True, stdout="401", stderr="", exit_code=0, duration=0.1
    )
    with patch(
        "scripts.delegation_executor.ProviderLedger.save", side_effect=OSError("ro")
    ):
        Delegator(config_dir=temp_config_dir).smart_delegate("p")
    assert mock_execute.call_count > 1
