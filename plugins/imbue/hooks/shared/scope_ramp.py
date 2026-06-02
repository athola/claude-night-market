"""Scope-ramp guard logic: couple increment size to demonstrated competence.

A coding agent that one-shots a large change hands back a diff the
human cannot verify, the failure the research calls blind trust. The
fix the learning sciences and five apprenticeship domains converged on
is graduated practice: start at the smallest intentional increment and
ramp ambition up a notch only after the prior increment's understanding
is demonstrated and recorded (see
docs/research/3dfdba53-graduated-implementation.md).

This module holds the pure decision logic so it can be unit-tested
without hook plumbing or disk. The hook wrapper
(``guard_scope_ramp.py``) handles stdin, session state, and the
ramp-token file; everything here is a pure function of its arguments.

The model:

  - ``rung`` is the current ambition tier, measured as the maximum
    number of lines a single increment may add. It starts bounded
    (``RUNG_START``) and grows by ``RAMP_FACTOR`` up to ``RUNG_CAP``.
  - The rung only widens when a *ramp token* is present. The token is
    minted out-of-band when a demonstration of the prior increment is
    recorded (a tradeoff-ledger entry plus, for high-stakes work, the
    human explaining the diff unaided: the magenta hand-fly check).
    You cannot ramp by simply writing more; you ramp by proving you
    understood the last slice. This is the clean-record gate (GDL) and
    the four-eyes anti-gaming device.
  - High-stakes paths (auth, migrations, payments, infra, crypto) get a
    halved effective rung, so they force a demonstration sooner. This
    is the hybrid-by-stakes gate.
"""

from __future__ import annotations

import re

__all__ = [
    "RAMP_FACTOR",
    "RUNG_CAP",
    "RUNG_START",
    "added_lines",
    "assess_ramp",
    "is_high_stakes",
    "ledger_entry",
    "stakes_for",
]

# The bounded starting increment: ~40 added lines is a slice a human can
# read and explain in one sitting. Below the 85%-band intent: small
# enough that understanding keeps pace with output.
RUNG_START = 40
# Ramp one notch per recorded demonstration. 1.5x is a notch, not a leap.
RAMP_FACTOR = 1.5
# Even a well-understood ladder tops out: a single increment past this is
# unreviewable regardless of demonstrated competence.
RUNG_CAP = 200

# The rung divisor per leyline risk tier (GREEN/YELLOW/RED/CRITICAL).
# GREEN/YELLOW keep the full rung; RED halves it and CRITICAL quarters it,
# so higher-stakes work forces a demonstration sooner. The tier scale is
# the same one leyline:risk-classification assigns, so the gate is driven
# by the project's authoritative risk signal, not by path-regex alone.
_RUNG_DIVISOR_BY_TIER = {"GREEN": 1, "YELLOW": 1, "RED": 2, "CRITICAL": 4}
_EXPLANATION_TIERS = frozenset({"RED", "CRITICAL"})

_HIGH_STAKES_RE = re.compile(
    r"(auth|login|password|credential|secret|token|crypto|"
    r"migrat|payment|billing|invoice|charge|"
    r"infra|terraform|k8s|kubernetes|deploy|"
    r"security|permission|access[_-]?control)",
    re.IGNORECASE,
)


def added_lines(tool_name: str, tool_input: dict) -> int:
    """Return the number of lines the tool call would add.

    Write counts its content; Edit counts its new_string; MultiEdit sums
    each edit's new_string. Any other tool is zero (the guard only gates
    code-writing tools). This is a deliberate over-estimate of net change
    (it does not subtract removed lines): the question is how much new
    code the human must take on, and a rewrite is as much to verify as an
    addition.
    """
    if tool_name == "Write":
        return _count_lines(tool_input.get("content", ""))
    if tool_name == "Edit":
        return _count_lines(tool_input.get("new_string", ""))
    if tool_name == "MultiEdit":
        return sum(
            _count_lines(edit.get("new_string", ""))
            for edit in tool_input.get("edits", [])
        )
    return 0


def _count_lines(text: str) -> int:
    """Count non-empty logical lines in *text*."""
    if not text:
        return 0
    return len(text.splitlines())


