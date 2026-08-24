"""How a night-shift task reaches a verdict.

The separation this module enforces is the whole reason a night run can
be trusted in the morning: the party that writes the code has no vote on
whether the code is correct.

Three rules:

**The implementer's output is a log.** ``objective_check`` accepts it
only so callers can pass it without ceremony, and provably ignores it.
The test suite asserts that passing a boast changes nothing.

**Past a block, the evidence decides.** Not "the check can tighten,
not loosen", which is what this said and is not what it does. A
babysitter PASS over red evidence becomes FAIL, which is tightening. A
babysitter FAIL over green evidence becomes PASS with the objection
recorded as ``dissent``, which is loosening, and is deliberate: a model
disagreeing with a passing test is a comment on the specification, and
specifications are a human's call in the morning, not a 3am block.

What the babysitter can do alone is BLOCK. Past that arm it selects the
wording of the reason and whether ``dissent`` is set, and the evidence
selects the verdict. ``reconcile`` is written in that shape so the rule
is legible from the control flow rather than from this paragraph.

**A check that was supposed to fail and did not is blocking.** This is
Guard 2 of ``Skill(imbue:proof-of-work)`` module ``verifier-integrity``:
a check proven able to go red is the only kind whose green means
anything. Nothing downstream may proceed on an unproven guard.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


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


#: Exit codes that mean the command never ran to a conclusion. They
#: satisfied `expect: fail` on nonzero alone, so a guard that could not
#: be found, or that hung until the timeout killed it, was recorded as
#: proven able to go red. 127 is the shell's "not found"; 124 is what
#: `SubprocessRunner` reports for a timeout.
_COULD_NOT_RUN = frozenset({127, 124})


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

    # Binary, read once. Comparing against both spellings separately made
    # the field tri-state: any third value fell through both arms and
    # returned ok=True whatever the exit code, so `expect: Pass` over a
    # command exiting 1 produced a PASS proof row. The gate rejects
    # anything outside the two legal values (handoff_gate._LEGAL_EXPECT);
    # this reads the field as what it is.
    expects_failure = evidence.get("expect", "pass") == "fail"
    match = evidence.get("match")

    if expects_failure and exit_code in _COULD_NOT_RUN:
        return Objective(
            ok=False,
            why=(
                f"the check exited {exit_code}, which is not the guard going "
                "red. A command that could not be found, or that never "
                "finished, has proved nothing about whether it guards the "
                "task, and `expect: fail` counted it as proof."
            ),
            blocking=True,
        )

    if expects_failure and exit_code == 0:
        return Objective(
            ok=False,
            why=(
                "the check did not fail when it was declared to fail. It does "
                "not guard what the task claims, so no later green from it "
                "means anything."
            ),
            blocking=True,
        )

    if not expects_failure and exit_code != 0:
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

    # Past the two blocking arms the verdict is the evidence's. The
    # babysitter string selects only the wording and the dissent flag.
    if not objective.ok:
        overridden = babysitter == "PASS"
        return Verdict(
            verdict="FAIL",
            reason=(
                f"babysitter passed it; overridden by evidence: {objective.why}"
                if overridden
                else objective.why
            ),
        )

    if babysitter == "FAIL":
        return Verdict(
            verdict="PASS",
            reason=(
                "evidence is green; babysitter dissent recorded for the morning: "
                f"{babysitter_reason}"
            ),
            dissent=True,
        )

    return Verdict(verdict="PASS", reason=babysitter_reason)


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
