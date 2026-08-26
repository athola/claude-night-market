"""Delegation probed eight CLIs on every call and remembered nothing.

Review on PR #662: "we need to have a skill which walks the user
through setting up one or many of these CLI providers and stores which
providers have been setup/auth'd on this machine vs just blindly
attempting/guessing each time", and "report to the user which
harnesses are properly setup and authenticated on this machine and
thus are available to call with conjure".

The ledger is the storage half. What it may and may not remember is
the load-bearing decision here, and it is asymmetric on purpose:

- **Installed and version** are cheap to re-derive and stable between
  runs, so they are cached with a time-to-live.
- **A confirmed credential** is cached with the timestamp that
  confirmed it, and never treated as current on its own. A token
  expires without touching the binary, so a positive auth cache would
  send work to a provider that has since started refusing it. The
  ledger records when the claim was made; the caller decides whether
  that is recent enough.
- **A recorded failure** invalidates the entry outright. This is the
  half that keeps the ledger from pinning a stale success.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

import pytest
from scripts.delegation_setup import (
    ProviderState,
    render_available,
    write_ledger,
)
from scripts.provider_ledger import (
    LEDGER_VERSION,
    ProviderLedger,
    ProviderRecord,
)

from scripts import delegation_setup, provider_ledger


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    """Return a ledger path in a temp dir, so no test touches the real one."""
    return tmp_path / "provider-state.json"


def _record(
    name: str,
    *,
    installed: bool = True,
    version: str | None = "1.0.0",
    auth_confirmed_at: float | None = 1000.0,
    recorded_at: float = 1000.0,
) -> ProviderRecord:
    """Build a record whose defaults describe a healthy provider.

    No ``last_error`` parameter: a failure is set through
    ``record_failure``, which is the only path that also clears the
    confirmation, and a test that set the field directly would bypass
    the behavior it means to check.
    """
    return ProviderRecord(
        name=name,
        binary=name,
        installed=installed,
        version=version,
        auth_confirmed_at=auth_confirmed_at,
        recorded_at=recorded_at,
    )


class TestRoundTrip:
    """Persistence, and how a damaged file degrades."""

    def test_records_survive_a_save_and_load(self, ledger_path: Path) -> None:
        """What was probed once is readable without probing again."""
        ledger = ProviderLedger(ledger_path)
        ledger.record(_record("gemini", version="0.26.0"))
        ledger.save()

        reloaded = ProviderLedger(ledger_path)

        assert reloaded.get("gemini").version == "0.26.0"

    def test_file_carries_a_version_for_forward_compatibility(
        self, ledger_path: Path
    ) -> None:
        """A future schema change must be able to tell the old shape apart."""
        ledger = ProviderLedger(ledger_path)
        ledger.record(_record("qwen"))
        ledger.save()

        assert json.loads(ledger_path.read_text())["version"] == LEDGER_VERSION

    def test_absent_file_loads_as_empty_rather_than_raising(
        self, ledger_path: Path
    ) -> None:
        """First run on a fresh machine is the ordinary path, not an error."""
        assert ProviderLedger(ledger_path).names() == ()

    def test_corrupt_file_loads_as_empty_rather_than_raising(
        self, ledger_path: Path
    ) -> None:
        """A truncated write must degrade to "probe again", never to a crash.

        The ledger is a cache. Losing it costs one round of probes.
        """
        ledger_path.write_text("{not json")

        assert ProviderLedger(ledger_path).names() == ()


class TestADamagedLedgerDegradesToACacheMiss:
    """Whole-file and per-entry damage, which are different failures.

    The round-trip tests cover a file that will not parse. These cover a
    file that parses into the wrong shape, which is what a future schema
    change produces on an old reader, and a file where one entry is
    malformed while the rest are fine.
    """

    def test_an_unfamiliar_version_is_ignored_wholesale(
        self, ledger_path: Path
    ) -> None:
        """GIVEN a ledger written by a later schema version.

        WHEN this reader loads it
        THEN no record is taken from it

        Reading unknown fields as a partial record would let a newer
        writer's meaning be silently reinterpreted. Discarding costs one
        round of probes, which is the price this module is built to pay.

        The record here is **complete and valid**, so the version check
        is the only thing that can reject it. With a malformed record
        the per-entry guard rejects it anyway and this test passes with
        the version check deleted, which is LL-006's failure mode.
        """
        ledger_path.write_text(
            json.dumps(
                {
                    "version": LEDGER_VERSION + 1,
                    "providers": {"gemini": asdict(_record("gemini"))},
                }
            )
        )

        assert ProviderLedger(ledger_path).names() == ()

    def test_one_malformed_entry_does_not_discard_the_others(
        self, ledger_path: Path
    ) -> None:
        """GIVEN a ledger with one good record and one malformed one.

        WHEN it is loaded
        THEN the good record survives and only the malformed one is dropped

        Invariant: per-entry damage is contained to that entry. This is
        the property that makes the ledger worth keeping across
        a partial write. Discarding the whole file on one bad record
        would turn a one-provider problem into a full re-probe.

        If this assertion ever needs to change, that is a decision about
        the invariant rather than about the test: preserve it, layer a
        repair pass on top, or revise it with a stated reason.
        """
        good = _record("gemini")
        ledger_path.write_text(
            json.dumps(
                {
                    "version": LEDGER_VERSION,
                    "providers": {
                        "gemini": asdict(good),
                        "qwen": {"name": "qwen", "unexpected_field": 1},
                    },
                }
            )
        )

        loaded = ProviderLedger(ledger_path)

        assert loaded.names() == ("gemini",)
        assert loaded.get("gemini").version == "1.0.0"


class TestFreshness:
    """The time-to-live on the cheap, stable facts."""

    def test_installed_facts_are_fresh_inside_the_ttl(self, ledger_path: Path) -> None:
        """A record inside the window still describes this machine."""
        ledger = ProviderLedger(ledger_path, ttl_seconds=3600)
        ledger.record(_record("codex", recorded_at=1000.0))

        assert ledger.is_fresh("codex", now=1000.0 + 3599)

    def test_installed_facts_go_stale_past_the_ttl(self, ledger_path: Path) -> None:
        """Past the window, an install or uninstall may have happened."""
        ledger = ProviderLedger(ledger_path, ttl_seconds=3600)
        ledger.record(_record("codex", recorded_at=1000.0))

        assert not ledger.is_fresh("codex", now=1000.0 + 3601)

    def test_unknown_provider_is_never_fresh(self, ledger_path: Path) -> None:
        """No entry is not a stale entry; it is no evidence at all."""
        assert not ProviderLedger(ledger_path).is_fresh("nobody", now=1000.0)


class TestAuthIsNeverAssumedCurrent:
    """A credential ages; a failure invalidates. The asymmetry."""

    def test_confirmed_auth_is_reported_with_its_age(self, ledger_path: Path) -> None:
        """The caller gets the timestamp, so it can apply its own bar."""
        ledger = ProviderLedger(ledger_path)
        ledger.record(_record("muse", auth_confirmed_at=1000.0))

        assert ledger.get("muse").auth_confirmed_at == 1000.0

    def test_a_recorded_failure_clears_the_confirmation(
        self, ledger_path: Path
    ) -> None:
        """A 401 after a cached success must not leave the success standing.

        This is the asymmetry the module exists for: a positive auth
        result ages, and a negative one invalidates immediately.
        """
        ledger = ProviderLedger(ledger_path)
        ledger.record(_record("qwen", auth_confirmed_at=1000.0))

        ledger.record_failure("qwen", "401 Incorrect API key provided")

        assert ledger.get("qwen").auth_confirmed_at is None
        assert ledger.get("qwen").last_error == "401 Incorrect API key provided"

    def test_failure_for_an_unprobed_provider_creates_an_entry(
        self, ledger_path: Path
    ) -> None:
        """A provider that failed before it was ever probed is still news."""
        ledger = ProviderLedger(ledger_path)

        ledger.record_failure("glimmer", "no model pulled")

        assert ledger.get("glimmer").last_error == "no model pulled"
        assert ledger.get("glimmer").auth_confirmed_at is None


class TestAvailableReport:
    """What conjure can call right now, by this ledger's reckoning."""

    def test_available_lists_installed_and_confirmed_providers(
        self, ledger_path: Path
    ) -> None:
        """The answer to "what can conjure call right now"."""
        ledger = ProviderLedger(ledger_path, ttl_seconds=3600)
        ledger.record(_record("gemini", recorded_at=1000.0))
        ledger.record(_record("qwen", recorded_at=1000.0, auth_confirmed_at=None))
        ledger.record(_record("codex", recorded_at=1000.0, installed=False))

        assert ledger.available(now=1000.0) == ("gemini",)

    def test_available_excludes_a_stale_entry(self, ledger_path: Path) -> None:
        """A record past its TTL is not evidence about this machine now."""
        ledger = ProviderLedger(ledger_path, ttl_seconds=3600)
        ledger.record(_record("gemini", recorded_at=1000.0))

        assert ledger.available(now=1000.0 + 7200) == ()

    def test_available_excludes_a_provider_with_a_recorded_failure(
        self, ledger_path: Path
    ) -> None:
        """A provider that started refusing work leaves the report."""
        ledger = ProviderLedger(ledger_path, ttl_seconds=3600)
        ledger.record(_record("muse", recorded_at=1000.0))
        ledger.record_failure("muse", "auth expired")

        assert ledger.available(now=1000.0) == ()


