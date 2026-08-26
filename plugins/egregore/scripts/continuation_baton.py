"""A handoff record the loop writes down, so a dropped turn is visible.

ADR-0022 records why egregore continues at all: the Stop hook returns
``{"decision": "block", "reason": ...}`` and the harness feeds the
reason back as the next instruction. It also records the cost of that
being undocumented: "no test can cover the harness end of it, so the
first symptom of an upstream change is a loop that stops after one
turn."

This module does not remove the dependency. It removes the silence.

The problem stated as a contradiction: the trigger must be inside the
session, because only the session knows a unit finished the moment it
finishes, and outside the session, because only an external process
survives the session ending. One parameter pulled toward two opposite
values, which is a physical contradiction, and compromise is the wrong
move for one of those. The separation axis is system scale: the
knowledge stays inside, the actuator moves outside, and a durable
artifact carries the signal across.

That artifact is a baton. At each stop the session writes what it just
finished, what comes next, and the time by which the next turn should
have started. A turn that happens advances the sequence and sets a new
deadline. A turn that does not leaves a baton past its deadline with
its sequence unmoved.

The property that makes this more than a timeout: **stranded means
stalled, not old.** A run that keeps advancing is healthy at any age,
and a baton written seconds ago is stranded the instant its own
deadline passes with no successor. An external watcher therefore polls
on a clock but *acts* on a written fact, so relaunch latency is the
grace period the session chose rather than the poll interval.

Three failure modes become distinguishable, where the pidfile alone
distinguishes one:

===========================  =====================================
Observation                  Meaning
===========================  =====================================
No baton                     Nothing was handed off. Not a failure.
Baton cleared                The run finished its work.
Baton stranded, pid alive    Reinjection stopped. The ADR-0022 case.
Baton stranded, pid gone     The session died mid-unit.
===========================  =====================================

The third row is the one that had no observation at all before.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

#: Bumped when the on-disk shape changes incompatibly. A reader that
#: finds an unfamiliar version treats the baton as absent, which errs
#: toward not relaunching.
BATON_VERSION = 1

DEFAULT_BATON_PATH = Path(".egregore") / "baton.json"


@dataclass(frozen=True)
class Baton:
    """One handoff: what finished, what is next, and by when."""

    #: Increments on every handoff. The sequence, not the timestamp, is
    #: what says a turn happened.
    sequence: int
    #: The work unit that just completed.
    unit: str
    #: The instruction to resume with. Written by the session that knows
    #: what comes next, so a relaunch does not have to rediscover it.
    next_prompt: str
    written_at: float
    #: Epoch seconds by which the next turn should have started. Chosen
    #: by the session, because it knows how long its next unit takes.
    deadline: float


def read_baton(path: Path | None = None) -> Baton | None:
    """Return the current baton, or None if there is none to read.

    A missing file and an unreadable one both answer None. Treating
    damage as "no claim" errs toward not relaunching; the opposite
    default would let a truncated write spawn sessions.
    """
    target = Path(path) if path is not None else DEFAULT_BATON_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(raw, dict) or raw.get("version") != BATON_VERSION:
        return None

    try:
        return Baton(**raw["baton"])
    except (KeyError, TypeError):
        return None


def write_baton(baton: Baton, path: Path | None = None) -> None:
    """Put the baton down where a process outside this session can see it.

    Written to a sibling temporary file and renamed, because a watcher
    may read at any moment and a half-written baton reads as no baton,
    which would look like a finished run.
    """
    target = Path(path) if path is not None else DEFAULT_BATON_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": BATON_VERSION, "baton": asdict(baton)}
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def advance_baton(
    path: Path | None = None,
    *,
    unit: str,
    now: float,
    deadline: float,
    next_prompt: str | None = None,
) -> Baton:
    """Record that a turn happened, and set the deadline for the next.

    This is the call that makes a healthy run distinguishable from a
    stalled one, so it belongs at the point the session decides it has
    finished a unit, not on a timer.

    ``now`` is required and separate from ``deadline`` on purpose. An
    earlier version recorded the deadline as the write time, which made
    the two fields equal and let a plain age-based timeout pass every
    test this module has. Keeping them distinct is what makes "stalled"
    mean something other than "old".

    ``next_prompt`` carries forward when omitted: a turn that does not
    change what comes next should not have to restate it. With no prior
    baton the sequence starts at 1, which is the ordinary first stop.
    """
    previous = read_baton(path)
    baton = Baton(
        sequence=(previous.sequence + 1) if previous else 1,
        unit=unit,
        next_prompt=next_prompt
        or (previous.next_prompt if previous else "Resume the pipeline"),
        written_at=now,
        deadline=deadline,
    )
    write_baton(baton, path)
    return baton


def clear_baton(path: Path | None = None) -> None:
    """Record that the run finished, rather than dropped the baton.

    Without this the last baton of every completed run sits past its
    deadline forever and reads as stranded, which would have the
    watcher relaunch finished work.
    """
    target = Path(path) if path is not None else DEFAULT_BATON_PATH
    target.unlink(missing_ok=True)


def is_stranded(path: Path | None = None, now: float = 0.0) -> bool:
    """Whether a handoff was made and no turn picked it up.

    Stalled, not old: a baton that kept advancing set a new deadline
    each time, so a long healthy run never satisfies this. No baton and
    a cleared baton are both False, because nothing was dropped.
    """
    baton = read_baton(path)
    if baton is None:
        return False
    return now > baton.deadline
