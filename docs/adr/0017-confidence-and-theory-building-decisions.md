# ADR-0017: Decisions on Confidence-Tagging and Theory-Building

**Date**: 2026-06-18
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Source**: Issue #572, Discussion #448 (deferred patterns)
**Supersedes**: ADR-0012, ADR-0013

## Context

Two patterns surfaced during the April 2026 tome research pass for
``imbue:karpathy-principles`` and were captured as research records
in ADR-0012 (confidence-tagged agent claims) and ADR-0013 (Naur
theory-building for LLM-assisted code). Both recorded the pattern
and then deferred the call to a future pilot.

This ADR closes that deferral. The pilots in ADR-0012 and ADR-0013
were never scheduled, and leaving two patterns in a permanent
"Proposed" state is itself a decision debt: readers cannot tell
whether the framework intends to adopt them. We make the call now.

- Pattern 1 (confidence tagging): every agent claim carries one of
  ``[VERIFIED]`` (confirmed by a tool call this turn),
  ``[INFERRED]`` (derived from verified facts), or
  ``[ASSUMPTION]`` (believed without evidence).
- Pattern 2 (theory-building): per Naur's 1985 "Programming as
  Theory Building", the question is whether the human still
  understands the code after the model writes it.

Both patterns extend the Karpathy principles already encoded in
``plugins/imbue/skills/karpathy-principles/``. Pattern 1 hardens
AP-1 (Think Before Coding); Pattern 2 covers a layer the four
principles do not: human comprehension after the diff lands.

## Decision

### Decision 1: Confidence tagging: defer enforcement

**Do not build an enforcement mechanism. Permit voluntary use.**

No automated mechanism will scan or gate agent output for
confidence tags. The reasons are concrete, not provisional.

- **False-positive cost.** The only enforcement path is a scanner
  that flags unmarked factual claims. Distinguishing a factual
  claim from narration, a question, or a hypothetical is a hard
  natural-language problem. A high false-positive rate trains
  authors to ignore or suppress the check, which is worse than no
  check.
- **No surgical enforcement path.** Every operational form in
  ADR-0012 is large or imprecise: a hook scanner (low precision),
  an output-style retrain (broad prose disruption), or a per-claim
  style mandate (conversational-tone damage). None is a small,
  reversible edit, so none clears the bar for a framework-wide
  default.

Voluntary adoption is allowed and encouraged where it is cheap and
high-signal. Agent and skill authors may add the three tags to
introspection output (for example catchup summaries, justify
reports, structured-review findings) in their own prompts without
any framework gate. AP-1's existing "list silent assumptions"
remains the canonical, enforced defense.

### Decision 2: Theory-building: adopt the lightest form

**Adopt the senior-engineer self-check as the theory-building
form: a single optional recommendation, no hard gate. Wiring it
into ``imbue:karpathy-principles`` is tracked separately (see the
acceptance criteria below), so this ADR records the decision, not
a completed skill change.**

The adopted form is the single self-check question:

> Could I explain what this code does and why, without re-reading
> the model's transcript?

It is recommended after any non-trivial LLM-authored diff. If the
answer is no, the recommended response is to slow down: read the
diff, rebuild the mental model, or rewrite the unclear part by
hand.

Why this form over the alternatives in ADR-0013:

- It is the cheapest. It adds zero output tokens and no ceremony,
  so it avoids the "formulaic narrative" failure mode that the
  2-sentence-summary variant risks.
- It targets the actual concern (human comprehension) directly,
  rather than proxying it through commit-authorship ratios that
  are hard to define and easy to game.
- As a recommendation rather than a gate, it carries no
  false-positive cost and is fully reversible.

The 2-sentence narrative summary from ADR-0013 remains available as
an optional escalation when a reviewer explicitly wants a written
theory-recovery surface (for example on a large or high-risk PR).
It is not a default.

This is a recommendation, not enforcement. It lives as guidance in
the karpathy-principles skill, the same place AP-1 through AP-4
live. Nothing fails CI for skipping it.

## Consequences

### Positive

- Two long-open patterns reach a recorded decision instead of
  sitting indefinitely in "Proposed".
- The theory-building check costs nothing to run and addresses a
  real gap (comprehension after AI-authored changes) that the four
  Karpathy principles do not.
- Confidence tagging stays available to authors who find it useful
  without imposing a high-false-positive gate on everyone.

### Negative

- Neither pattern is enforced, so neither is guaranteed to be
  applied. We accept this: enforcement cost exceeds expected
  benefit for both, given current evidence.
- A future change in evidence (a low-false-positive tagger, or
  data showing comprehension loss despite the self-check) would
  warrant revisiting. Such a change should supersede this ADR
  rather than silently amend it.

## Acceptance criteria

- [x] Confidence-tagging decision recorded: defer enforcement,
  permit voluntary use, with stated rationale
- [x] Theory-building decision recorded: adopt the
  senior-engineer self-check as an optional recommendation
- [x] ADR-0012 and ADR-0013 marked as superseded by this ADR
- [x] Follow-up landed: the karpathy-principles skill carries the
  self-check as optional guidance in its senior-engineer-test
  module (tracked separately from this ADR's decision)

## Source

- Issue #572 (origin)
- Discussion #448 (deferred patterns from karpathy research)
- ADR-0012 (confidence-tagged agent claims, superseded)
- ADR-0013 (Naur theory-building, superseded)
- Naur 1985: "Programming as Theory Building"
- Related skill: ``plugins/imbue/skills/karpathy-principles/``
