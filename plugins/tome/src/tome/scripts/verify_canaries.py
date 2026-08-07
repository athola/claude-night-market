"""Re-verify the canary targets (``make verify-canaries``).

The three canary targets in :mod:`tome.channels.canary` are third-party
documents. From inside the verdict, a target that moved and a channel
that broke look identical: the control did not come back. They call for
opposite actions. A moved target means edit ``canary.py``. A broken
channel means every recent session using it is suspect.

So this classifies four ways, and only two are defects:

``RETRIEVED``       the expected document came back
``TARGET_MOVED``    the channel answered cleanly, the document was absent
``CHANNEL_ERROR``   transport failure, 5xx, or an unparseable body
``RATE_LIMITED``    a 429, which is not a verdict about anything

Not a pytest. Two reasons. A test's binary pass/fail collapses exactly
the distinction this job exists to draw, so a red test would say
"something is wrong with a canary" and leave the operator to work out
which of two unrelated remedies applies. And tome's pytest config
carries no ``-m "not network"`` default, so a network-marked test would
run in CI and redden the suite on any third-party hiccup.

This is the one module under ``src/tome/`` that performs network I/O.
That is a deliberate, contained exception: it lives in ``scripts/``,
nothing on the synthesis path imports it, and the classifier it wraps
is pure and offline-testable.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

from tome.channels.canary import CANARY_TARGETS, describe_canary_target

__all__ = [
    "CHANNEL_ERROR",
    "RETRIEVED",
    "RATE_LIMITED",
    "TARGET_MOVED",
    "CanaryOutcome",
    "classify_canary_response",
    "exit_code_for",
    "main",
]

RETRIEVED = "RETRIEVED"
TARGET_MOVED = "TARGET_MOVED"
CHANNEL_ERROR = "CHANNEL_ERROR"
RATE_LIMITED = "RATE_LIMITED"

# Outcomes that require someone to do something.
_DEFECTS = (TARGET_MOVED, CHANNEL_ERROR)

# Seconds between fetches. tome has no rate limiting anywhere, and
# Semantic Scholar returned 429 during the original target
# verification, so the pause is the only throttle there is.
_PAUSE = 3.0


@dataclass(frozen=True)
class CanaryOutcome:
    """What the control did, and what the operator should do about it."""

    channel: str
    result: str
    detail: str
    remedy: str


def _expected_marker(channel: str) -> str:
    """The string that must appear for the target to count as retrieved."""
    return {
        "academic": "Attention Is All You Need",
        "code": "torvalds/linux",
        "discourse": "Y Combinator",
    }[channel]


def _answered_cleanly(channel: str, body: str) -> bool:
    """Did the service return a well-formed, understood response?

    Distinguishing this from "returned the target" is the whole job. A
    body we cannot parse is a broken channel. A body we parse fine that
    lacks the document is a moved target.
    """
    if channel == "academic":
        return "<feed" in body or "<entry>" in body
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return False
    if channel == "code":
        return isinstance(data, dict) and "total_count" in data
    return isinstance(data, dict) and "hits" in data


def classify_canary_response(channel: str, *, status: int, body: str) -> CanaryOutcome:
    """Classify one canary fetch. Pure: no network, no clock."""
    if status == 429:
        return CanaryOutcome(
            channel,
            RATE_LIMITED,
            "the service throttled us",
            "Retry later. A rate limit says nothing about the target or "
            "the channel, so this does not fail the job.",
        )
    if status != 200:
        return CanaryOutcome(
            channel,
            CHANNEL_ERROR,
            f"HTTP {status}",
            f"Investigate the {channel} channel. Sessions that used it "
            "recently could not have been retrieving reliably.",
        )
    if not _answered_cleanly(channel, body):
        return CanaryOutcome(
            channel,
            CHANNEL_ERROR,
            "response body was not the shape this service returns",
            f"Investigate the {channel} channel or its endpoint. An "
            "unparseable body is not evidence a document moved, so do "
            "not edit the target for it.",
        )
    if _expected_marker(channel) in body:
        return CanaryOutcome(channel, RETRIEVED, "target retrieved", "None.")
    return CanaryOutcome(
        channel,
        TARGET_MOVED,
        "service answered cleanly, target document absent",
        "Update the url and verified_on for this channel in "
        "src/tome/channels/canary.py. The channel is working; the "
        "document it was pointed at is not where it was.",
    )


def exit_code_for(results: list[str]) -> int:
    """Nonzero only when a human has to act.

    A rate limit is excluded deliberately. A job that reddened on
    throttling would train its operator to rerun until green, which is
    how a real defect gets rerun away.
    """
    return 1 if any(r in _DEFECTS for r in results) else 0


def _https_only_opener() -> urllib.request.OpenerDirector:
    """An opener that can speak https and nothing else.

    The default ``urlopen`` handles ``file:``, ``ftp:`` and ``data:``
    too, so a canary target edited to a local path would read as a
    passing control while touching no network: a control vouching for a
    channel it never contacted. That is worse than a missing control,
    because it looks like evidence.

    Built handler by handler rather than with ``build_opener``, which
    keeps the default ``FileHandler`` even when passed an
    ``HTTPSHandler``. Verified rather than assumed: this director
    returns ``None`` for a ``file://`` URL, while
    ``build_opener(HTTPSHandler())`` reads the file.
    """
    director = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.HTTPSHandler(),
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        director.add_handler(handler)
    # Headers belong on the director rather than on a per-call Request.
    # GitHub's API rejects requests without a User-Agent, and building a
    # Request per fetch would reintroduce the arbitrary-scheme surface
    # this function exists to remove.
    director.addheaders = [("User-Agent", "tome-canary-check")]
    return director


_OPENER = _https_only_opener()


def _fetch(url: str) -> tuple[int, str]:
    """Fetch one canary URL over https.

    The scheme is checked as well as structurally excluded. The opener
    would decline a bad target quietly by returning ``None``, which
    surfaces downstream as an empty read and classifies as
    CHANNEL_ERROR, sending a maintainer after a channel that is fine.
    Raising here names the real problem instead.
    """
    if urlparse(url).scheme != "https":
        raise ValueError(
            f"canary target must be https, got {url!r}. A non-https target "
            "could resolve to a local file and pass a control without "
            "reaching the channel it claims to vouch for."
        )
    try:
        with _OPENER.open(url, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, f"transport failure: {exc}"


def main() -> int:
    outcomes: list[CanaryOutcome] = []
    for i, channel in enumerate(sorted(CANARY_TARGETS)):
        if i:
            time.sleep(_PAUSE)
        status, body = _fetch(CANARY_TARGETS[channel].url)
        outcomes.append(classify_canary_response(channel, status=status, body=body))

    print("Canary target re-verification")
    print("=" * 60)
    for outcome in outcomes:
        print(f"\n{outcome.channel:<12} {outcome.result}")
        print(f"  url      {CANARY_TARGETS[outcome.channel].url}")
        print(f"  detail   {outcome.detail}")
        print(f"  expected {describe_canary_target(outcome.channel)}")
        if outcome.result != RETRIEVED:
            print(f"  remedy   {outcome.remedy}")

    code = exit_code_for([o.result for o in outcomes])
    print(
        "\nAll targets verified."
        if not code
        else "\nAt least one target moved or one channel is broken. See remedies."
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
