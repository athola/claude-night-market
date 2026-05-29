---
name: belief-clarity
description: |
  Pre-compression clarity check using dual anchor questions.
  Verifies that a summary or compressed context retains enough
  task state to guide future reasoning before proceeding.
category: conservation
---

# Belief Clarity Module

## Purpose

Before compressing context or handing off to a continuation agent,
verify the compressed form can answer two anchor questions. If it
cannot, the compression has lost task-critical information.

This implements the anchor-question pattern from MMPO
(arXiv:2605.30159, Liu et al. 2026) as a qualitative pre-compression
gate. The paper shows that ambiguous intermediate summaries cause
belief deviation: the agent's internal model of the task drifts
from reality as interactions extend. This module catches that drift
before it causes a handoff failure.

## When to Apply

Apply this check at two points:

1. **Before saving session-state.md** (conserve:clear-context): verify
   the draft state can answer both probes before delegating.
2. **After any context compression** (conserve:context-optimization):
   verify the compressed result retains the pre-compression answers.

## The Two Anchor Questions

Ask these questions against the memory or compressed context:

**Q1: Progress probe:**
```
Based on the current memory/context, what is the current task
progress? What has been completed and what state is the task in now?
```

**Q2: Gap probe:**
```
Based on the current memory/context, what information is still needed
to complete the task? List specific open items, not generic categories.
```

A memory that answers Q1 with specific completed steps and Q2 with
a bounded list of concrete unknowns is clear enough to proceed.

## Scoring

| Q1 answer | Q2 answer | Decision |
|-----------|-----------|----------|
| Specific and complete | Finite concrete list | Proceed |
| Specific | Open-ended or generic | Expand memory before proceeding |
| Hedging ("I think...") | Any | Regenerate or expand |
| Vague or empty | Any | Regenerate: do not hand off |

## Usage Pattern

### Inline check before clear-context handoff

```
1. Draft session-state.md with current task summary
2. Ask Q1 against the draft
3. Ask Q2 against the draft
4. If both score "Proceed": save and hand off
5. If either fails: append the failing probe's answer directly
   to session-state.md as "Current state: ..." and "Still needed: ..."
   then re-score
```

### Post-compression verification

```
1. Record Q1 and Q2 answers from pre-compression context
2. Apply compression (compact, summarize, delegate)
3. Ask Q1 and Q2 again against the compressed form
4. If answers materially match: compression preserved task state
5. If answers diverge: compression lost information; add a
   "Task state snapshot" section to the compressed form
```

## Integration with memory-clarity-probe

When `memory-palace:memory-clarity-probe` is available, delegate
the dual-probe evaluation to it rather than running inline:

```
Skill(memory-palace:memory-clarity-probe)
```

The probe produces a `Clarity Assessment` block with
composite score and recommendation. Use "Proceed" composite as the
gate condition.

## Limitation

This check is qualitative. It cannot compute token-level predictive
entropy (true Belief Entropy from the MMPO paper) because Claude Code
skills do not expose model log-probabilities. A session-state.md that
produces confident but wrong answers to the probes will score as
"Proceed" incorrectly. Pair this gate with explicit task-state
verification (imbue:proof-of-work) for high-stakes handoffs.

## Failure Recovery

If the check fails and expansion does not resolve it:

1. Do not hand off. The continuation agent will start from corrupted
   task state.
2. Ask the user to confirm current state and next steps.
3. Write the confirmed state explicitly as bullet points at the top
   of session-state.md before re-running the check.