class TestSetupWritesTheLedger:
    """The probe an operator already paid for is the one worth storing."""

    @staticmethod
    def _state(
        name: str,
        *,
        installed: bool = True,
        authenticated: bool = True,
        issues: tuple[str, ...] = (),
        auth_checked: bool = True,
    ) -> ProviderState:
        """Build a state whose defaults describe a healthy provider."""
        return ProviderState(
            name=name,
            binary=name,
            installed=installed,
            version="1.0.0",
            authenticated=authenticated,
            issues=issues,
            missing_variables=(),
            auth_checked=auth_checked,
        )

    def test_confirmed_provider_is_recorded_as_available(
        self, ledger_path: Path
    ) -> None:
        """A healthy probe result reaches the availability report."""
        write_ledger([self._state("gemini")], path=ledger_path, now=1000.0)

        assert ProviderLedger(ledger_path).available(now=1000.0) == ("gemini",)

    def test_unprobed_auth_is_not_recorded_as_confirmed(
        self, ledger_path: Path
    ) -> None:
        """`auth_checked=False` is an absence of findings, not a finding.

        `ProviderState.authenticated` defaults true for providers whose
        credentials live inside the CLI, because the status table does
        not spawn the probe that would find out. Storing that as a
        confirmation would turn "we did not look" into "it works".
        """
        write_ledger(
            [self._state("muse", auth_checked=False)], path=ledger_path, now=1000.0
        )

        assert ProviderLedger(ledger_path).available(now=1000.0) == ()

    def test_issues_are_recorded_as_the_failure_that_clears_confirmation(
        self, ledger_path: Path
    ) -> None:
        """The first issue from the probe becomes the recorded failure."""
        write_ledger(
            [self._state("qwen", authenticated=False, issues=("401 rejected",))],
            path=ledger_path,
            now=1000.0,
        )

        assert ProviderLedger(ledger_path).get("qwen").last_error == "401 rejected"


