---
name: graduated-implementation
description: Ramps implementation ambition a notch only after the prior increment is understood. Use when building a feature you must understand, not just ship.
alwaysApply: false
category: workflow-methodology
tags:
- learning
- graduated-practice
- zone-of-proximal-development
- scope-ramp
- competence-gate
- automation-bias
dependencies: []
tools: []
usage_patterns:
- bounded-start
- competence-gated-ramp
- magenta-hand-fly-check
complexity: intermediate
model_hint: standard
estimated_tokens: 2300
modules:
- modules/advancement-gate.md
- modules/ramp-ledger.md
- modules/research-basis.md
role: library
---

> Start with the smallest slice you can fully understand. Earn the
> next notch by proving you understood the last one. Ambition that
> outruns understanding is how a fluent diff becomes an unverifiable
> one.

# Graduated Implementation

## Overview

The sibling skill `imbue:assisted-mastery` fades scaffolding as
competence grows. This skill ramps the other axis: the ambition of
the next increment. They are the two directions of one move, the
graduated practice that turned novices into experts long before
agents existed. Not "ban the tool," but "couple the next challenge
to demonstrated competence on the last one."

The learning sciences give the move a number. Wilson et al. (2019,
*Nature Communications* 10:4646) derive the optimal training point
for a learner at roughly 85% success: hard enough to learn from,
not so hard that the signal is noise. The same band is what
Vygotsky's zone of proximal development, Ericsson's edge of
ability, and Csikszentmihalyi's flow channel all gesture at.
Bloom's mastery learning (advance a unit at >=90% on a fresh
check), Bayesian Knowledge Tracing (advance at p(mastery) >= 0.95),
and competence-based curriculum learning (Platanios et al. 2019,
only attempt tasks within the current competence) are the same
rule at different resolutions.

The danger this guards against is specific. An agent that one-shots
a large change is maximally helpful to throughput and quietly
corrosive to verification: you cannot review what you did not watch
get built, and automation bias means you will trust it precisely
when it is wrong (Perry et al. 2023). Aviation named the endpoint
"children of the magenta": ramp the operator's autonomy faster than
their retained understanding and they can no longer hand-fly or
override the automation when it misbehaves.

## The Three Practices

### 1. Start at the smallest intentional increment

Do not design the whole system up front. Pick the smallest slice
that is a real, end-to-end step and stop there. The default rung is
about 40 added lines: a change a human can read and explain in one
sitting. The bound is the point, not a nuisance: it keeps
understanding in pace with output. The `guard_scope_ramp.py` hook
makes this concrete by flagging an increment that jumps past the
current rung.

### 2. Ramp a notch only on demonstrated understanding

The next increment may be more ambitious only after the prior one's
understanding is demonstrated and recorded. The check is sized to
blast radius, the [advancement gate](modules/advancement-gate.md):

- **Low-stakes increment**: ramp on an evidence gate. The prior
  slice has green tests and a recorded tradeoff (what was chosen,
  what was rejected, why).
- **High-stakes increment** (auth, migrations, money, infra,
  crypto): ramp only when the human explains the prior diff
  unaided. This is the magenta hand-fly check. If they cannot
  explain it, the rung drops rather than rises.

Recording the demonstration mints a ramp token (`touch
.imbue/ramp-ok`), which the hook consumes to widen the rung one
notch. You ramp by proving you understood the last slice, not by
writing more. Each notch is appended to the
[ramp ledger](modules/ramp-ledger.md) so a reviewer can later audit
that the demonstration was real, not rubber-stamped.

### 3. Hold the 85% band in both directions

Advancing too fast is one failure; never advancing is the other.

- Below the band (the human is lost, the slice was too big): hold,
  shrink the increment, re-scaffold. Do not ramp.
- In the band (clean demonstration, some genuine effort): ramp one
  notch.
- Above the band (the human clears it trivially, repeatedly): ramp
  faster. Drilling a mastered skill is over-practice, the boredom
  failure that gets spaced-repetition decks abandoned (Cen &
  Koedinger 2007).

## When To Use

- An agent is building a feature across more than one increment and
  the human will maintain or be accountable for it.
- The work touches an unfamiliar subsystem or a high-stakes path.
- The human is building skill in an area, not just shipping a
  throwaway.

Skip it for a single bounded edit, a trivial reversible change, or
generated and vendored code. Forcing a ramp ritual on a typo fix is
ceremony, and ceremony trains people to ignore the gate.

## When NOT To Use

- A trivial or mechanical fix, where ramping buys nothing
- You already understand the change and need evidence it works (use
  `imbue:proof-of-work`)

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll just build the whole thing, then review" | You cannot review what you did not watch get built. Start with one slice. |
| "Tests pass, so it is understood" | Completion is not understanding. Duolingo streaks prove a cheap signal decouples from skill. |
| "I can self-certify I get it" | The producer may not grade its own readiness. Demonstrate it, record it. |
| "Bigger increments are faster" | Faster to write, slower to verify, and the verification is the point. |
| "The rung is slowing me down" | On work you must own, staying in the 85% band is the fast path to durable skill. |

## Related Skills

- `imbue:assisted-mastery`: fades scaffolding as competence grows;
  this skill ramps challenge. Two directions, one axis.
- `imbue:proof-of-work`: the evidence half of the low-stakes gate.
- `imbue:scope-guard`: bounds the branch; this bounds the
  increment within it.
- `leyline:risk-classification`: the stakes tier that selects which
  gate (evidence vs explanation) applies.
- `leyline:decision-journal`: the durable home for the recorded
  tradeoff that mints a ramp token.

The empirical basis for the 85% band, the failure modes, and the
cross-domain gate design is preserved in
[research-basis.md](modules/research-basis.md).

## Exit Criteria

- [ ] The first increment of the feature was bounded to roughly the
      start rung, not the whole design.
- [ ] Each ramp to a more ambitious increment was preceded by a
      recorded demonstration of the prior increment (a tradeoff
      entry; for high-stakes paths, the human explaining the diff
      unaided).
- [ ] The stakes tier was used to choose the evidence gate vs the
      explanation gate, not defaulted silently.
- [ ] An increment that put the human below the understanding band
      triggered a hold and a smaller next slice, not a ramp.
