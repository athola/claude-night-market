# Two-Phase Extraction

Inventory before judgment. Grouping while reading suppresses threads
that do not yet fit a group, and those are usually the corrections and
process findings worth keeping.

## PHASE 1: Inventory

Sweep the transcript and list every distinct thread it touched, one line
each, numbered. The only objective is to **miss nothing**. Do not assign
types, merge items, or exclude anything except startup mechanics and
tool-call narration. When in doubt, list it.

Sweep for:

- Every question the human asked, including ones answered in passing
- Every decision, with whatever alternatives were rejected
- Every error hit and how it resolved
- Every file or subsystem touched
- Every correction the human made to the approach
- Every question left hanging

State the thread count at the end of the phase. That number is the
checksum for PHASE 2.

## PHASE 2: Render

Now apply judgment. Group the inventory into threads, where a thread is
one line of work, investigation, decision, finding, or correction. Each
thread becomes one unit per type.

Rules:

- A sub-step is not its own unit. Fold it into its parent thread's
  `State` or `Why`.
- A correction, decision, or finding is always its own thread, even when
  it happened in the middle of another activity.
- Apply the split rule from `unit-schema.md` when a thread bundles a
  durable result with the transient action that produced it.
- Capture where things landed, not the blow-by-blow. The full path stays
  in the transcript, reachable through `Ref`.
- Use the session's own terminology.

## Fidelity

Include only what the transcript supports. Never infer a decision that
was not made. Dates, filenames, identifiers, and counts go in only when
the transcript states them. When a thread's outcome is ambiguous, say so
or leave it out.

A **confident-but-wrong** unit is the worst possible outcome. It will be
retrieved months later and acted on, and nothing in the retrieval path
can detect that it was fabricated. An omitted unit merely costs a
re-derivation.

## Coverage Self-Check

Before staging, confirm every PHASE 1 item appears in PHASE 2, either as
its own unit or folded into a parent thread's text. Report any item
deliberately dropped and why. A silent drop reads as coverage that was
never achieved.
