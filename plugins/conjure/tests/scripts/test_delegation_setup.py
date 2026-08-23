"""Tests for delegation_setup.py following TDD/BDD principles."""

import json
import subprocess

# Import the module under test
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import Delegator
from delegation_setup import (
    DECLINED,
    FAILED,
    INSTALLED,
    UnverifiedBinaryError,
    doctor_lines,
    install_command_for,
    install_provider,
    main,
    probe_all,
    probe_provider,
    render_status,
)


class TestProbing:
    """Provider state is read from the registry, never hardcoded."""

    @pytest.mark.bdd
    def test_every_registered_service_is_probed(self) -> None:
        """A provider absent from the report is a provider nobody installs.

        The table is built from the delegator's own registry, so registering
        a service is enough to make it appear here too.
        """
        states = probe_all(Delegator())

        assert {state.name for state in states} == set(Delegator.SERVICES)

    @pytest.mark.bdd
    def test_a_missing_binary_is_reported_as_not_installed(self, monkeypatch) -> None:
        """Absence is a first-class state, not an error."""
        monkeypatch.setattr("delegation_setup.shutil.which", lambda _: None)

        states = {state.name: state for state in probe_all(Delegator())}

        assert states["muse"].installed is False

    @pytest.mark.bdd
    def test_status_table_names_every_provider_and_its_binary(self) -> None:
        """The operator has to see which binary a provider actually spawns.

        #655 shipped a service pointing at a binary nobody publishes, so the
        binary column is what makes that class of mistake visible.
        """
        rendered = render_status(probe_all(Delegator()))

        assert "glm" in rendered
        assert "claude" in rendered
        assert "muse" in rendered


class TestInstallProvenance:
    """Nothing is executed that the provenance map does not vouch for."""

    @pytest.mark.bdd
    def test_install_command_comes_from_the_provenance_map(self) -> None:
        """The install string is data a reviewer already checked."""
        assert install_command_for("codex") == "npm install -g @openai/codex"

    @pytest.mark.bdd
    def test_an_unverified_binary_has_no_install_command(self) -> None:
        """Refusing is the point.

        Resolving an install command for an unrecorded binary would let a
        mistyped or attacker-chosen name reach a shell with -g privileges,
        which is the failure #655 shipped.
        """
        with pytest.raises(UnverifiedBinaryError, match="totally-not-real"):
            install_command_for("totally-not-real")

    @pytest.mark.bdd
    def test_declining_the_prompt_installs_nothing(self) -> None:
        """Consent gates execution, so declining must be inert."""
        runner = MagicMock()

        outcome = install_provider("codex", confirm=lambda _: False, runner=runner)

        assert outcome == DECLINED
        runner.assert_not_called()

    @pytest.mark.bdd
    def test_confirming_runs_the_recorded_command(self) -> None:
        """A confirmed install runs the vouched-for command and nothing else."""
        runner = MagicMock(return_value=subprocess.CompletedProcess([], 0))

        outcome = install_provider("codex", confirm=lambda _: True, runner=runner)

        assert outcome == INSTALLED
        assert runner.call_args.args[0] == [
            "/bin/sh",
            "-c",
            "npm install -g @openai/codex",
        ]

    @pytest.mark.bdd
    def test_the_prompt_shows_publisher_and_source(self) -> None:
        """Consent is uninformed without naming who publishes the artifact.

        Muse installs by piping a remote script into a shell, so the source
        URL is the only thing an operator can check beforehand.
        """
        shown: list[str] = []

        def decline(text: str) -> bool:
            shown.append(text)
            return False

        install_provider("muse", confirm=decline, runner=MagicMock())

        assert "Meta" in shown[0]
        assert "https://dev.meta.ai/docs/muse-code" in shown[0]


