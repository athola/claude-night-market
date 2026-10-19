"""Characterization tests for the service registry and credential checks.

Written green before ``delegation_executor.py`` was split, so the split
had a contract to keep. They pin behavior, not location: the import line
is the only thing that moved with the code, and it now names
``delegation_services`` so deleting that module turns these red.
"""

import dataclasses
import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import delegation_services  # noqa: E402 - sys.path set above
from delegation_executor import (  # noqa: E402 - sys.path set above
    Delegator,
    ExecutionResult,
)
from delegation_services import (  # noqa: E402 - sys.path set above
    VERIFIED_BINARIES,
    ServiceConfig,
    _apply_overrides,
    _expired_credentials,
    _missing_required_fields,
    _smart_delegate_model,
    credential_file_issues,
    credential_issues,
    resolve_env_overlay,
)

_BASE = ServiceConfig(
    name="probe", command="probe", auth_method="api_key", auth_env_var="PROBE_API_KEY"
)


def _api_key_service(**overrides: Any) -> ServiceConfig:
    """Vary one API-key provider without restating its required fields."""
    return replace(_BASE, **overrides)


class TestCredentialIssues:
    """Contract for credential issues."""

    def test_unset_variable_with_no_files_is_one_issue(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no file route declared, the variable is the only route, so its absence is the whole finding."""
        monkeypatch.delenv("PROBE_API_KEY", raising=False)
        assert credential_issues(_api_key_service()) == [
            "Environment variable PROBE_API_KEY not set"
        ]

    def test_set_variable_clears_every_file_finding(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A set variable satisfies the provider on its own; the state of a credential file then decides nothing."""
        monkeypatch.setenv("PROBE_API_KEY", "k")
        service = _api_key_service(auth_files=(str(tmp_path / "absent.json"),))
        assert credential_issues(service) == []
        assert credential_file_issues(service) == []

    def test_present_file_keeps_the_env_question_open(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A file on disk is one route among several, so an unset variable beside it is not an issue. muse says as much in its own error text."""
        monkeypatch.delenv("PROBE_API_KEY", raising=False)
        creds = tmp_path / "creds.json"
        creds.write_text("{}")
        assert credential_issues(_api_key_service(auth_files=(str(creds),))) == []

    def test_declared_files_all_absent_names_where_it_looked(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Both routes failed, so both are reported, and the file finding names the paths so the operator can create one."""
        monkeypatch.delenv("PROBE_API_KEY", raising=False)
        missing = str(tmp_path / "absent.json")
        issues = credential_issues(_api_key_service(auth_files=(missing,)))
        assert issues == [
            f"No credential file found; looked for {missing}",
            "Environment variable PROBE_API_KEY not set",
        ]


class TestExpiredCredentials:
    """Contract for expired credentials."""

    def _write(self, tmp_path: Path, payload: object) -> str:
        path = tmp_path / "oauth_creds.json"
        path.write_text(json.dumps(payload))
        return str(path)

    def test_past_millisecond_expiry_is_reported_with_its_date(
        self, tmp_path: Path
    ) -> None:
        """Qwen writes `expiry_date` in epoch milliseconds; a stale file cleared a presence check for five months and spent a call on a dead token."""
        past_ms = int((time.time() - 86_400) * 1000)
        path = self._write(tmp_path, {"expiry_date": past_ms})
        expired = _expired_credentials(_api_key_service(auth_files=(path,)))
        assert len(expired) == 1
        assert expired[0][0] == path
        assert len(expired[0][1]) == len("2026-01-01")

    def test_future_expiry_in_seconds_is_not_reported(self, tmp_path: Path) -> None:
        """Seconds and milliseconds are told apart by magnitude, so a seconds value in the future must not be read as a millisecond value in 1970."""
        path = self._write(tmp_path, {"expires_at": time.time() + 3600})
        assert _expired_credentials(_api_key_service(auth_files=(path,))) == []

    def test_unparseable_or_non_numeric_produces_no_finding(
        self, tmp_path: Path
    ) -> None:
        """Ruling out a working provider costs more than one wasted round trip, so only a stated numeric expiry counts and a bool is not a number."""
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        boolean = self._write(tmp_path, {"expiry": True})
        service = _api_key_service(auth_files=(str(bad), boolean))
        assert _expired_credentials(service) == []


class TestEnvOverlay:
    """Contract for env overlay."""

    def test_references_resolve_and_unset_ones_are_named(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty substitution would send an unauthenticated request that surfaces as a 401 far from its cause, so the unset name is reported instead."""
        monkeypatch.setenv("PROBE_HOST", "https://h")
        monkeypatch.delenv("PROBE_MISSING", raising=False)
        service = _api_key_service(
            env={"BASE": "${PROBE_HOST}/v1", "KEY": "${PROBE_MISSING}"}
        )
        resolved, missing = resolve_env_overlay(service)
        assert resolved == {"BASE": "https://h/v1", "KEY": ""}
        assert missing == ["PROBE_MISSING"]


class TestApplyOverrides:
    """Contract for apply overrides."""

    def test_unknown_field_raises_instead_of_being_dropped(self) -> None:
        """CJR-003: config load must not swallow a typo as a silent no-op."""
        with pytest.raises(TypeError, match="unknown ServiceConfig field"):
            _apply_overrides(_api_key_service(), "probe", {"nope": 1})

    def test_name_in_overrides_is_ignored_and_others_replace(self) -> None:
        """The registry key is the name; letting an override rename a service would detach it from its own entry."""
        updated = _apply_overrides(
            _api_key_service(), "probe", {"name": "other", "priority": 7}
        )
        assert updated.name == "probe"
        assert updated.priority == 7


class TestSmartDelegateModel:
    """Contract for smart delegate model."""

    def test_requirement_model_wins_and_default_backs_it(self) -> None:
        """Model ids live on the config so registering a provider is the only step; a module-level table used to raise KeyError for a new one."""
        service = _api_key_service(
            default_model="d", large_context_model="big", fast_response_model=None
        )
        assert _smart_delegate_model(service, "large_context") == "big"
        assert _smart_delegate_model(service, "fast_response") == "d"
        assert _smart_delegate_model(service, "anything") == "d"

    def test_minimax_routes_current_models_and_preserves_saved_overrides(
        self, temp_config_dir
    ) -> None:
        """Smart selection must emit current IDs while saved choices remain authoritative."""
        service = Delegator(config_dir=temp_config_dir).services["minimax"]
        assert _smart_delegate_model(service, "anything") == "MiniMax-M3.1-Flash"
        assert _smart_delegate_model(service, "fast_response") == "MiniMax-M3.1-Flash"
        assert _smart_delegate_model(service, "large_context") == "MiniMax-M3"
        saved = _apply_overrides(
            service,
            "minimax",
            {"default_model": "MiniMax-M2.7", "fast_response_model": "custom-model"},
        )
        assert _smart_delegate_model(saved, "anything") == "MiniMax-M2.7"
        assert _smart_delegate_model(saved, "fast_response") == "custom-model"
        delegator = Delegator(config_dir=temp_config_dir)
        delegator.services["minimax"] = saved
        command = delegator.build_command("minimax", "question")
        assert command[command.index("--model") + 1] == "MiniMax-M2.7"

    def test_service_with_no_models_yields_none(self) -> None:
        """None means the CLI's own default applies, which is degradation rather than the KeyError the old table raised."""
        assert _smart_delegate_model(_api_key_service(), "large_context") is None


DEFAULT_REQUESTS_PER_MINUTE = 60


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
    def test_a_cli_with_only_a_boolean_json_flag_emits_that_flag(
        self, temp_config_dir, service: str
    ) -> None:
        """GIVEN a CLI whose only JSON control is a boolean --json.

        WHEN a caller asks for JSON
        THEN the valueless flag reaches argv and no value follows it

        `--json` takes no value, so the key-and-value shape cannot
        express it: `--json json` would land "json" as a positional and
        displace the prompt, since both providers take the prompt
        positionally. The request used to be dropped in silence for
        that reason. `output_format_is_boolean` carries the shape now,
        which is issue #684. Emitting --output-format is still not the
        answer: muse exits 2 on it, and so does codex.
        """
        delegator = Delegator(config_dir=temp_config_dir)
        command = delegator.build_command(
            service, "extract", options={"output_format": "json"}
        )

        assert "--output-format" not in command
        assert "--json" in command
        assert command[command.index("--json") + 1] != "json", (
            "a valueless flag must not be followed by its own name"
        )
        assert command[-1] == "extract", "the prompt stays positional and last"

    @pytest.mark.bdd
    @pytest.mark.parametrize("service", ["muse", "codex"])
    def test_an_unsupported_format_is_refused_rather_than_dropped(
        self, temp_config_dir, service: str
    ) -> None:
        """GIVEN a CLI with exactly one machine-readable mode.

        WHEN a caller asks for a different format
        THEN the call raises rather than returning argv without it

        A caller that asked for a format is entitled to know it cannot
        have one. Silence was the previous answer and is what issue
        #684 asked to end.
        """
        delegator = Delegator(config_dir=temp_config_dir)

        with pytest.raises(ValueError, match="valueless"):
            delegator.build_command(
                service, "extract", options={"output_format": "yaml"}
            )


class TestTheContractCannotBeRewrittenUnderneath:
    """Provider contracts are shared, so they must not be assignable."""

    @pytest.mark.bdd
    def test_a_service_config_refuses_field_assignment(self) -> None:
        """GIVEN the registry entry every Delegator shares.

        WHEN a caller assigns to one of its fields
        THEN the assignment raises

        ``Delegator.__init__`` does ``dict(self.SERVICES)``, which copies
        the mapping and not the values, so every Delegator in a process
        holds the same ServiceConfig objects as the class default. While
        the dataclass was mutable, one field assignment anywhere rewrote
        the contract for every later Delegator, including ones already
        constructed. ``_apply_overrides`` already returns a new object via
        ``replace``, so nothing needed the mutability.
        """
        service = Delegator.SERVICES["gemini"]

        # setattr rather than a plain assignment: assigning to a frozen
        # field is the behavior under test, so a direct write is exactly
        # what the type checker is right to reject.
        with pytest.raises(dataclasses.FrozenInstanceError):
            service.priority = 1

    @pytest.mark.bdd
    def test_overriding_one_delegator_leaves_the_class_default_alone(
        self, temp_config_dir
    ) -> None:
        """GIVEN a config file overriding gemini's priority.

        WHEN a delegator loads it
        THEN the class default keeps its original priority

        The behavior the frozen dataclass protects, stated as the caller
        sees it rather than as an exception type.
        """
        before = Delegator.SERVICES["gemini"].priority
        (temp_config_dir / "config.json").write_text(
            json.dumps({"services": {"gemini": {"priority": 999}}})
        )

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.services["gemini"].priority == 999
        assert Delegator.SERVICES["gemini"].priority == before


class TestAuthMethodIsValidated:
    """``auth_method`` is a de-facto enum over api_key, cli and none.

    ``_apply_overrides`` validates field names, not values, so a config
    saying ``auth_method: apikey`` constructed cleanly and then matched
    neither the api_key branch nor the cli one: the service skipped both
    the auth probe and the API-key check while reporting itself
    configured.
    """

    def test_an_unknown_auth_method_is_rejected(self) -> None:
        """A near-miss spelling must not construct."""
        with pytest.raises(ValueError, match="auth_method"):
            delegation_services.ServiceConfig(
                name="typo",
                command="typo-cli",
                auth_method="apikey",
            )

    def test_each_known_auth_method_constructs(self) -> None:
        """The three real values still work."""
        for method in sorted(delegation_services.AUTH_METHODS):
            config = delegation_services.ServiceConfig(
                name="ok", command="ok-cli", auth_method=method, auth_env_var="OK_KEY"
            )
            assert config.auth_method == method

    def test_every_registered_service_declares_a_known_method(self) -> None:
        """The shipped registry must satisfy its own invariant."""
        for name, config in delegation_services.SERVICES.items():
            assert config.auth_method in delegation_services.AUTH_METHODS, (
                f"{name} declares auth_method {config.auth_method!r}"
            )


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


class TestContradictoryPairingsDoNotConstruct:
    """A pairing ``build_command`` or ``verify_service`` cannot honor is refused.

    Each case below constructed cleanly and failed later: at argv time,
    or by reporting a provider ready that checks nothing. Construction is
    where ``config.json`` is read, so a refusal there names the entry
    before any delegation depends on it.
    """

    @pytest.mark.parametrize(
        ("overrides", "field_named"),
        [
            pytest.param(
                {"prompt_flag": "-p", "prompt_long_flag": None},
                "prompt_long_flag",
                id="flag-prompt-without-long-form",
            ),
            pytest.param(
                {"prompt_flag": "--message", "prompt_long_flag": ""},
                "prompt_long_flag",
                id="flag-prompt-with-empty-long-form",
            ),
            pytest.param(
                {"output_format_flag": None, "output_format_is_boolean": True},
                "output_format_is_boolean",
                id="boolean-format-without-flag",
            ),
            pytest.param(
                {"auth_method": "api_key", "auth_env_var": None},
                "auth_env_var",
                id="api-key-without-variable",
            ),
            pytest.param(
                {"readiness_expect": "model-x"},
                "readiness_expect",
                id="readiness-expect-without-probe",
            ),
            pytest.param(
                {"readiness_hint": "pull it"},
                "readiness_hint",
                id="readiness-hint-without-probe",
            ),
        ],
    )
    def test_the_error_names_the_field(
        self, overrides: dict[str, Any], field_named: str
    ) -> None:
        """The operator reading config.json is told which field to change."""
        fields = {"name": "probe", "command": "probe", "auth_method": "none"}
        with pytest.raises(ValueError, match=field_named):
            ServiceConfig(**{**fields, **overrides})

    @pytest.mark.parametrize(
        "overrides",
        [
            pytest.param({}, id="defaults"),
            pytest.param({"prompt_flag": None}, id="positional"),
            pytest.param({"stdin_prompt": True, "prompt_long_flag": None}, id="stdin"),
            pytest.param(
                {"output_format_flag": "--json", "output_format_is_boolean": True},
                id="boolean-format",
            ),
            pytest.param(
                {"readiness_probe": ("list",), "readiness_expect": "m"},
                id="readiness",
            ),
        ],
    )
    def test_a_coherent_pairing_constructs(self, overrides: dict[str, Any]) -> None:
        """Each rule refuses only its contradiction, not its neighbors."""
        ServiceConfig(name="probe", command="probe", auth_method="none", **overrides)

    def test_the_defaults_escape_a_dash_prompt(self) -> None:
        """The defaults claim the Gemini contract, whose long form is ``--prompt``."""
        service = ServiceConfig(name="probe", command="probe", auth_method="none")

        assert service.prompt_long_flag == "--prompt"

    @pytest.mark.parametrize(
        "service", list(delegation_services.SERVICES.values()), ids=lambda s: s.name
    )
    def test_every_registered_service_reconstructs(self, service) -> None:
        """A registry entry that broke a rule would fail here by name."""
        assert replace(service) == service
