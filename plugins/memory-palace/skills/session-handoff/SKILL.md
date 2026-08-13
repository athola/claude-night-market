---
name: session-handoff
description: Decompose a session into typed handoff units and recall them later. Use when ending a session or resuming work whose prior state must be recovered.
alwaysApply: false
category: session-management
tags:
- session-continuity
- handoff
- recall
- typed-units
- temporal-awareness
dependencies:
- memory-palace:memory-clarity-probe
- memory-palace:session-palace-builder
scripts: []
usage_patterns:
- session-end-capture
- session-resume
- cross-session-recall
complexity: intermediate
model_hint: standard
estimated_tokens: 900
---

## Table of Contents

- [What It Is](#what-it-is)
- [The Unit Schema](#the-unit-schema)
- [Two-Phase Extraction](#two-phase-extraction)
- [Splitting and Superseding](#splitting-and-superseding)
- [Capture Workflow](#capture-workflow)
- [Recall Workflow](#recall-workflow)
- [When NOT To Use](#when-not-to-use)
- [Detailed Resources](#detailed-resources)
- [Exit Criteria](#exit-criteria)

# Session Handoff

Record where the thinking landed, not that a session happened.

## What It Is

A session ends with decisions half-made, questions half-answered, and
findings nobody wrote down. The next session starts from zero and
re-derives them, which costs tokens and forces the human to reconstruct
their own prior reasoning.

This skill decomposes a session into **typed units** and stages them for
later recall. The type is what makes recall trustworthy: a status update
stops being true in days, while a fact about how a tool behaves stays
true for years, so the two cannot share one shelf life.

## The Unit Schema

Every unit carries seven fields:

```
Thread: short, specific label phrased the way a later session would ask
Type:   finding | decision | open-thread | state
Date:   YYYY-MM-DD, when this thread reached its conclusion
State:  what landed by the end of the session, in 1-2 sentences
Why:    the load-bearing reasoning, including what was rejected
Open:   what remains unresolved, omitted entirely when nothing is
Ref:    the session this came from
```

The four types and how fast each ages:

| Type | What it is | Half-life |
|------|-----------|-----------|
| `finding` | A durable fact about the world, platform, or tools | 365 days |
| `decision` | A project choice that could later be revised | 90 days |
| `state` | A transient status or state change | 7 days |
| `open-thread` | A live, unresolved question | does not decay |

Those values are the retention classes in
`memory_palace.corpus.decay_model.UNIT_TYPE_DECAY`. The writer picks a
type, never a shelf life, so retention is bound once per class rather
than guessed per item.

## Two-Phase Extraction

Inventory first, judge second. Doing both at once loses threads, because
the act of grouping suppresses items that do not fit a group yet.

1. **Phase 1** sweeps the transcript and lists every distinct thread it
   touched, one line each. Over-include on purpose.
2. **Phase 2** groups that inventory into threads and renders one unit
   per thread per type.

Full procedure and the coverage self-check:
`modules/two-phase-extraction.md`.

## Splitting and Superseding

A thread that bundles a durable finding with the transient action that
produced it becomes **two units with different types**, so each ages on
its own curve.

A later unit with the same `Thread` and `Type` **supersedes** the earlier
one. The same thread under a different type stays separate. Supersession
is why a revised decision does not surface next to the decision it
replaced.

## Capture Workflow

1. Run Phase 1, then Phase 2.
2. Optionally gate the rendered units through
   `Skill(memory-palace:memory-clarity-probe)`. If the composite reads
   Unclear, expand the units before staging them.
3. Write them to `data/state/handoff_units.json` in this shape:

```json
{"units": [{"thread": "...", "type": "decision", "date": "2026-08-13",
            "state": "...", "why": "...", "open": "", "ref": "...",
            "files": ["src/thing.py"]}]}
```

Declare `files` when the claim would stop being true if those paths
changed. The capture path fingerprints them, and recall flags the unit
when one moves.

The `Stop` hook drains that file and merges the units into the session
record. The Stop payload carries no transcript content and the hook runs
no model, which is why capture is staged by this skill rather than
extracted by the hook.

## Recall Workflow

Append `+recall` to a prompt to have matching units injected, or
`+recall?` to also see what was retrieved. Recall is opt-in because
fixed-cost injection on every turn spends the context window it was
meant to extend.

Before acting on any `state` unit, state the elapsed time since it was
written. See `modules/temporal-awareness.md`.

### When to suggest it mid-session

The token is the user's to type, so the work here is to say when it
would pay and leave the choice with them. Offer it in one line at the
moment it applies, then answer the question that was actually asked.

`plugins/memory-palace/hooks/recall.py` ranks units by keyword overlap
between the prompt and each unit's `thread`, `state`, `why`, and
`open` fields, scaled by type-aware decay. The rest follows from that:
overlap is the retrieval, so a prompt naming its topic retrieves and a
prompt gesturing at it does not.

| Moment in the session | Offer | What makes it pay |
|-----------------------|-------|-------------------|
| The prompt names work from an earlier session in that work's own vocabulary | `+recall` | Overlap scoring has terms to match |
| Work resumes after a clear or a compaction | `+recall` | The units are still on disk once the live context no longer holds them |
| The user asks why a past decision went the way it did | `+recall` | `why` is one of the ranked fields |
| The user doubts whether injected state is still current | `+recall?` | Visible mode shows what was retrieved and which dependencies moved |

Stay quiet in the other cases. Say nothing when the answer is already
in the live context, when the prompt shares no content words with any
prior thread, or when this session already recalled that thread.
Retrieval on a zero-overlap prompt returns nothing and costs the user
a round trip, and units dedupe by thread and type, so a second
`+recall` on a recalled thread returns what the user is reading now.

Phrase it as an offer beside the answer, never as a precondition for
one: "the prior session left notes on this, so add `+recall` if you
want them."

## When NOT To Use

- Capturing knowledge from an external article: use
  `Skill(memory-palace:knowledge-intake)`.
- Building a scratch structure inside one long conversation: use
  `Skill(memory-palace:session-palace-builder)`.
- Judging whether a summary is clear enough to hand off: that is
  `Skill(memory-palace:memory-clarity-probe)`.

## Detailed Resources

| Module | Read it for |
|--------|-------------|
| `modules/unit-schema.md` | Field semantics, type selection, worked examples |
| `modules/two-phase-extraction.md` | The sweep checklist and render rules |
| `modules/temporal-awareness.md` | Session gaps and what survives them |

## Known Limitation

The staging file is process-global. Two concurrent sessions in one
checkout can have one drain the other's units. The window is a single
turn, and the skill cannot know its own session id, which is why
staging exists rather than direct record writes.

## Exit Criteria

- [ ] Phase 1 names the thread count before any unit is written
- [ ] Every unit carries all seven fields and a `Type` from the four
- [ ] A thread holding a durable result and the transient action that
      produced it is emitted as two units with different types
- [ ] Units land in `data/state/handoff_units.json` and it parses as
      JSON with a top-level `units` array
- [ ] On resume, elapsed time since the prior session is stated before
      any `state` unit is acted on
- [ ] Open threads carry a non-empty `Open` field
- [ ] A `+recall` offer names the thread it would retrieve, and is made
      at most once per thread per session
