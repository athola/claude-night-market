---
description: Prefer unrepresentable illegal states over defensive fallbacks in internal code
alwaysApply: true
---

**Make illegal states unrepresentable before you guard
against them!**

Language models are, in Karpathy's words, "mortally
terrified of exceptions." Trained to avoid failure, they
over-produce defensive handlers, fallback defaults, and
try/except blocks for near-impossible cases instead of
designing the impossible case out of existence. Armin
Ronacher's "The Coming Loop" names this as a core failure
mode of agentic coding: code that is "too defensive, too
complex, too local in its reasoning" and "avoids strong
invariants." This rule is the counter-pressure.

**Before adding a defensive guard, ask one question:**

Can this illegal state be made unrepresentable instead of
handled? Reach for the invariant first:

- Encode the constraint in a type or a constructor so the
  bad value cannot be built (parse, don't validate).
- Establish the invariant once at a boundary, then trust
  it downstream instead of re-checking it everywhere.
- Let an exception propagate when the caller cannot
  meaningfully recover. A crash with a clear stack trace
  beats a silent fallback that corrupts state and hides
  the bug.

**The load-bearing distinction (keep vs. remove):**

| Keep the defensive handling | Remove it |
|-----------------------------|-----------|
| Untrusted input, network, filesystem, FFI, subprocess | Redundant None-check after guaranteed construction |
| Genuinely fallible I/O with a real recovery path | Fallback default that masks missing or malformed data |
| Safety-critical defense-in-depth (see below) | catch-and-continue on a programming error |
| A contract at a public API boundary | Belt-and-suspenders re-validation of an internal invariant |

The test: does the guard defend against the *outside
world*, or against a state your own code already
guarantees cannot occur? Defend boundaries. Delete guards
that paper over unclear internal design; fix the design.

**Detection heuristics (surface, then judge):**

- Broad `except Exception:` or bare `except:` around code
  that only throws on programmer error
- A fallback value (`or {}`, `?? []`, `getattr(x, k,
  default)`) standing in for data that should always exist
- A None/null check on a value a constructor or prior
  invariant guarantees is set
- Two layers validating the same internal condition
- An error swallowed and logged where propagation was the
  correct response

**When this rule does NOT apply:**

- Trust boundaries. Validating untrusted or external input
  is correct and required; this rule never argues against
  it.
- Safety-critical code. `pensive:safety-critical-patterns`
  (NASA Power of Ten) *requires* defensive checks and
  assertions by design. That is deliberate defense-in-depth
  at a boundary, not the internal-invariant bloat this rule
  targets. When the two seem to conflict, safety-critical
  wins.
- Do not strip a guard whose comment or context marks it as
  intentional (mirrors the anti-goals in
  `slop-scan-for-docs.md`: never remove contract-bearing or
  safety checks).

**Why this rule exists:**

Defensive bloat is measurable, not aesthetic. Independent
studies find AI-accelerated codebases rising in cyclomatic
complexity and duplication while refactoring collapses (see
`docs/research/2026-07-01-the-coming-loop-agentic-harness-guardrails.md`).
Every fallback that hides an impossible case is a bug that
will surface later as silent corruption instead of a loud,
locatable failure. Strong invariants keep a codebase legible
and human-supervisable, which is the property the coming
harness loops most threaten.

**References:**

- `docs/research/2026-07-01-the-coming-loop-agentic-harness-guardrails.md`
  (evidence base and source citations)
- Armin Ronacher, "The Coming Loop" (2026)
- Karpathy on LLMs and exceptions (research report, source list)
- `Skill(imbue:scope-guard)` (over-abstraction, sibling guard)
- `Skill(leyline:additive-bias-defense)` (challenge every addition)
- `Skill(pensive:safety-critical-patterns)` (the deliberate exception)