class TestInstallAll:
    """Declining an offer is a choice, not a failure."""

    @pytest.mark.bdd
    def test_declining_every_offer_still_exits_clean(self, monkeypatch) -> None:
        """--all reports success when the operator installs nothing.

        Given: no provider CLI is installed
        When:  the operator declines every offer
        Then:  the command exits 0 and names nothing as failed

        Conflating a decline with a failed install turns the normal path
        through `make delegate-install`, where an operator wants two of
        eight, into a red build.
        """
        monkeypatch.setattr("delegation_setup.shutil.which", lambda _: None)
        monkeypatch.setattr(
            "delegation_setup.install_provider",
            lambda *_args, **_kwargs: DECLINED,
        )

        assert main(["--all"]) == 0

    @pytest.mark.bdd
    def test_a_failed_install_is_still_an_error(self, monkeypatch) -> None:
        """An install that ran and failed is reported as a failure."""
        monkeypatch.setattr("delegation_setup.shutil.which", lambda _: None)
        monkeypatch.setattr(
            "delegation_setup.install_provider",
            lambda *_args, **_kwargs: FAILED,
        )

        assert main(["--all"]) == 1


class TestDoctor:
    """Each failure names the one command that resolves it."""

    @pytest.mark.bdd
    def test_a_missing_binary_is_answered_with_its_install_command(
        self,
        monkeypatch,
    ) -> None:
        """A diagnosis without a remedy only restates the problem."""
        monkeypatch.setattr("delegation_setup.shutil.which", lambda _: None)
        delegator = Delegator()

        lines = "\n".join(doctor_lines(probe_all(delegator)))

        assert "npm install -g @openai/codex" in lines

    @pytest.mark.bdd
    def test_an_unset_credential_is_named(self, monkeypatch) -> None:
        """Naming the variable is the whole remedy for an endpoint swap."""
        monkeypatch.setattr(
            "delegation_setup.shutil.which",
            lambda name: f"/usr/bin/{name}",
        )
        monkeypatch.delenv("ZAI_API_KEY", raising=False)
        delegator = Delegator()

        lines = "\n".join(doctor_lines(probe_all(delegator)))

        assert "ZAI_API_KEY" in lines

    @pytest.mark.bdd
    def test_a_variable_needed_twice_is_reported_once(self, monkeypatch) -> None:
        """GLM names ZAI_API_KEY as both its auth variable and its overlay.

        Listing it twice tells the operator there are two things to fix when
        there is one, which is how a trivial setup reads as a broken one.
        """
        monkeypatch.setattr(
            "delegation_setup.shutil.which",
            lambda name: f"/usr/bin/{name}",
        )
        monkeypatch.delenv("ZAI_API_KEY", raising=False)

        state = {s.name: s for s in probe_all(Delegator())}["glm"]

        assert [issue for issue in state.issues if "ZAI_API_KEY" in issue] == [
            "environment variable ZAI_API_KEY is not set"
        ]

    @pytest.mark.bdd
    def test_an_installed_provider_is_not_told_to_install_itself(
        self,
        monkeypatch,
    ) -> None:
        """An install command is no remedy for a missing credential.

        gemini with an unset key is installed and working; printing its
        install command sends the operator to fix the wrong thing.
        """
        monkeypatch.setattr(
            "delegation_setup.shutil.which",
            lambda name: f"/usr/bin/{name}",
        )
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        delegator = Delegator()

        text = "\n".join(doctor_lines(probe_all(delegator)))

        assert "export GEMINI_API_KEY=" in text
        assert "npm install -g @google/gemini-cli" not in text


