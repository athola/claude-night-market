"""How a night-shift task reaches a verdict.

The separation this module enforces is the whole reason a night run can
be trusted in the morning: the party that writes the code has no vote on
whether the code is correct.

Three rules:

**The implementer's output is a log.** ``objective_check`` accepts it
only so callers can pass it without ceremony, and provably ignores it.
The test suite asserts that passing a boast changes nothing.

**The deterministic check can tighten, not loosen.** A babysitter PASS
over red evidence becomes FAIL. A babysitter FAIL over green evidence
becomes PASS with the objection recorded as ``dissent``, because a model
disagreeing with a passing test is a comment on the specification, and
specifications are a human's call in the morning, not a 3am block.

**A check that was supposed to fail and did not is blocking.** This is
Guard 2 of ``Skill(imbue:proof-of-work)`` module ``verifier-integrity``:
a check proven able to go red is the only kind whose green means
anything. Nothing downstream may proceed on an unproven guard.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import scope
from scope import ScopeResult


@dataclass(frozen=True)
class Objective:
    """The deterministic reading of a task's evidence."""

    ok: bool
    why: str
    #: True when the failure invalidates downstream greens rather than
    #: merely failing this attempt. A retry cannot fix it.
    blocking: bool = False


@dataclass(frozen=True)
class Verdict:
    """The reconciled outcome for one task attempt."""

    verdict: str
    reason: str
    dissent: bool = False


def objective_check(
    evidence: Mapping[str, Any],
    exit_code: int,
    output: str,
    diff_lines: int,
    cap: int,
    *,
    implementer_output: str | None = None,
) -> Objective:
    """Read a task's evidence deterministically.

    ``implementer_output`` is accepted and never read. It is a parameter
    rather than an omission so that a caller can hand over everything it
    has without deciding what is admissible, and so the exclusion is
    visible in the signature instead of implied by its absence. The test
    suite asserts that varying it changes nothing.
    """
    del implementer_output

    expect = evidence.get("expect", "pass")
    match = evidence.get("match")

    if expect == "fail" and exit_code == 0:
        return Objective(
            ok=False,
            why=(
                "the check did not fail when it was declared to fail. It does "
                "not guard what the task claims, so no later green from it "
                "means anything."
            ),
            blocking=True,
        )

    if expect == "pass" and exit_code != 0:
        return Objective(ok=False, why=f"expected a pass, exit code was {exit_code}")

    if match and match not in output:
        return Objective(ok=False, why=f"expected {match!r} in the output, absent")

    if diff_lines > cap:
        return Objective(
            ok=False,
            why=f"the diff is {diff_lines} lines, over the item's cap of {cap}",
        )

    return Objective(ok=True, why="")


def reconcile(
    babysitter: str,
    objective: Objective,
    babysitter_reason: str = "",
) -> Verdict:
    """Combine the babysitter's verdict with the deterministic reading."""
    if objective.blocking:
        return Verdict(verdict="BLOCKED", reason=objective.why)

    if babysitter == "BLOCKED":
        return Verdict(verdict="BLOCKED", reason=babysitter_reason)

    if babysitter == "PASS" and not objective.ok:
        return Verdict(
            verdict="FAIL",
            reason=f"babysitter passed it; overridden by evidence: {objective.why}",
        )

    if babysitter == "FAIL" and objective.ok:
        return Verdict(
            verdict="PASS",
            reason=(
                "evidence is green; babysitter dissent recorded for the morning: "
                f"{babysitter_reason}"
            ),
            dissent=True,
        )

    if not objective.ok:
        return Verdict(verdict="FAIL", reason=objective.why)

    return Verdict(verdict="PASS", reason=babysitter_reason)


def check_scope(allow_paths: Sequence[str], changed: Sequence[str]) -> ScopeResult:
    """Check changed paths against the item's allowlist and the denylist."""
    return scope.check(allow_paths, changed)


def babysitter_schema() -> dict[str, Any]:
    """JSON Schema the babysitter must answer with.

    Passed to ``claude --json-schema``, which forces a structured answer
    rather than prose a caller would have to parse. This is the mechanism
    herald already uses in ``hooks/double_shot_latte.py``.
    """
    return {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["PASS", "FAIL", "BLOCKED"]},
            "reason": {"type": "string"},
            "next_instruction": {"type": "string"},
        },
        "required": ["verdict", "reason"],
    }
