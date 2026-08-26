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
from pathlib import Path

import pytest
from scripts.delegation_setup import ProviderState, write_ledger
from scripts.provider_ledger import (
    LEDGER_VERSION,
    ProviderLedger,
    ProviderRecord,
)


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