class TestCliManagedAuthIsNotOverclaimed:
    """A credential the probe never inspected is reported as unknown.

    The probe deliberately does not spawn each CLI, so for providers whose
    credentials live inside the CLI it has no evidence either way. Reporting
    "ok" there turned a skipped check into a claim: `delegate-setup` showed
    minimax as authenticated while `mmx` had no credentials at all and the
    delegation failed on the first call.
    """

    @pytest.mark.bdd
    def test_a_cli_managed_provider_is_reported_unknown_not_ok(self) -> None:
        """GIVEN a provider whose auth lives in the CLI.

        WHEN the status table is rendered
        THEN its auth cell reads unknown rather than ok
        """
        delegator = Delegator()
        states = {state.name: state for state in probe_all(delegator)}
        cli_managed = [
            name
            for name, service in delegator.services.items()
            if service.auth_method == "cli" and states[name].installed
        ]
        assert cli_managed, "registry has no installed cli-auth provider to check"

        rendered = render_status(probe_all(delegator))
        for name in cli_managed:
            row = next(
                line for line in rendered.splitlines() if line.startswith(f"{name} ")
            )
            assert row.split()[-1] != "ok", (
                f"{name} manages its own credentials, so the probe has no "
                f"evidence it is authenticated; row claimed: {row!r}"
            )

    @pytest.mark.bdd
    def test_an_absent_credential_file_is_reported_missing_not_unknown(
        self, tmp_path
    ) -> None:
        """GIVEN a cli-auth provider whose credential file is absent.

        WHEN the status table is rendered
        THEN its auth cell reads missing

        "Unknown" was honest while absence of evidence was all the probe
        had. A CLI that names the file it stores credentials in gives up
        more than that: the file not being there is evidence, and it
        costs a stat rather than a spawn, so the NB3 constraint that this
        table spawns no CLI still holds.
        """
        delegator = Delegator()
        delegator.services["filebound"] = replace(
            delegator.services["opencode"],
            name="filebound",
            command="sh",
            auth_files=(str(tmp_path / "absent.json"),),
        )

        state = probe_provider(delegator, "filebound")

        assert state.auth_checked is True
        assert state.authenticated is False
        assert any("credential" in issue.lower() for issue in state.issues)

    @pytest.mark.bdd
    def test_an_expired_credential_is_reported_missing_not_unknown(
        self, tmp_path
    ) -> None:
        """GIVEN a credential file whose stated expiry has passed.

        WHEN the table is rendered
        THEN the provider reads missing rather than unknown

        The table is the surface an operator reads before deciding what
        to fix. A provider whose credential says of itself that it died
        in March must not be shrugged at, or the operator reinstalls a
        CLI that was never the problem.
        """
        credential = tmp_path / "oauth_creds.json"
        credential.write_text(json.dumps({"expiry_date": 1_000_000_000_000}))

        delegator = Delegator()
        delegator.services["filebound"] = replace(
            delegator.services["opencode"],
            name="filebound",
            command="sh",
            auth_files=(str(credential),),
        )

        state = probe_provider(delegator, "filebound")

        assert state.auth_checked is True
        assert state.authenticated is False
        assert any("expired" in issue.lower() for issue in state.issues)

    @pytest.mark.bdd
    def test_a_present_credential_file_stays_unknown(self, tmp_path) -> None:
        """GIVEN a cli-auth provider whose credential file exists.

        WHEN the status table is rendered
        THEN its auth cell still reads unknown

        The check only rules out. `codex login status` printed "Logged in
        using ChatGPT" over a spent refresh token, and its auth.json was
        on disk the whole time. Promoting presence to "ok" would restore
        exactly the overclaim this class exists to prevent.
        """
        credential = tmp_path / "auth.json"
        credential.write_text("{}")

        delegator = Delegator()
        delegator.services["filebound"] = replace(
            delegator.services["opencode"],
            name="filebound",
            command="sh",
            auth_files=(str(credential),),
        )

        state = probe_provider(delegator, "filebound")

        assert state.auth_checked is False

    @pytest.mark.bdd
    def test_an_api_key_provider_still_reports_ok_when_set(self, monkeypatch) -> None:
        """GIVEN an api_key provider whose variable is set.

        WHEN the status table is rendered
        THEN it still reads ok, because that check really ran
        """
        delegator = Delegator()
        for service in delegator.services.values():
            if service.auth_method == "api_key" and service.auth_env_var:
                monkeypatch.setenv(service.auth_env_var, "test-key")
        states = {state.name: state for state in probe_all(delegator)}
        checked = [
            name
            for name, service in delegator.services.items()
            if service.auth_method == "api_key" and states[name].installed
        ]
        assert checked, "registry has no installed api_key provider to check"
        for name in checked:
            assert states[name].authenticated is True

    @pytest.mark.bdd
    def test_doctor_names_the_verified_login_command(self) -> None:
        """GIVEN a cli-auth provider with a recorded login command.

        WHEN doctor explains it
        THEN the recorded command appears, and none is invented
        """
        delegator = Delegator()
        lines = "\n".join(doctor_lines(probe_all(delegator)))
        assert "mmx auth login" in lines