class TestTheAvailabilityReport:
    """What an operator reads when they ask what conjure can call.

    `render_available` is the answer to the review question "report to
    the user which harnesses are properly setup and authenticated on
    this machine". It had no test, which for the one function whose
    whole job is telling a human the truth is the wrong place to have a
    gap.
    """

    def test_a_ready_provider_is_named(self, ledger_path: Path) -> None:
        """GIVEN a ledger holding one confirmed provider.

        WHEN the operator asks what is available
        THEN the provider is named in the line they read

        `render_available` reads the wall clock, because an operator
        asking "what can I call" means now. So these records carry a
        live timestamp rather than the fixed one the freshness tests
        use, which would read as stale against any real clock.
        """
        ledger = ProviderLedger(ledger_path, ttl_seconds=10**9)
        ledger.record(_record("gemini", recorded_at=time.time()))

        assert "gemini" in render_available(ledger)

    def test_several_ready_providers_are_listed_in_order(
        self, ledger_path: Path
    ) -> None:
        """GIVEN more than one confirmed provider.

        WHEN the operator asks what is available
        THEN all of them are listed, ordered so the line is stable
        """
        now = time.time()
        ledger = ProviderLedger(ledger_path, ttl_seconds=10**9)
        ledger.record(_record("qwen", recorded_at=now))
        ledger.record(_record("codex", recorded_at=now))

        assert render_available(ledger) == "Available to conjure: codex, qwen"

    def test_an_empty_ledger_says_what_to_run_next(self, ledger_path: Path) -> None:
        """GIVEN no provider is confirmed ready.

        WHEN the operator asks what is available
        THEN the reply names the commands that would fix it

        A bare "none" leaves the operator where they started. This is
        the branch they hit on a fresh machine, so it is the one that
        has to carry the next step.
        """
        line = render_available(ProviderLedger(ledger_path))

        assert "--doctor" in line
        assert "--install" in line

    def test_a_provider_with_a_failure_is_not_reported_available(
        self, ledger_path: Path
    ) -> None:
        """GIVEN a provider that was confirmed and has since refused work.

        WHEN the operator asks what is available
        THEN it is absent, because the report must not outlive the
        credential that earned it
        """
        ledger = ProviderLedger(ledger_path, ttl_seconds=10**9)
        ledger.record(_record("muse", recorded_at=time.time()))
        ledger.record_failure("muse", "auth expired")

        assert "muse" not in render_available(ledger)

    def test_a_directly_recorded_confirmed_failure_is_still_excluded(
        self, ledger_path: Path
    ) -> None:
        """GIVEN a record carrying both a confirmation and an error.

        WHEN the operator asks what is available
        THEN it is absent, because the error wins

        `record_failure` clears the confirmation, so the pair cannot
        arise through it, and a test that goes through it cannot tell
        the `last_error` clause from the `auth_confirmed_at` one. But
        `record` is public and takes whatever it is given, so the pair
        is reachable and the clause is load-bearing rather than
        redundant. This is the only path that proves it.
        """
        ledger = ProviderLedger(ledger_path, ttl_seconds=10**9)
        ledger.record(
            ProviderRecord(
                name="glm",
                binary="claude",
                installed=True,
                version="2.1.240",
                auth_confirmed_at=time.time(),
                recorded_at=time.time(),
                last_error="endpoint swap rejected the key",
            )
        )

        assert "glm" not in render_available(ledger)


