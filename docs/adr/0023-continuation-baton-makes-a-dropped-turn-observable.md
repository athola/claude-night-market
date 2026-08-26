# ADR-0023: A Continuation Baton Makes a Dropped Turn Observable

**Date**: 2026-08-25
**Status**: Accepted, with the ADR-0022 dependency unchanged
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0022 (the dependency this does not remove),
`night-market-research-frontier` problem 6,
`night-market-architecture-contract` weak point 6

## Context

ADR-0022 records that egregore continues across turns by riding an
undocumented harness behavior, and closes with the part nobody could
act on: no test can cover the harness end of it, so the first symptom
of an upstream change is a loop that stops after one turn.

That last clause is a detection problem rather than a dependency
problem. A loop that stopped after one turn and a loop that finished
its work produce the same observation from outside: a session that is
no longer running. The watchdog cannot tell them apart, so it polls a
static fact instead, whether the manifest still holds active items,
and relaunches on that. The completion signal never crosses out of the
session at all.

Review on PR #662 asked for this to be addressed with a novel
technique, naming TRIZ.

## The contradiction

Stated as TRIZ asks for it, this is a physical contradiction rather
than a technical one. One parameter is pulled toward two opposite
values:

> The continuation trigger must live **inside** the session, because
> only the session knows a work unit finished at the moment it
> finishes. It must live **outside** the session, because only an
> external process survives the session ending.

Compromise is the wrong move for a physical contradiction, and the
compromise is what exists today: a clock-driven external poller, which
is durable and not responsive, plus a session-bound Stop hook, which
is responsive and not durable. Neither knows what the other knows.

The Ideal Final Result: the next unit begins the instant the previous
one completes, with no process existing whose job is to make that
happen.

Separation axis: **system scale**. The knowledge stays inside, the
actuator moves outside, and a durable artifact carries the signal
across the boundary.

## The cross-domain bridges

| Field | Analogue | What it contributes | Confidence |
|-------|----------|---------------------|-----------|
| Rail engineering | Dead man's control: the driver holds a lever, and releasing it brakes the train | Liveness is proved by a positive repeated act, so the *absence* of the act is the signal. Inverts polling from "is there work" to "did an expected act fail to happen" | High |
| Cell biology | Cell-cycle checkpoint: no central clock authorizes division, a state is written and downstream machinery reads it | The producer writes the state at the moment it is true; the consumer is decoupled and may be absent | Medium-high |
| Logistics | Kanban card: work is pulled, not pushed on a schedule, and the card outlives whoever placed it | The artifact is the handoff. Its presence and its collection are both meaningful | Medium-high |

All three land on the same shape, which is the sign the analogy is
carrying weight rather than decorating a decision already made: a
producer that writes a positive record, and a consumer that watches
for that record failing to be renewed.

## Decision

`plugins/egregore/scripts/continuation_baton.py`. At each stop the
session records the unit it finished, the instruction to resume with,
a monotonically increasing sequence number, and the time by which the
next turn should have started. A turn that happens calls
`advance_baton`, which increments the sequence and sets a new
deadline. A turn that does not leaves a baton past its deadline with
its sequence unmoved.

The load-bearing property, and the one the tests pin hardest:
**stranded means stalled, not old**. A run that keeps advancing is
healthy at any age, because each turn set a new deadline. A baton
written seconds ago is stranded the instant its own deadline passes
with no successor. An external watcher therefore still polls on a
clock but *acts* on a written fact, so relaunch latency is the grace
period the session chose rather than the poll interval.

Four states become distinguishable where the pidfile distinguished
one:

| Observation | Meaning |
|-------------|---------|
| No baton | Nothing was handed off. Not a failure |
| Baton cleared | The run finished its work |
| Baton stranded, pid alive | Reinjection stopped. The ADR-0022 case |
| Baton stranded, pid gone | The session died mid-unit |

The third row had no observation at all before this, which is the
detection gap ADR-0022 named.

A relaunch also carries the session's own `next_prompt` rather than
the watchdog's generic fallback, so a resumed session does not
rediscover what it was doing.

## What this does not change

The dependency in ADR-0022 stands. Egregore still continues because
the Stop hook blocks and the harness reinjects the reason. This ADR
adds no continuation primitive and removes no reliance.

What changes is that the reliance failing is now a fact somebody can
read. If an upstream release stops treating the reason field as the
next instruction, the baton strands with the pid alive, and that is a
distinct signal rather than a run that quietly ended.

Both halves in this repository are tested:
`plugins/egregore/tests/test_continuation_baton.py` covers the write
side, the read side, and the stalled-versus-old distinction. The
harness end remains untestable here, exactly as ADR-0022 states, and
this record makes no claim otherwise.

The revert test earned its place on the first attempt. `advance_baton`
recorded the deadline as the write time, which collapsed two fields
into one, and with the deadline check replaced by "older than a fixed
interval" all thirteen tests still passed. The mechanism's entire
claim over a timeout is that it measures a missed handoff rather than
elapsed time, and the suite could not tell the difference. Separating
the fields, and asserting on a baton written at 1000 and due at 9000,
is what makes two tests fail when the mechanism degrades.

## Consequences

- **Positive**: The failure mode ADR-0022 called undetectable is now
  detectable, and a stalled loop is distinguishable from a finished
  one and from a crashed one.
- **Positive**: Relaunch carries the instruction the session wrote at
  handoff, replacing a generic fallback prompt.
- **Negative / debt accepted**: The watchdog does not read the baton
  yet. Wiring it means changing the relaunch condition in
  `plugins/egregore/scripts/watchdog.sh` from "manifest has active
  items" to "baton is stranded", which changes when unattended runs
  relaunch and deserves its own change with its own dogfooding, of the
  kind that found the three defects in ADR-0022's table. The module
  and its contract land first.
- **Negative / debt accepted**: The deadline is chosen by the session,
  and a session that consistently underestimates its next unit will
  strand batons on healthy runs. No calibration exists; the grace
  period is a judgment the caller passes in.