def is_high_stakes(file_path: str) -> bool:
    """Return True when the path matches a high-blast-radius area."""
    return bool(_HIGH_STAKES_RE.search(file_path or ""))


def stakes_for(file_path: str, explicit: str | None = None) -> str:
    """Resolve the risk tier for an increment.

    An *explicit* tier (from ``leyline:risk-classification``, passed via
    the hook's ``IMBUE_STAKES`` signal) is authoritative and wins over
    the path guess, since the project's risk classifier sees more than a
    filename. An unrecognized explicit value falls back to the path
    heuristic: a high-stakes path is RED, everything else GREEN.
    """
    if explicit:
        tier = explicit.strip().upper()
        if tier in _RUNG_DIVISOR_BY_TIER:
            return tier
    return "RED" if is_high_stakes(file_path) else "GREEN"


def _effective_rung(rung: int, tier: str) -> int:
    """Return the effective rung, divided by the tier's stakes divisor."""
    divisor = _RUNG_DIVISOR_BY_TIER.get(tier, 1)
    return max(1, rung // divisor)


def assess_ramp(
    added: int,
    file_path: str,
    state: dict,
    *,
    ramp_token: bool,
    stakes: str | None = None,
) -> tuple[dict | None, dict]:
    """Decide whether *added* lines stay within the current rung.

    Returns ``(finding, new_state)``. ``finding`` is None when the
    increment is within the effective rung; otherwise it is a dict with
    ``kind``, ``stakes`` (the risk tier), ``high_stakes`` (tier in RED or
    CRITICAL, kept for back-compat), and ``detail``. ``new_state`` always
    carries the (possibly widened) rung and the bumped increment count,
    so the caller can persist it.

    *stakes* is an authoritative risk tier from
    ``leyline:risk-classification``; when None the tier is derived from
    the file path. A ramp token, if present, widens the rung *before* the
    check: the bigger slice is earned by the recorded demonstration that
    minted the token, not by the act of writing more.
    """
    rung = int(state.get("rung", RUNG_START))
    increments = int(state.get("increments", 0))

    if ramp_token:
        rung = min(int(round(rung * RAMP_FACTOR)), RUNG_CAP)

    tier = stakes_for(file_path, stakes)
    high_stakes = tier in _EXPLANATION_TIERS
    effective = _effective_rung(rung, tier)

    new_state = {"rung": rung, "increments": increments + 1}

    if added <= effective:
        return None, new_state

    finding = {
        "kind": "over-rung",
        "stakes": tier,
        "high_stakes": high_stakes,
        "detail": _format_detail(added, effective, high_stakes),
    }
    return finding, new_state


def ledger_entry(
    *,
    increment: int,
    rung_before: int,
    rung_after: int,
    tier: str,
    timestamp: str,
) -> dict:
    """Build one ramp-ledger record for a notch climbed.

    The record names the increment, the rung on either side of the
    notch, the risk tier, the gate that applied (explanation for RED or
    CRITICAL, evidence otherwise), and when it happened. The caller
    supplies *timestamp* so this stays a pure function; the hook appends
    the record to the local ledger and the human promotes it to
    ``leyline:decision-journal``. See module ``ramp-ledger.md``.
    """
    gate = "explanation" if tier in _EXPLANATION_TIERS else "evidence"
    return {
        "increment": increment,
        "rung_before": rung_before,
        "rung_after": rung_after,
        "stakes": tier,
        "gate": gate,
        "timestamp": timestamp,
    }


def _format_detail(added: int, effective: int, high_stakes: bool) -> str:
    """Build the human-facing reason for an over-rung increment."""
    head = (
        f"increment adds {added} lines, past the current rung of "
        f"{effective}. Bound it to ~{effective} lines (start with the "
        f"smallest intentional slice)"
    )
    if high_stakes:
        remedy = (
            ", or demonstrate the prior increment: explain its diff "
            "unaided and record a tradeoff-ledger entry, then `touch "
            ".imbue/ramp-ok` to ramp the rung a notch. High-stakes path: "
            "the explanation is required, not optional."
        )
    else:
        remedy = (
            ", or record evidence the prior increment is understood "
            "(green tests plus a tradeoff-ledger entry), then `touch "
            ".imbue/ramp-ok` to ramp the rung a notch."
        )
    return head + remedy
