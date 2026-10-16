"""HTTP GET with the retry behavior research sources require.

arXiv, Semantic Scholar and Reddit all answer HTTP 429 to bursts, and on
2026-10-05 a whole academic channel came back empty because nothing
retried. A 429, a 503 or no response at all is retried after the server's
``Retry-After`` when it sends one, otherwise after an exponential backoff,
both capped. Any other status is final: a 403 block page does not clear by
waiting, and a URL that is not https is refused unsent.

Standard library only, so the channel agents can run it with no install.
"""

from __future__ import annotations

import http.client
import os
import time
import types
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from email.utils import parsedate_to_datetime
from typing import Any

OK = 200
TOO_MANY_REQUESTS = 429
NO_RESPONSE = 0
# The request was never sent: the URL, or a redirect, named a scheme other
# than https. Waiting does not change the URL, so it is not retried.
REFUSED = -1
# A timeout or reset (NO_RESPONSE) clears on its own as often as a 429 does.
RETRYABLE = frozenset({NO_RESPONSE, TOO_MANY_REQUESTS, 503})
_BASE_BACKOFF = 2.0
# Longest single wait. A Retry-After of an hour would stall the whole
# research run, so a longer one is cut to this and the request retried.
# When the retries run out, the 429 is returned.
MAX_WAIT = 30.0


@dataclass(frozen=True)
class Response:
    """One HTTP answer.

    ``status`` NO_RESPONSE means the request got no answer and REFUSED that
    it was never sent. ``error`` says why, and is set for those two only.
    """

    status: int
    body: str
    # Read-only view, so a frozen Response cannot change through it.
    # A mapping does not hash, so it is left out of the hash.
    headers: Mapping[str, str] = field(hash=False)
    attempts: int = 1
    error: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "headers", types.MappingProxyType(dict(self.headers)))
        if (self.status in (NO_RESPONSE, REFUSED)) != bool(self.error):
            raise ValueError(
                f"status {self.status} with error {self.error!r}: error text "
                "belongs to NO_RESPONSE and REFUSED only"
            )


Transport = Callable[[str, Mapping[str, str]], Response]


def user_agent() -> str:
    """Name the tool and, when set, a contact address.

    OpenAlex, Unpaywall and arXiv all ask for a contact so they can reach
    a client before throttling it.
    """
    contact = os.environ.get("TOME_CONTACT_EMAIL")
    suffix = f" (mailto:{contact})" if contact else ""
    return f"tome-research/1.0{suffix}"


# Headers that authenticate the caller to one service. A redirect to
# another host must not carry them: the Semantic Scholar key would reach
# whoever the API redirected to.
_CREDENTIAL_HEADERS = frozenset({"x-api-key", "authorization", "cookie"})


_DEFAULT_PORTS = {"https": 443, "http": 80}


def _origin(url: str) -> tuple[str, str | None, int | None]:
    """Scheme, host and port: the service a credential header belongs to.

    Another port on the same host can be another service, so a redirect
    there is treated like one to another host.
    """
    parts = urllib.parse.urlsplit(url)
    return (
        parts.scheme,
        parts.hostname,
        parts.port or _DEFAULT_PORTS.get(parts.scheme),
    )


class _RefusedSchemeError(urllib.error.URLError):
    """A URL or redirect target that is not https."""


def _refusal(url: str) -> str | None:
    scheme = urllib.parse.urlsplit(url).scheme
    if scheme == "https":
        return None
    return f"refused {scheme or 'scheme-less'} URL: only https is fetched"


class _CredentialSafeRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects, dropping credential headers when the origin changes."""

    def redirect_request(  # noqa: PLR0913 - signature fixed by urllib's override
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        refused = _refusal(newurl)
        if refused:
            # No handler would answer it: urllib's open() returns None.
            raise _RefusedSchemeError(refused)
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return None
        if _origin(new.full_url) != _origin(req.full_url):
            for name in list(new.headers):
                if name.lower() in _CREDENTIAL_HEADERS:
                    del new.headers[name]
        return new


def _https_only_opener() -> urllib.request.OpenerDirector:
    """An opener with an https handler and nothing for file:, ftp: or data:.

    Same construction as scripts/verify_canaries.py, for the same reason:
    a URL edited to a local path must fail rather than read a file. The
    redirect handler raises on a redirect to any other scheme, since no
    handler here would answer it.
    """
    director = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.HTTPSHandler(),
        _CredentialSafeRedirect(),
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        director.add_handler(handler)
    # Headers travel on the Request, never in addheaders: urllib applies
    # addheaders to every request the opener sends, redirect targets on
    # other hosts included, and no redirect handler can strip them.
    director.addheaders = []
    return director


def urllib_transport(
    url: str, headers: Mapping[str, str], timeout: float = 30.0
) -> Response:
    """Fetch over https, returning HTTP error statuses instead of raising."""
    refused = _refusal(url)
    if refused:
        return Response(REFUSED, "", {}, error=refused)
    try:
        request = urllib.request.Request(url, headers=dict(headers))  # noqa: S310 - opener has only an https handler, file: and ftp: fail
        with _https_only_opener().open(request, timeout=timeout) as reply:
            body = reply.read().decode("utf-8", errors="replace")
            return Response(reply.status, body, dict(reply.headers))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return Response(exc.code, body, dict(exc.headers or {}))
    except _RefusedSchemeError as exc:
        return Response(REFUSED, "", {}, error=str(exc.reason))
    # URLError and TimeoutError are OSErrors.
    except (OSError, http.client.HTTPException) as exc:
        return Response(NO_RESPONSE, "", {}, error=str(exc) or type(exc).__name__)


def _retry_after(headers: Mapping[str, str]) -> float | None:
    """Seconds named by a Retry-After header, as delta or HTTP date."""
    value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
    if value is None:
        return None
    value = value.strip()
    if value.isascii() and value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - time.time())


def fetch(  # noqa: PLR0913 - transport, sleep and clock are test seams
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    retries: int = 3,
    transport: Transport = urllib_transport,
    sleep: Callable[[float], None] = time.sleep,
    deadline: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Response:
    """GET ``url``, retrying a 429, a 503 or no response up to ``retries`` times.

    No response covers a timeout or a reset. With ``deadline``, a time on
    ``clock``, a wait that would end past it is not started and the last
    reply is returned instead.
    """
    sent = {"User-Agent": user_agent(), **dict(headers or {})}
    attempt = 0
    while True:
        attempt += 1
        reply = transport(url, sent)
        if reply.status not in RETRYABLE or attempt > retries:
            return replace(reply, attempts=attempt)
        named = _retry_after(reply.headers)
        delay = named if named is not None else _BASE_BACKOFF * 2 ** (attempt - 1)
        wait = min(delay, MAX_WAIT)
        if deadline is not None and clock() + wait > deadline:
            return replace(reply, attempts=attempt)
        sleep(wait)
