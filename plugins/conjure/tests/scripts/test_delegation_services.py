"""Characterization tests for the service registry and credential checks.

Written green before ``delegation_executor.py`` was split, so the split
had a contract to keep. They pin behavior, not location: the import line
is the only thing that moved with the code.
"""

import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from delegation_executor import (  # noqa: E402 - sys.path set above
    ServiceConfig,
    _apply_overrides,
    _expired_credentials,
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

    def test_service_with_no_models_yields_none(self) -> None:
        """None means the CLI's own default applies, which is degradation rather than the KeyError the old table raised."""
        assert _smart_delegate_model(_api_key_service(), "large_context") is None
