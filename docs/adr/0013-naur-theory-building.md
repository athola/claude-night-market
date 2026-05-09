# ADR-0013: Operationalizing Naur Theory-Building for LLM-Assisted Code

**Date**: 2026-05-06
**Status**: Proposed (research, not yet adopted)
**Deciders**: Claude Night Market maintainers
**Source**: Issue #459, Discussion #448 Pattern 2

## Context

The April 2026 tome research pass surfaced an HN thread,
[After two years of vibecoding, I'm back to writing by
hand](https://news.ycombinator.com/item?id=46765460) (865 points,
634 comments). The dominant framing invokes Peter Naur's 1985
paper "Programming as Theory Building": the artifact a programmer
produces is the mental model, not the source code. Source code
without a maintained theory in someone's head is legacy code from
day one.

Practitioner evidence:

> You HAVE to write the code yourself sometimes. Like
> weightlifting, the effort itself builds the strength that lets
> you debug the next thing.

Bram Cohen (BitTorrent) reinforces from the
[opposite angle](https://news.ycombinator.com/item?id=47664912):

> I frequently have to throw away their massively verbose and
> ridiculously complex code.

The code lacks a theory the maintainer can reconstruct quickly,
so replacement is cheaper than repair.

Karpathy Principles 1-4 prevent the model from writing bad code.
Theory-building is about whether the *human* still understands
what the code does after the model writes it. Different layer;
complementary defense.

## Operational variants considered

| Variant | What it does | Tradeoff |
|---------|--------------|----------|
| Senior-engineer-test question: "Could I explain this code without re-reading the LLM transcript?" | Lightweight; relies on agent self-report | Easily fooled by motivated reasoning |
| New module ``theory-maintenance.md`` (reference doc + checklist) | Adds scaffolding | May be ignored; doesn't change behavior |
| Behavior change: agent must produce a 2-sentence narrative summary alongside any non-trivial diff | Forces theory articulation | Increases output volume; may fragment focus |
| Audit: periodic check that the human has written N% of recent commits by hand | Quantitative discipline | Hard to define "by hand"; may game |

Each variant has tradeoffs. None is a clear winner without data.

## Decision

**Defer adoption.** The principle is sound but the operational
form is unclear. Run a pilot before committing the framework to
one variant.

### Pilot plan

Apply the **2-sentence narrative summary** variant to one
workflow (``/sanctum:do-issue`` completion phase) for two weeks.
Capture:

1. Reader uptake: do reviewers read the narrative?
2. Theory recovery: ask reviewers a week after merge, "what does
   this PR do?" without showing them the diff. Does the narrative
   help them answer?
3. Prose drag: does it feel like ceremony, or signal?

The 2-sentence variant is the lowest-cost test; the audit variant
is the highest-cost. Pilot the cheap one first; escalate if data
warrants.

## Consequences

### If we eventually adopt the narrative variant

- Reviewers gain a fast theory-recovery surface.
- Agent output volume grows by ~50 tokens per non-trivial diff.
- Risk: narratives become formulaic ("This PR adds X. It is
  needed because Y.") and lose signal value.

### If we drop

- Karpathy AP-4 (Goal-Driven Execution) and existing PR-template
  prompts continue to carry the load. We lose the defense against
  theory-loss but pay no extra cost.

## Acceptance criteria

- [x] ADR drafted with variants, recommendation, pilot scope
  (this document)
- [x] Decision recorded (defer pending pilot)
- [ ] If pursued: pilot result documented with theory-recovery
  observations as an update to this ADR

## Source

- Issue #459 (origin)
- Discussion #448 (deferred patterns from karpathy research)
- HN thread: <https://news.ycombinator.com/item?id=46765460>
- Bram Cohen counterpoint: <https://news.ycombinator.com/item?id=47664912>
- Naur 1985: "Programming as Theory Building"
- Related skill: ``plugins/imbue/skills/karpathy-principles/``