class TestCliDispatch:
    """The flags reach the code that answers them.

    `doctor_lines`, `install_provider` and the DECLINED/FAILED triage are
    each covered above in isolation. What was not covered is `main`
    routing a flag to them, which is the part an operator actually runs.
    Every branch below was reachable only through the CLI.
    """

    @pytest.mark.bdd
    def test_an_unknown_service_is_rejected_by_name(self, monkeypatch, capsys) -> None:
        """GIVEN a --install argument naming no registered service.

        WHEN the CLI runs
        THEN it exits 1 and names the unknown service on stderr

        The registry is the list of installable things. Accepting a name
        absent from it would send an unverified binary to install_provider,
        which is the check UnverifiedBinaryError exists to make loud.
        """
        assert main(["--install", "not-a-provider"]) == 1
        assert "not-a-provider" in capsys.readouterr().err

    @pytest.mark.bdd
    def test_declining_a_single_install_is_not_an_error(self, monkeypatch) -> None:
        """GIVEN one named provider whose offer the operator declines.

        WHEN --install runs for it
        THEN the command exits 0

        This is the NB4 rule applied to the single-provider path. The
        --all path is guarded in TestInstallAll; without this, --install
        could regress to treating a decline as a failure while --all
        stayed correct.
        """
        monkeypatch.setattr(
            "delegation_setup.install_provider",
            lambda *_args, **_kwargs: DECLINED,
        )
        assert main(["--install", "gemini"]) == 0

    @pytest.mark.bdd
    def test_a_failed_single_install_is_an_error(self, monkeypatch) -> None:
        """GIVEN an install that ran and failed.

        WHEN --install runs for it
        THEN the command exits 1
        """
        monkeypatch.setattr(
            "delegation_setup.install_provider",
            lambda *_args, **_kwargs: FAILED,
        )
        assert main(["--install", "gemini"]) == 1

    @pytest.mark.bdd
    def test_nothing_to_install_is_reported_as_success(
        self,
        monkeypatch,
        capsys,
    ) -> None:
        """GIVEN every registered provider is already on PATH.

        WHEN --all runs
        THEN it says so and exits 0 without offering anything

        Reaching install_provider here would prompt the operator about
        software they already have.
        """
        monkeypatch.setattr(
            "delegation_setup.shutil.which",
            lambda _: "/usr/bin/stub",
        )

        def _refuse(*_args, **_kwargs):
            raise AssertionError("offered an install for a present binary")

        monkeypatch.setattr("delegation_setup.install_provider", _refuse)

        assert main(["--all"]) == 0
        assert "already installed" in capsys.readouterr().out

    @pytest.mark.bdd
    def test_doctor_output_reaches_stdout(self, monkeypatch, capsys) -> None:
        """GIVEN no provider CLI is installed, so every row is unhealthy.

        WHEN --doctor runs
        THEN the status table and the per-provider fixes are both printed

        doctor_lines is guarded directly in TestDoctor. This guards the
        wiring: the flag was parsed, the lines were built, and they were
        printed rather than discarded.
        """
        monkeypatch.setattr("delegation_setup.shutil.which", lambda _: None)

        assert main(["--doctor"]) == 0
        out = capsys.readouterr().out
        assert "PROVIDER" in out, "status table missing"
        assert "fix:" in out, "doctor explanations missing"
