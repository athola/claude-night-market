"""Decide between research passes whether to stop or search again.

The shape comes from OctoTools' context verifier (arXiv 2502.11271),
which after every step asks an LLM whether the memory is complete,
whether an unused tool could help, whether results conflict, whether a
tool limitation calls for verification, and whether anything is
ambiguous, then answers STOP or CONTINUE.

The judgment here is not the model's. VRR-Stop (arXiv 2607.17641)
measured a verifier's acceptance rate rising while true validity fell,
and arXiv 2607.24300 found self-authored verification unreliable in
self-improving agents. A research agent grading its own sufficiency is
that arrangement. So each criterion is read from records the agents did
not grade: the query log, the positive controls, and the frontier
verdict, which already separates a bad search from a thin field.

Each non-passing criterion names the channels it wants run again and
how: ``rerun`` the same queries after an outage, ``reformulate`` in
different vocabulary after a venue mismatch, or ``add`` a retrieval
channel that never looked. The pass budget bounds the loop. OctoTools
allowed ten steps and averaged 2.56 with GPT-4o. A pass here dispatches
up to four agents, so the default is two.
"""

from __future__ import annotations

from dataclasses import dataclass

from tome.channels.cards import CHANNEL_CARDS
from tome.models import ResearchSession
from tome.synthesis.frontier import (
    MISMATCH_SUSPECTED,
    THIN_CANDIDATE,
    canary_outcomes,
    frontier_verdict,
)
from tome.synthesis.quality import channel_outcomes

__all__ = [
    "CONTINUE",
    "DEFAULT_MAX_PASSES",
    "STOP",
    "Check",
    "ContextVerification",
    "verify_context",
]

STOP = "STOP"
CONTINUE = "CONTINUE"

DEFAULT_MAX_PASSES = 2

_CLEAN = ("ok", "empty")


@dataclass(frozen=True)
class Check:
    """One criterion's result and the evidence behind it."""

    criterion: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ContextVerification:
    """The decision, every check behind it, and the work it asks for.

    The action tuples stay populated on a budget STOP, so the report can
    say what the run left undone rather than implying it finished.
    """

    conclusion: str
    reason: str
    checks: tuple[Check, ...]
    rerun: tuple[str, ...]
    reformulate: tuple[str, ...]
    add: tuple[str, ...]


def _in_card_order(channels: set[str]) -> tuple[str, ...]:
    return tuple(card.name for card in CHANNEL_CARDS if card.name in channels)


def verify_context(
    session: ResearchSession,
    *,
    passes_run: int,
    max_passes: int = DEFAULT_MAX_PASSES,
) -> ContextVerification:
    """Return STOP or CONTINUE for ``session`` after ``passes_run`` passes.

    Criteria, each mapped from OctoTools' verifier prompt:

    ``completeness``
        Every dispatched channel searched cleanly (``ok`` or ``empty``).
        Anything else is rerun: an outage, a rate limit, a degraded
        fallback, or no record at all.
    ``verification``
        Every controlled channel that came back empty proved it could
        retrieve. A failed control, or an empty channel that ran none,
        is rerun: its silence carries no weight.
    ``ambiguity``
        The frontier verdict is not a suspected venue mismatch. OctoTools
        splits inconsistency from ambiguity. Here the one inconsistency
        the record can show is one venue full and another empty, which
        the frontier verdict already names, so the two are one check.
    ``unused_channels``
        A thin-field candidate was reached with every retrieval channel.
        Otherwise the missing retrieval channels are added. Generative
        channels are never added: they cannot testify about absence.
    ``budget``
        The pass budget did not cut off outstanding work.

    Raises:
        ValueError: When ``passes_run`` is below 1 or ``max_passes`` is
            below 1. The verifier runs after a pass, inside a budget of
            at least one, so either is a caller bug.
    """
    if passes_run < 1:
        raise ValueError(
            f"verify after a pass: passes_run must be >= 1, got {passes_run}"
        )
    if max_passes < 1:
        raise ValueError(f"max_passes must be >= 1, got {max_passes}")

    outcomes = channel_outcomes(session)
    controls = canary_outcomes(session)
    verdict = frontier_verdict(session)
    controlled = {card.name for card in CHANNEL_CARDS if card.controlled}

    unclean = {c for c in session.channels if outcomes.get(c, "unknown") not in _CLEAN}
    blind = {
        c
        for c, control in controls.items()
        if c in controlled
        and (control == "fail" or (control == "absent" and outcomes.get(c) == "empty"))
    }
    mismatched: set[str] = set()
    if verdict.verdict == MISMATCH_SUSPECTED:
        mismatched = {
            c
            for c, control in controls.items()
            if control == "pass" and outcomes.get(c) == "empty"
        }
    missing: set[str] = set()
    if verdict.verdict == THIN_CANDIDATE:
        missing = {
            card.name
            for card in CHANNEL_CARDS
            if card.kind == "retrieval" and card.name not in session.channels
        }

    rerun = _in_card_order(unclean | blind)
    reformulate = _in_card_order(mismatched)
    add = _in_card_order(missing)
    outstanding = rerun + reformulate + add
    exhausted = passes_run >= max_passes

    checks = (
        Check(
            "completeness",
            not unclean,
            ", ".join(
                f"{c} ({outcomes.get(c, 'unknown')})" for c in _in_card_order(unclean)
            )
            or "every dispatched channel searched cleanly",
        ),
        Check(
            "verification",
            not blind,
            ", ".join(f"{c} (control {controls[c]})" for c in _in_card_order(blind))
            or "no empty channel lacks a passing control",
        ),
        Check(
            "ambiguity",
            verdict.verdict != MISMATCH_SUSPECTED,
            verdict.reason,
        ),
        Check(
            "unused_channels",
            not missing,
            ", ".join(add) or "no retrieval channel left unused where it matters",
        ),
        Check(
            "budget",
            not (exhausted and outstanding),
            f"{passes_run} of {max_passes} pass(es) run",
        ),
    )

    if not outstanding:
        return ContextVerification(
            STOP, f"Nothing left to search: {verdict.verdict}.", checks, (), (), ()
        )
    todo = "; ".join(
        f"{action} {', '.join(channels)}"
        for action, channels in (
            ("rerun", rerun),
            ("reformulate", reformulate),
            ("add", add),
        )
        if channels
    )
    if exhausted:
        return ContextVerification(
            STOP,
            f"Pass budget spent with work outstanding: {todo}. Report these as gaps.",
            checks,
            rerun,
            reformulate,
            add,
        )
    return ContextVerification(
        CONTINUE, f"Pass {passes_run + 1}: {todo}.", checks, rerun, reformulate, add
    )
