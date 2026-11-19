"""Characterization tests for provider verification after its extraction.

The behavior was pinned through Delegator.verify_service before the move;
these import ``delegation_verify`` directly so deleting the module turns
them red.
"""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import Delegator  # noqa: E402 - sys.path set above
from delegation_services import (
    SERVICES,
    ServiceConfig,  # noqa: E402 - sys.path set above
)
from delegation_verify import (  # noqa: E402 - sys.path set above
    readiness_issues,
    verify_service,
)

_BASE = ServiceConfig(
    name="probe",
    command="probe-cli",
    auth_method="api_key",
    auth_env_var="PROBE_API_KEY",
)


def _service(**overrides: Any) -> ServiceConfig:
    """Vary one provider without restating its required fields."""
    return replace(_BASE, **overrides)


class TestVerifyService:
    """The cheapest question is asked first and nothing is spawned after a no."""

    def test_unset_credential_costs_no_subprocess(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unset variable rules the provider out before any probe runs."""
        monkeypatch.delenv("PROBE_API_KEY", raising=False)
        with patch("subprocess.run") as run:
            ok, issues = verify_service(_service())
        assert not ok
        assert issues == ["Environment variable PROBE_API_KEY not set"]
        run.assert_not_called()

    def test_missing_binary_names_its_install_hint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A FileNotFoundError from the version probe becomes the remedy."""
        monkeypatch.setenv("PROBE_API_KEY", "k")
        with patch("subprocess.run", side_effect=FileNotFoundError):
            ok, issues = verify_service(_service(install_hint="brew install probe"))
        assert not ok
        assert issues == [
            "Command 'probe-cli' not found. Install with: brew install probe"
        ]


class TestReadinessIssues:
    """The binary being present is not the provider being able to serve."""

    def test_expected_text_absent_is_reported_with_the_hint(self) -> None:
        """`readiness_expect` missing from stdout is a named, remediable issue."""
        service = _service(
            readiness_probe=("list",),
            readiness_expect="model-x",
            readiness_hint="pull it",
        )
        fake = type("R", (), {"returncode": 0, "stdout": "model-y\n", "stderr": ""})()
        with patch("subprocess.run", return_value=fake):
            issues = readiness_issues(service, {})
        assert issues == [
            "probe is installed but 'model-x' is not available to it. pull it"
        ]


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


class TestVerifyServiceNarrowException:
    """Auth probe must not swallow unexpected exceptions.

    These used to run against qwen, which no longer declares an auth
    probe: it has no auth subcommand, so the inherited one was delivered
    to the model as a prompt. The contract under test is the probe's
    exception handling, so the class moved to a provider that still runs
    one, and plants a credential file so the cheaper checks do not settle
    the question first.
    """

    @staticmethod
    def _probed(tmp_path: Path) -> Delegator:
        """Return a delegator whose codex entry reaches its auth probe."""
        credential = tmp_path / "auth.json"
        credential.write_text("{}")
        delegator = Delegator(config_dir=tmp_path)
        delegator.services["codex"] = replace(
            delegator.services["codex"],
            auth_files=(str(credential),),
        )
        return delegator

    def test_unexpected_exception_propagates_from_auth_probe(
        self, tmp_path: Path
    ) -> None:
        """Propagate an unexpected error raised by the auth probe.

        GIVEN a version check that succeeds and an auth probe that
            raises RuntimeError
        WHEN verify_service runs
        THEN the RuntimeError propagates
        AND it is not swallowed as a normal issue
        """
        delegator = self._probed(tmp_path)

        # --version call succeeds, auth status raises unexpected error
        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[ok_result, RuntimeError("unexpected auth failure")],
        ):
            with pytest.raises(RuntimeError, match="unexpected auth failure"):
                delegator.verify_service("codex")

    def test_timeout_is_caught_as_issue(self, tmp_path: Path) -> None:
        """Report an auth-probe timeout as a service issue.

        GIVEN a version check that succeeds and an auth probe that
            raises TimeoutExpired
        WHEN verify_service runs
        THEN the service is reported unavailable
        AND an auth-related issue is included
        """
        delegator = self._probed(tmp_path)

        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[
                ok_result,
                subprocess.TimeoutExpired(cmd=["codex", "login", "status"], timeout=10),
            ],
        ):
            is_available, issues = delegator.verify_service("codex")
            assert not is_available
            assert any("auth" in i.lower() for i in issues)

    def test_file_not_found_is_caught_as_issue(self, tmp_path: Path) -> None:
        """Report a missing auth binary as a service issue.

        GIVEN a version check that succeeds and an auth probe that
            raises FileNotFoundError
        WHEN verify_service runs
        THEN the service is reported unavailable
        AND an auth-related issue is included
        """
        delegator = self._probed(tmp_path)

        ok_result = MagicMock()
        ok_result.returncode = 0

        with patch(
            "scripts.delegation_executor.subprocess.run",
            side_effect=[ok_result, FileNotFoundError("codex not found")],
        ):
            is_available, issues = delegator.verify_service("codex")
            assert not is_available
            assert any("auth" in i.lower() for i in issues)


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


def test_verify_probe_env_drops_env_unset_variables(monkeypatch) -> None:
    """--verify spawns the provider CLI too, so it drops the same variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-parent")
    monkeypatch.setenv("ZAI_API_KEY", "zai-test-value")
    seen_envs = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        seen_envs.append(kwargs["env"])
        return subprocess.CompletedProcess(args[0], 0, "1.0.0", "")

    with patch("delegation_verify.subprocess.run", side_effect=fake_run):
        verify_service(SERVICES["glm"])

    assert seen_envs
    assert all("ANTHROPIC_API_KEY" not in env for env in seen_envs)


def test_missing_binary_is_reported_before_a_missing_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No binary and no key: the trail said "set the key" (CNJ-2)."""
    monkeypatch.delenv("PROBE_API_KEY", raising=False)
    module = sys.modules[verify_service.__module__]
    monkeypatch.setattr(module, "_binary_on_path", lambda _c: False)
    ok, issues = verify_service(_service(install_hint="pipx install probe-cli"))
    assert ok is False
    assert issues == [
        "Command 'probe-cli' not found. Install with: pipx install probe-cli"
    ]
