"""Credential headers must not follow a redirect to another host.

The Semantic Scholar key travels as ``x-api-key``. urllib re-applies an
opener's ``addheaders`` to every request it sends and copies a request's
own headers onto the redirected one, so either way a 302 to another host
received the key. These tests drive a real redirect through the opener,
with a fake https handler standing in for the network.
"""

from __future__ import annotations

import email.message
import io
import urllib.request
import urllib.response

import pytest

from tome.channels import http


class _FakeHttps(urllib.request.HTTPSHandler):
    """Answer the first request with a redirect, then 200; record headers.

    Subclasses the real handler so urllib's request preprocessing, which
    is where an opener's addheaders are applied, still runs.
    """

    def __init__(self, location: str) -> None:
        super().__init__()
        self.location = location
        self.seen: list[tuple[str, dict[str, str]]] = []

    def https_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        # header_items() includes the opener's addheaders, which urllib adds
        # as unredirected headers before the handler sees the request.
        sent = {name.lower(): value for name, value in req.header_items()}
        self.seen.append((req.full_url, sent))
        headers = email.message.Message()
        if len(self.seen) == 1:
            headers["Location"] = self.location
            code, msg = 302, "Found"
        else:
            code, msg = 200, "OK"
        reply = urllib.response.addinfourl(
            io.BytesIO(b"{}"), headers, req.full_url, code
        )
        reply.msg = msg
        return reply


def _run(
    monkeypatch: pytest.MonkeyPatch,
    location: str,
    headers: dict[str, str] | None = None,
) -> list[tuple[str, dict[str, str]]]:
    fake = _FakeHttps(location)
    monkeypatch.setattr(http.urllib.request, "HTTPSHandler", lambda: fake)
    reply = http.urllib_transport(
        "https://api.semanticscholar.org/graph/v1/paper/search?query=x",
        headers or {"User-Agent": "tome-test", "x-api-key": "secret-key"},
    )
    assert reply.status == http.OK
    return fake.seen


@pytest.mark.unit
def test_api_key_is_dropped_on_redirect_to_another_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 302 to a different host gets no x-api-key."""
    seen = _run(monkeypatch, "https://attacker.example/collect")

    assert seen[0][1]["x-api-key"] == "secret-key"
    assert seen[1][0] == "https://attacker.example/collect"
    assert "x-api-key" not in seen[1][1]
    assert seen[1][1]["user-agent"] == "tome-test"


@pytest.mark.unit
def test_api_key_is_kept_on_redirect_within_the_same_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A redirect that stays on the API host still authenticates."""
    seen = _run(
        monkeypatch, "https://api.semanticscholar.org/graph/v1/paper/search?q=y"
    )

    assert seen[1][1]["x-api-key"] == "secret-key"


@pytest.mark.unit
def test_api_key_is_dropped_on_redirect_to_another_port_on_the_same_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A different port is a different service, so it gets no key."""
    seen = _run(
        monkeypatch, "https://api.semanticscholar.org:8443/graph/v1/paper/search"
    )

    assert seen[1][0].startswith("https://api.semanticscholar.org:8443/")
    assert "x-api-key" not in seen[1][1]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("header", "value"), [("Authorization", "Bearer secret"), ("Cookie", "s=secret")]
)
def test_authorization_and_cookie_are_dropped_on_redirect_to_another_host(
    monkeypatch: pytest.MonkeyPatch, header: str, value: str
) -> None:
    """Every credential header is stripped, not only x-api-key."""
    seen = _run(
        monkeypatch,
        "https://attacker.example/collect",
        {"User-Agent": "tome-test", header: value},
    )

    assert seen[0][1][header.lower()] == value
    assert header.lower() not in seen[1][1]
    assert seen[1][1]["user-agent"] == "tome-test"


@pytest.mark.unit
def test_api_key_is_kept_when_redirect_names_the_default_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """:443 on https is the same service as no port at all."""
    seen = _run(
        monkeypatch, "https://api.semanticscholar.org:443/graph/v1/paper/search"
    )

    assert seen[1][1]["x-api-key"] == "secret-key"


@pytest.mark.unit
def test_redirect_request_declines_when_urllib_declines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    GIVEN urllib's base handler returns None, its documented way to say
          it will not follow a redirect
    WHEN the credential-safe handler is asked for the redirected request
    THEN it passes None through instead of touching a missing request
    """
    monkeypatch.setattr(
        urllib.request.HTTPRedirectHandler,
        "redirect_request",
        lambda self, req, fp, code, msg, headers, newurl: None,
    )
    handler = http._CredentialSafeRedirect()
    original = urllib.request.Request("https://api.example.com/x")

    declined = handler.redirect_request(
        original, None, 302, "Found", {}, "https://other.example.com/y"
    )

    assert declined is None
