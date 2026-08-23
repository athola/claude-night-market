"""Learning when a usage window renews, and scheduling the resume.

An unattended run that stops at 3am should restart the moment capacity
returns, and not a minute of the night earlier or an hour later.

**The constraint that shapes this module**: the reset semantics of the
5-hour window, and the weekly window's reset day, are **not publicly
documented**. The docs say usage "resets on a rolling five-hour window
and a weekly window" without saying whether the five hours roll from the
first message or from fixed clock boundaries. So nothing here computes a
reset time from an assumed window length. Every instant is read from
what the API actually returned, and when the response says nothing, this
module says it does not know.

What the API does return, and what is used here:

- ``retry-after``: seconds to wait. Present on a rate-limit 429.
- ``anthropic-ratelimit-{requests,tokens,input-tokens,output-tokens}-reset``:
  RFC 3339 instants. Capacity is back only when the latest of them has
  passed, so the latest wins.
- A spend-cap 429 carries **no** ``retry-after``. Its reset time is in
  the message prose: "You will regain access on 2026-09-01 at 00:00 UTC".
  It also carries ``error_code: enforced_spend_limit_reached``.

The reset instant is written into egregore's existing
``budget.cooldown_until``, which ``scripts/watchdog.sh`` already reads and
already refuses to relaunch during. So an accurate reset time is the
whole fix: the OS-level timer that egregore already installs becomes a
resume-at-renewal scheduler without any new scheduling machinery.

For the in-session case, Claude Code documents
``CLAUDE_CODE_RETRY_WATCHDOG=1``, which retries 429 and 529 capacity
errors indefinitely in unattended sessions but fails immediately on a
spend-limit 429. See :func:`unattended_env`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol

#: How long to wait when a limit was hit but nothing said when it lifts.
#: A named constant rather than a guess dressed as a computation: it is
#: an arbitrary retry interval, and calling it that is the honest thing.
UNKNOWN_RESET_WAIT_MINUTES = 30

#: Headers whose RFC 3339 value marks when one limit resets.
RESET_HEADERS = (
    "anthropic-ratelimit-tokens-reset",
    "anthropic-ratelimit-requests-reset",
    "anthropic-ratelimit-input-tokens-reset",
    "anthropic-ratelimit-output-tokens-reset",
)

_SPEND_MARKERS = ("enforced_spend_limit_reached", "reached your api usage limits")
_SPEND_TIME = re.compile(
    r"regain access on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2}:\d{2})\s*UTC",
    re.IGNORECASE,
)


class CooldownState(Protocol):
    """The two fields :func:`record_reset` writes.

    Naming the shape structurally is what lets the assignments below
    type-check. The parameter was previously ``object``, which every
    attribute write then had to suppress one at a time.
    ``budget.Budget`` satisfies this, and so would any later carrier of
    the same two fields.
    """

    last_rate_limit_at: Optional[str]
    cooldown_until: Optional[str]


def _now(now: Optional[datetime] = None) -> datetime:
    return now or datetime.now(timezone.utc)


def classify(text: str) -> Optional[str]:
    """Name what kind of refusal ``text`` describes.

    Returns ``"spend_limit"``, ``"rate_limit"``, ``"capacity"``, or None.
    The spend case is separated because it is the one the documented
    retry watchdog explicitly will not retry, and because waiting it out
    can mean waiting until next month rather than next hour.
    """
    low = text.lower()
    if any(marker in low for marker in _SPEND_MARKERS):
        return "spend_limit"
    if "529" in text or "overloaded" in low:
        return "capacity"
    if "429" in text or "rate_limit_error" in low or "rate limit" in low:
        return "rate_limit"
    return None


def _parse_rfc3339(value: str) -> Optional[datetime]:
    """Parse an RFC 3339 instant, returning None rather than raising."""
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_reset(
    headers: Mapping[str, str],
    text: str,
    now: Optional[datetime] = None,
) -> Optional[datetime]:
    """Read when capacity returns, or None when the response did not say.

    Order of preference: the reset headers (most precise), then
    ``retry-after``, then the spend-cap message prose. A reset already in
    the past is treated as no answer, because a stale header cannot tell
    us anything about now.
    """
    moment = _now(now)
    candidates = [
        parsed
        for name in RESET_HEADERS
        if (parsed := _parse_rfc3339(headers.get(name, ""))) is not None
    ]
    if candidates:
        latest = max(candidates)
        return latest if latest > moment else None

    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return moment + timedelta(seconds=int(float(retry_after)))
        except (TypeError, ValueError):
            pass

    match = _SPEND_TIME.search(text or "")
    if match:
        parsed = _parse_rfc3339(f"{match.group(1)}T{match.group(2)}:00Z")
        if parsed and parsed > moment:
            return parsed
    return None


def record_reset(
    budget: CooldownState,
    reset_at: Optional[datetime],
    now: Optional[datetime] = None,
) -> datetime:
    """Write the reset instant into the cooldown the watchdog reads.

    Returns the instant recorded. When ``reset_at`` is None the fallback
    is ``UNKNOWN_RESET_WAIT_MINUTES`` from now: an unattended run that
    stops forever because a header was missing is worse than one that
    tries again in half an hour.
    """
    moment = _now(now)
    resume_at = reset_at or moment + timedelta(minutes=UNKNOWN_RESET_WAIT_MINUTES)
    budget.last_rate_limit_at = moment.isoformat()
    budget.cooldown_until = resume_at.isoformat()
    return resume_at


def cron_for(reset_at: datetime, grace_minutes: int = 0) -> str:
    """Build a one-shot 5-field cron expression for the resume.

    ``grace_minutes`` nudges the fire time past the boundary. Firing at
    the exact reset instant risks a second refusal from a limit that has
    not quite lifted, and a refused relaunch costs another whole cycle.
    """
    fire = reset_at + timedelta(minutes=grace_minutes)
    return f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"


def unattended_env(env: Mapping[str, str]) -> dict[str, str]:
    """Return ``env`` with the documented unattended retry watchdog on.

    ``CLAUDE_CODE_RETRY_WATCHDOG=1`` retries 429 and 529 capacity errors
    indefinitely in unattended sessions, and fails immediately on a
    spend-limit 429. An operator who set it explicitly keeps their value.
    """
    updated = dict(env)
    updated.setdefault("CLAUDE_CODE_RETRY_WATCHDOG", "1")
    return updated
