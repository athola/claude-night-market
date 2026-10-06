"""HTTP GET with the retry behavior research sources require.

arXiv, Semantic Scholar and Reddit all answer HTTP 429 to bursts, and on
2026-10-05 a whole academic channel came back empty because nothing
retried. A 429 or 503 is retried after the server's ``Retry-After`` when it
sends one, otherwise after an exponential backoff, both capped. Any other
status is final: a 403 block page does not clear by waiting.

Standard library only, so the channel agents can run it with no install.
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

OK = 200
TOO_MANY_REQUESTS = 429
NO_RESPONSE = 0
# A timeout or reset (NO_RESPONSE) clears on its own as often as a 429 does.
RETRYABLE = frozenset({NO_RESPONSE, TOO_MANY_REQUESTS, 503})
_BASE_BACKOFF = 2.0
# Longest single wait. A Retry-After of an hour would stall the whole
# research run; past this, the source is reported as rate-limited.
MAX_WAIT = 30.0


@dataclass(frozen=True)
class Response:
    """One HTTP answer. ``status`` NO_RESPONSE means the request never got one."""

    status: int
    body: str
    headers: Mapping[str, str]
    attempts: int = 1
    error: str = field(default="", compare=False)


Transport = Callable[[str, Mapping[str, str]], Response]


def user_agent() -> str:
    """Name the tool and, when set, a contact address.

    OpenAlex, Unpaywall and arXiv all ask for a contact so they can reach
    a client before throttling it.
    """
    contact = os.environ.get("TOME_CONTACT_EMAIL")
    suffix = f" (mailto:{contact})" if contact else ""
    return f"tome-research/1.0{suffix}"


def _https_only_opener(headers: Mapping[str, str]) -> urllib.request.OpenerDirector:
    """An opener with an https handler and nothing for file:, ftp: or data:.

    Same construction as scripts/verify_canaries.py, for the same reason:
    a URL edited to a local path must fail rather than read a file. The
    redirect handler follows https redirects only, since no other scheme
    has a handler.
    """
    director = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.HTTPSHandler(),
        urllib.request.HTTPRedirectHandler(),
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        director.add_handler(handler)
    # On the director, not a per-call Request, so no URL object is built
    # outside the https-only handler set.
    director.addheaders = list(headers.items())
    return director


def urllib_transport(
    url: str, headers: Mapping[str, str], timeout: float = 30.0
) -> Response:
    """Fetch over https, returning HTTP error statuses instead of raising."""
    try:
        with _https_only_opener(headers).open(url, timeout=timeout) as reply:
            body = reply.read().decode("utf-8", errors="replace")
            return Response(reply.status, body, dict(reply.headers))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return Response(exc.code, body, dict(exc.headers or {}))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return Response(NO_RESPONSE, "", {}, error=str(exc))


def _retry_after(headers: Mapping[str, str]) -> float | None:
    """Seconds named by a Retry-After header, as delta or HTTP date."""
    value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, when.timestamp() - time.time())


def fetch(
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    retries: int = 3,
    transport: Transport = urllib_transport,
    sleep: Callable[[float], None] = time.sleep,
) -> Response:
    """GET ``url``, retrying a 429 or 503 up to ``retries`` times."""
    sent = {"User-Agent": user_agent(), **dict(headers or {})}
    attempt = 0
    while True:
        attempt += 1
        reply = transport(url, sent)
        if reply.status not in RETRYABLE or attempt > retries:
            return Response(
                reply.status, reply.body, reply.headers, attempt, reply.error
            )
        named = _retry_after(reply.headers)
        delay = named if named is not None else _BASE_BACKOFF * 2 ** (attempt - 1)
        sleep(min(delay, MAX_WAIT))
