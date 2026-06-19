# ADR-0012: Confidence-Tagged Agent Claims (VERIFIED / INFERRED / ASSUMPTION)

**Date**: 2026-05-06
**Status**: Superseded by ADR-0017
**Deciders**: Claude Night Market maintainers
**Source**: Issue #458, Discussion #448 Pattern 1

## Context

The April 2026 tome research pass for ``imbue:karpathy-principles``
surfaced a pattern from
[crisnahine/rails-ai-context](https://github.com/crisnahine/rails-ai-context)
(126 stars, Ruby/Rails MCP server): every agent introspection result
carries one of three explicit tags.

- ``[VERIFIED]``: confirmed via tool call in this turn
- ``[INFERRED]``: derived from verified facts but not directly
  checked
- ``[ASSUMPTION]``: believed without evidence

The distinctive guideline from rails-ai-context, verbatim:

> Never reference a column, association, route, helper, method,
> class, partial, or gem not verified in THIS project via a tool
> call in THIS turn.

This is a stronger version of Karpathy Principle 1 (Think Before
Coding). Our current AP-1 says "list silent assumptions"; this
pattern enforces a typed assumption discipline at the
line-of-output level. Every claim the agent emits carries its
epistemic status.

## Operational forms considered

| Form | What it does | Tradeoff |
|------|--------------|----------|
| Hook scanning agent output for unmarked factual claims | Hard regex; high false-positive rate | Low precision, hard to specify |
| Skill that retrains output style for one tag per claim | Forces typed output | Large prose-style change; conversational tone disruption |
| Style guide encouraging tags for ambiguous statements | Lightweight; opt-in | Easily ignored; no enforcement |
| Per-domain pilot inside one skill family (e.g. imbue introspection output) | Bounded scope | Cannot test cross-skill effects |

None is a small surgical edit. Each has a different cost/benefit
profile.

## Decision

**Defer adoption.** The pattern is promising but the operational
form is unclear and the prose disruption is real. Adopt only after:

1. A two-week pilot inside ``imbue`` introspection output (catchup
   summaries, justify reports, structured-review findings) that
   measures:
   - Reader uptake: do reviewers find the tags helpful?
   - Tag fidelity: how often are claims correctly classified?
   - Prose drag: does conversational tone degrade?
2. A pilot exit decision (pursue / merge into AP-1 / drop) that
   updates this ADR with the data.

Until the pilot runs, the existing AP-1 ("list silent assumptions")
remains the framework's canonical defense.

## Consequences

### If we eventually adopt

- Stronger calibration of agent output: readers can distinguish
  facts from inferences without re-checking sources.
- Stronger pre-flight discipline: the agent self-classifies each
  claim, surfacing under-supported assertions before they become
  bugs.

### If we drop

- AP-1 still requires assumption listing; we lose only the
  per-claim granularity, not the overall defense.

## Acceptance criteria

- [x] ADR drafted with sources, alternatives, recommendation
  (this document)
- [x] Decision recorded (defer pending pilot)
- [ ] If pursued: pilot scope and exit criteria specified in a
  follow-up update to this ADR

## Source

- Issue #458 (origin)
- Discussion #448 (deferred patterns from karpathy research)
- Reference repo: <https://github.com/crisnahine/rails-ai-context>
- April 2026 tome dispatch on karpathy-principles
- Related skill: ``plugins/imbue/skills/karpathy-principles/``
