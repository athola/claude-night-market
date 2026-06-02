# Independent Verification

For high-stakes changes, the agent that produced the work may not
be its sole verifier. A second, independent check is required.

## Why Self-Verification Is Not Enough

Automation-bias research is blunt about the failure mode: correct
decision support cut clinician errors by roughly 40%, but
*incorrect* support raised them by 25-33% and reduced independent
verification at the same time (medicine, e-prescribing studies).
Trust silently collapses verification precisely when the aid is
wrong. An agent reviewing its own output inherits the same blind
spot that produced the error: it is anchored to its own framing
and most confident exactly where it is most mistaken.

Iterative self-refinement does not rescue this. Critical
vulnerabilities rose 37.6% after five rounds of LLM self-refinement
(Shukla et al. 2025): asking the same model to check its own work
again can degrade it, not improve it.

High-stakes domains all forbid sole self-verification for
consequential steps: nuclear procedures require a separate
qualified individual to confirm critical actions (independent
verification, distinct from self-checking); finance separates the
maker from the checker (the four-eyes principle). The rule
transfers directly.

## The Rule

For a change classified high-stakes (see
`leyline:risk-classification` RED or CRITICAL, or any change to
auth, migrations, money handling, concurrency, or destructive
operations), the producing agent must not be the only thing that
verifies it. Require at least one independent check:

- a **second agent or model** that did not see the first one's
  reasoning, evaluating against the requirement rather than the
  diff's narrative;
- a **separate automated gate** the producer did not write or tune
  (independent test suite, static analysis, fuzzing); or
- a **human reviewer**.

The verifier evaluates against the original requirement, not
against the producer's explanation of what it did. Being handed the
producer's narrative re-anchors the second check to the first one's
blind spot, which is the thing independent verification exists to
break.

## What Counts as Independent

| Check | Independent? | Why |
|-------|-------------|-----|
| Same agent re-reading its diff | No | Anchored to its own framing |
| Same agent running tests it wrote | Partial | Tests encode the same assumptions |
| Fresh agent reviewing against the spec | Yes | No exposure to the producer's reasoning |
| CI / static analysis the producer did not tune | Yes | Independent ruleset |
| Human reviewer | Yes | Independent judgment |

## Progress Tracking

- `proof:independent-verified`: a second independent actor
  confirmed the high-stakes change against the requirement.

Record who or what performed the independent check and what they
evaluated against, as part of the evidence log. For the four-eyes
audit trail (which prompt, which agent, which diff, who approved
and why), see `leyline:usage-logging`.

## When This Does Not Apply

Low-stakes, reversible changes do not need a second verifier;
proof-of-work evidence from the producer is sufficient. Reserve
independent verification for the changes where being wrong is
expensive or hard to undo. Applying it everywhere turns it into
ceremony and trains reviewers to rubber-stamp, which is the exact
degradation it exists to prevent.
