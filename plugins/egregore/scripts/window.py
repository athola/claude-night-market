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
errors indefinitely in unattended sessions. That description is only
true from CLI 2.1.239 onward: before it, the watchdog retried
spend-limit 429s indefinitely too. Enabling it on an older CLI turns a
recoverable park into an unbounded wait, and a spend cap can be a month
out. So :func:`unattended_env` asks the version first, and treats not
knowing as a reason not to.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
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

#: First CLI version where the retry watchdog stops retrying a
#: spend-limit 429. Before it, the watchdog waits out a cap that may not
#: lift for weeks.
RETRY_WATCHDOG_MIN_VERSION = (2, 1, 239)

_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")

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
        if latest > moment:
            return latest
        # A stale reset says nothing about now, so it is not an answer.
        # It used to return one anyway, and returning None here skipped
        # the retry-after below: a response carrying both a reset header
        # from the previous window and a live retry-after was read as
        # "did not say", which parks the run for a fixed wait rather
        # than the one the response asked for.

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


def parse_cli_version(text: str) -> Optional[tuple[int, int, int]]:
    """Read the version out of ``claude --version``, or return None.

    The CLI prints something like ``2.1.241 (Claude Code)``. Anything
    that does not carry three numbers returns None, because a guessed
    version is worse than an admitted unknown: it is what decides
    whether a spend cap is waited out or refused.
    """
    match = _VERSION.search(text or "")
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def supports(
    version: Optional[tuple[int, int, int]],
    minimum: tuple[int, int, int],
) -> bool:
    """Say whether ``version`` is at least ``minimum``. Unknown is no."""
    return version is not None and version >= minimum


def unattended_env(
    env: Mapping[str, str],
    cli_version: Optional[tuple[int, int, int]] = None,
) -> dict[str, str]:
    """Return ``env`` with the retry watchdog on, where it is safe.

    ``CLAUDE_CODE_RETRY_WATCHDOG=1`` retries 429 and 529 capacity errors
    indefinitely, which is what an unattended run wants. From CLI 2.1.239
    it fails immediately on a spend-limit 429; before that it waited
    those out too, which can mean waiting until next month.

    So the variable is set only on a version known to be safe. An
    unknown version is left alone rather than assumed current: the cost
    of being wrong is a run that hangs instead of one that parks with a
    recorded reset instant the watchdog can act on. An operator who set
    the variable explicitly keeps their value either way.
    """
    updated = dict(env)
    if "CLAUDE_CODE_RETRY_WATCHDOG" in updated:
        return updated
    if supports(cli_version, RETRY_WATCHDOG_MIN_VERSION):
        updated["CLAUDE_CODE_RETRY_WATCHDOG"] = "1"
    return updated


#: Mechanism names :func:`plan_resume` chooses between.
WATCHDOG = "watchdog"
CRON = "cron"
NOTHING = "nothing"

#: How far ahead a session-only job is worth scheduling, in hours.
#: This is a judgment, not a documented limit. ``CronCreate`` jobs die
#: with the session, and holding one idle for longer than a day is a bet
#: rather than a plan. The tool's published 7-day expiry bounds the job,
#: not the session that carries it.
SESSION_JOB_HORIZON_HOURS = 24


@dataclass(frozen=True)
class ResumePlan:
    """Which mechanism will fire the resume, when, and why that one.

    Each mechanism pins the other two fields, so a plan cannot describe
    a resume nothing performs:

    ``WATCHDOG``
        A ``fire_at``, and no cron. The OS timer reads the cooldown.
    ``CRON``
        A ``fire_at`` and the cron expression that carries it.
    ``NOTHING``
        Neither. This is the shape that mattered: a ``NOTHING`` plan
        used to carry a real ``fire_at``, so a caller reading the time
        without first reading the mechanism scheduled against a
        mechanism that had already declined to schedule anything.
        ``why`` then says what to install to get one.
    """

    mechanism: str
    fire_at: Optional[datetime]
    cron: Optional[str]
    why: str

    def __post_init__(self) -> None:
        """Refuse a plan whose mechanism and fields disagree."""
        if self.mechanism not in (WATCHDOG, CRON, NOTHING):
            raise ValueError(f"unknown resume mechanism {self.mechanism!r}")
        if not self.why:
            raise ValueError("a resume plan must say why it chose its mechanism")
        if self.mechanism == NOTHING:
            if self.fire_at is not None or self.cron is not None:
                raise ValueError(
                    "a NOTHING plan schedules nothing, so it carries no "
                    f"fire_at and no cron: {self.fire_at!r} {self.cron!r}"
                )
            return
        if self.fire_at is None:
            raise ValueError(f"a {self.mechanism} plan needs a fire_at")
        if self.mechanism == CRON and not self.cron:
            raise ValueError("a CRON plan needs the cron expression that fires it")
        if self.mechanism == WATCHDOG and self.cron is not None:
            raise ValueError("a WATCHDOG plan is not carried by a cron expression")


def plan_resume(
    reset_at: datetime,
    *,
    session_survives: bool,
    watchdog_installed: bool,
    grace_minutes: int = 2,
    now: Optional[datetime] = None,
) -> ResumePlan:
    """Name the mechanism that can actually resume work at ``reset_at``.

    The choice is decided by the harness contract, not by preference.
    ``CronCreate`` schedules a prompt **inside the running session**: its
    own description says jobs "live only in this Claude session", that
    nothing is written to disk, that ``durable`` "has no effect", and
    that jobs fire only while the REPL is idle. None of that holds for
    the case this project cares about, which is a headless ``claude -p``
    night run stopping on a usage limit and exiting.

    So durability wins over precision. The OS timer behind
    ``watchdog.sh`` fires within one poll interval instead of on the
    instant, and it is the only option here that survives the session
    ending, the machine rebooting, or a weekly window that renews days
    from now.
    """
    moment = _now(now)
    fire_at = reset_at + timedelta(minutes=grace_minutes)

    if watchdog_installed:
        return ResumePlan(
            mechanism=WATCHDOG,
            fire_at=fire_at,
            cron=None,
            why=(
                "the OS timer reads budget.cooldown_until and survives the "
                "session exiting, the machine rebooting, and a window that "
                "renews days from now. It fires within one poll interval "
                "rather than on the instant, which is the price of that."
            ),
        )

    if not session_survives:
        return ResumePlan(
            mechanism=NOTHING,
            fire_at=None,
            cron=None,
            why=(
                "a CronCreate job lives only in the running session and is "
                "written to no disk, so it cannot outlive a headless run "
                "that exits on a usage limit. Install the watchdog "
                "(scripts/install_systemd.sh or scripts/install_launchd.sh) "
                "to get an unattended resume."
            ),
        )

    hours_out = (reset_at - moment).total_seconds() / 3600
    if hours_out > SESSION_JOB_HORIZON_HOURS:
        return ResumePlan(
            mechanism=NOTHING,
            fire_at=None,
            cron=None,
            why=(
                f"the window renews about {hours_out:.0f} hours out, which "
                "would outlive any session held open waiting for it. A "
                "weekly window needs the watchdog, not a session job."
            ),
        )

    return ResumePlan(
        mechanism=CRON,
        fire_at=fire_at,
        cron=cron_for(reset_at, grace_minutes),
        why=(
            "the session stays alive and idle until then, so a one-shot "
            "CronCreate fires inside it with context intact. It is lost if "
            "the session exits first."
        ),
    )
