"""Characterization tests for provider verification after its extraction.

The behavior was pinned through Delegator.verify_service before the move;
these import ``delegation_verify`` directly so deleting the module turns
them red.
"""

import sys
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_services import ServiceConfig  # noqa: E402 - sys.path set above
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
