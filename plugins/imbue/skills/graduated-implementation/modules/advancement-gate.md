# Advancement Gate

The gate decides whether the agent may ramp the next increment's
ambition a notch. It is the load-bearing part of graduated
implementation: too lax and ambition outruns understanding (blind
trust); too strict and the work never advances (over-drilling). The
design target is the ~85% band.

## The gate by stakes

The stakes tier (from `leyline:risk-classification`) selects which
check must pass before the rung widens.

| Stakes | Gate | What mints the ramp token |
|--------|------|---------------------------|
| Low (GREEN/YELLOW) | Evidence | Prior increment has green tests and a recorded tradeoff entry. |
| High (RED/CRITICAL) | Explanation | The human explains the prior diff unaided, on a novel question, and records a tradeoff entry. |

The high-stakes gate uses an *unrehearsed* question about the actual
change, not a recap the agent fed the human. This is the
sight-reading principle from graded music exams and the reason
medicine rejected "see one, do one, teach one": confidence outran
competence when the test was a rehearsal. A signal that is cheap to
fake (completion, a streak, a yes) will be faked; the gate has to
cost what understanding costs.

The tier comes from `leyline:risk-classification`. The hook reads it
from the `IMBUE_STAKES` environment variable or a one-line
`.imbue/stakes` file (values `GREEN`, `YELLOW`, `RED`, `CRITICAL`);
when neither is set it falls back to a path heuristic (a high-stakes
path is treated as RED). The rung scales with the tier: GREEN and
YELLOW keep the full rung, RED halves it, and CRITICAL quarters it, so
the riskier the change the sooner a demonstration is forced.

## Why the producer cannot self-certify

The agent that wrote the increment may not be the one that grades
readiness to ramp. This is the four-eyes principle, and it is the
universal anti-gaming device across every apprenticeship domain
studied: the guild masterpiece judged by other masters, the
visiting examiner, the medical milestone observed by a supervisor.
A producer grading its own readiness is the automation-bias trap in
miniature. See `imbue:proof-of-work` module
`independent-verification` for the high-stakes verification rule
this builds on.

## The three failure modes the gate guards

1. **Advancing too fast (under-mastery).** A large increment passes
   because the signal was cheap. Guard: the rung only widens by one
   notch per recorded demonstration, and high-stakes paths get a
   halved rung so they force a demonstration sooner.
2. **Never advancing (over-drill, boredom).** The human clears
   every slice trivially but the rung never grows, or a single
   stumble ratchets it down and traps the work (the spaced-
   repetition "ease hell" that gets decks abandoned). Guard: ramp
   faster when the human is clearly above the band; never ratchet
   the rung down on one miss alone.
3. **Gaming the metric (Goodhart).** Optimizing the signal instead
   of the skill: padding tests, memorizing the recap, clicking
   through. Guard: the high-stakes check is a novel question, the
   producer is not the certifier, and the demonstration is recorded
   where it can be audited later.

## How the hook operationalizes the gate

`guard_scope_ramp.py` (PreToolUse on Write, Edit, MultiEdit) holds
each increment to the current rung:

- The rung starts bounded (`RUNG_START`, ~40 added lines) and
  widens by `RAMP_FACTOR` per ramp token, capped at `RUNG_CAP`.
- A ramp token is `IMBUE_RAMP_OK=1` or a `.imbue/ramp-ok` file,
  created only after a demonstration is recorded and consumed on
  use, so one demonstration buys one notch.
- High-stakes paths (auth, migration, payment, infra, crypto) get a
  halved effective rung.
- Shadow mode (default) warns; `VOW_SHADOW_MODE=0` blocks an
  over-rung increment. The hook never blocks on its own state error
  and never crashes the agent.

The hook enforces the *bound and the ramp*. It does not measure
understanding; it requires that a demonstration was recorded before
ambition grows. Measuring understanding is the human's job, which
is the entire point: the gate exists so that judgment is built, not
bypassed.
