---
name: assisted-mastery
description: Makes agent reasoning visible, surfaces tradeoffs, and fades help so humans build judgment. Use when reviewing or learning from agent-written code.
alwaysApply: false
category: workflow-methodology
tags:
- learning
- assistance-dilemma
- visible-reasoning
- tradeoffs
- skill-retention
- automation-bias
dependencies: []
tools: []
usage_patterns:
- visible-reasoning
- mode-selection
- assistance-fading
complexity: intermediate
model_hint: standard
estimated_tokens: 2200
modules:
- modules/modes-and-fading.md
- modules/tradeoff-ledger.md
- modules/research-basis.md
role: entrypoint
---

> A finished diff hides the thinking that produced it. The
> thinking is what the human needs to keep. Show the work, surface
> the choices, and hand back the parts worth struggling with.

# Assisted Mastery

## Overview

A coding agent that always returns the finished answer is
maximally helpful to throughput and quietly corrosive to skill.
The learning-science evidence is consistent: instructional support
that helps a novice actively harms an expert (the expertise
reversal effect, Kalyuga et al. 2003), so help must fade as
competence grows rather than stay constant. Struggling with a
problem before being shown the solution produces deeper
understanding and transfer than being handed the answer
(productive failure, Kapur 2008). And offloading the thinking to a
tool measurably reduces what the human retains (the cognitive
offloading and critical-thinking correlation of r = -0.75,
Gerlich 2025; the Google effect, Sparrow et al. 2011).

This is the assistance dilemma: the same help that speeds the
output erodes the judgment needed to verify it. The danger
compounds with automation bias: AI-assisted developers in a
controlled study wrote less secure code while believing it was
more secure (Perry et al. 2023). You cannot verify what you do not
understand, and a fluent diff signals competence it has not
earned.

This skill does not slow down throughput work. It makes the
*reasoning* a first-class deliverable alongside the code, surfaces
the tradeoffs before a design is locked in, and lets the human
choose how much of the work to keep for themselves.

## The Three Practices

### 1. Make the reasoning visible

For any non-trivial change, emit the reasoning alongside the diff,
sized to the blast radius:

- **Assumptions**: what the change takes for granted about the
  codebase, inputs, and environment.
- **Alternatives considered**: the two or three approaches that
  were viable, and why each was rejected.
- **Ramifications**: what this design makes easy later, what it
  makes hard, and what would have to change to reverse it.

A high-blast-radius change with no stated reasoning is treated as
incomplete, the same way an apprentice who "just did it" without
showing their thinking would be sent back. This mirrors cognitive
apprenticeship: the expert's invisible reasoning must be
externalized before anyone can supervise or learn from it.

### 2. Surface tradeoffs before choosing

Do not present a single design as inevitable. State the decision,
the options, and the axis each option wins on, then make the call
and say why. Record consequential decisions in the
[tradeoff ledger](modules/tradeoff-ledger.md) so the reasoning is
auditable later and the human can challenge it now. This is how
novices were always trained into experts: by working through the
positives, negatives, and ramifications of a decision, not by
copying the conclusion.

### 3. Choose the mode, and fade it

Pick the assistance mode deliberately per task, and reduce it over
time on skills the human is building. See
[modes-and-fading.md](modules/modes-and-fading.md):

- **Explain mode**: the agent narrates the reasoning and the human
  writes the load-bearing code. Builds judgment. Use on
  unfamiliar territory, high-stakes paths, and skills the human
  wants to own.
- **Produce mode**: the agent writes, the human reviews. Maximizes
  throughput. Use on boilerplate, well-understood patterns, and
  reversible low-stakes work.

Default to produce mode for commodity work and explain mode where
understanding is the point. As the human's competence on a given
area grows, fade from produce toward explain to manual: permanent
scaffolding is the failure mode, not the goal.

## When To Use

- An agent produced code the human will have to maintain, review,
  or be accountable for.
- The change touches an unfamiliar subsystem or a high-stakes path
  (auth, migrations, money, concurrency).
- A design decision has more than one defensible answer.
- The human is trying to build skill in an area, not just ship.

Skip it for trivial, reversible, well-understood edits where the
reasoning is self-evident: forcing a ledger entry on a typo fix is
ceremony, and ceremony trains people to ignore the gate.

## When NOT To Use

- You only need the change shipped and verified (use
  `imbue:proof-of-work`)
- Deciding whether to build it at all (use `imbue:scope-guard`)

## Red Flags

| Thought | Reality |
|---------|---------|
| "The diff is obviously correct" | Correct to whom? State why, or you are guessing. |
| "Explaining slows me down" | On work you must own, the explanation is the deliverable. |
| "There was only one way to do it" | There is rarely one way. Name the alternatives you dismissed. |
| "I'll understand it later if it breaks" | Automation bias: you will trust it precisely when it is wrong. |
| "More agent help is always better" | Help that never fades builds dependence, not skill. |

## Related Skills

- `imbue:graduated-implementation`: the other direction of the same
  axis. This skill fades scaffolding; that one ramps the ambition
  of the next increment as understanding is demonstrated.
- `imbue:proof-of-work`: evidence that the code works; this skill
  adds evidence that the human understands it.
- `imbue:rigorous-reasoning`: anti-sycophancy when evaluating the
  agent's stated tradeoffs rather than deferring to them.
- `imbue:karpathy-principles`: think-first and simplicity, the
  pre-implementation companion to visible reasoning.
- `leyline:decision-journal`: the durable home for tradeoff-ledger
  entries that outlive the session.
- `leyline:risk-classification`: choosing the automation tier from
  the task's risk, the input to mode selection.

The measured evidence for blind-trust failure, the learning-science
basis for fading, and the six workflow principles are preserved in
[research-basis.md](modules/research-basis.md).

## Exit Criteria

- [ ] Non-trivial changes ship with stated assumptions,
      alternatives considered, and ramifications, sized to blast
      radius.
- [ ] At least one consequential design decision in the session is
      recorded with its rejected alternatives.
- [ ] The assistance mode (explain or produce) was chosen
      deliberately and stated, not defaulted to "produce" silently.
- [ ] On a skill the human is building, assistance is lower than it
      would have been at constant scaffolding (fading is applied).
