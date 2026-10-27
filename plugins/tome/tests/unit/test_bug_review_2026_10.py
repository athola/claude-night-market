"""Regression tests for defects found in the 2026-10 bug review."""

from __future__ import annotations

import http.client
import json
from pathlib import Path

import pytest
from hooks._session_utils import load_active_session

from tome.channels import http as tome_http
from tome.channels.academic import _extract_arxiv_id
from tome.scripts import verify_canaries


@pytest.fixture
def sessions(tmp_path: Path) -> Path:
    directory = tmp_path / "sessions"
    directory.mkdir()
    return directory


@pytest.mark.unit
@pytest.mark.parametrize("text", ["[]", "null", '"active"', "42"])
def test_load_active_session_ignores_non_object_json(sessions, text) -> None:
    (sessions / "s.json").write_text(text)

    assert load_active_session(sessions) is None


@pytest.mark.unit
def test_load_active_session_ignores_binary_garbage(sessions) -> None:
    (sessions / "s.json").write_bytes(b"\xff\xfe\x00\x80")

    assert load_active_session(sessions) is None


@pytest.mark.unit
def test_load_active_session_counts_null_findings_as_zero(sessions) -> None:
    (sessions / "s.json").write_text(
        json.dumps({"status": "active", "topic": "t", "findings": None})
    )

    assert load_active_session(sessions) == ("t", 0)


class _Opener:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def open(self, *_args, **_kwargs):
        raise self._error


@pytest.mark.unit
@pytest.mark.parametrize(
    "error",
    [http.client.IncompleteRead(b"x"), http.client.BadStatusLine("junk")],
)
def test_transport_reports_http_protocol_errors_as_no_response(
    monkeypatch, error
) -> None:
    monkeypatch.setattr(tome_http, "_https_only_opener", lambda: _Opener(error))

    reply = tome_http.urllib_transport("https://example.org/", {})

    assert reply.status == tome_http.NO_RESPONSE


@pytest.mark.unit
def test_retry_after_ignores_non_ascii_digits() -> None:
    assert tome_http._retry_after({"Retry-After": "\u00b2"}) is None


@pytest.mark.unit
def test_arxiv_id_for_old_style_solv_int_category() -> None:
    assert (
        _extract_arxiv_id("http://arxiv.org/abs/solv-int/9701001v1")
        == "solv-int/9701001"
    )


@pytest.mark.unit
def test_canary_run_does_not_claim_all_verified_when_rate_limited(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(verify_canaries, "_fetch", lambda _url: (429, ""))
    monkeypatch.setattr(verify_canaries, "_PAUSE", 0.0)

    verify_canaries.main()

    assert "All targets verified" not in capsys.readouterr().out