class TestTheAvailableFlagIsReachable:
    """The CLI wiring for the report, not the report itself.

    `render_available` is tested above. This covers the branch that
    connects it to `--available`, which is the entry point the review
    asked for: "report to the user which harnesses are properly setup
    and authenticated on this machine". A correct report behind an
    unreachable flag answers nobody.

    `probe_all` is stubbed because it spawns one subprocess per
    installed CLI. That is the external dependency; the flag dispatch
    is the system under test.
    """

    def test_available_prints_the_report_and_exits_zero(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
    ) -> None:
        """GIVEN one provider probed as installed and authenticated.

        WHEN the operator runs the setup CLI with --available
        THEN the provider is named on stdout and the exit code is 0
        """
        probed = [
            ProviderState(
                name="gemini",
                binary="gemini",
                installed=True,
                version="0.26.0",
                authenticated=True,
                issues=(),
                missing_variables=(),
                auth_checked=True,
            )
        ]
        monkeypatch.setattr(delegation_setup, "probe_all", lambda _: probed)
        monkeypatch.setattr(delegation_setup, "Delegator", object)
        monkeypatch.setattr(
            provider_ledger, "DEFAULT_LEDGER_PATH", tmp_path / "state.json"
        )

        code = delegation_setup.main(["--available"])

        assert code == 0
        assert "gemini" in capsys.readouterr().out

    def test_available_reports_an_unconfigured_machine_without_failing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
    ) -> None:
        """GIVEN no provider is installed.

        WHEN the operator runs --available
        THEN it says so and still exits 0

        A fresh machine is the ordinary case, not an error. Exiting
        non-zero here would fail any script that asks the question
        before deciding whether to delegate.
        """
        monkeypatch.setattr(delegation_setup, "probe_all", lambda _: [])
        monkeypatch.setattr(delegation_setup, "Delegator", object)
        monkeypatch.setattr(
            provider_ledger, "DEFAULT_LEDGER_PATH", tmp_path / "state.json"
        )

        code = delegation_setup.main(["--available"])

        assert code == 0
        assert "--doctor" in capsys.readouterr().out
