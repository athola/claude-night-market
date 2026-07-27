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
complexity and duplication while refactoring collapses. Every
fallback that hides an impossible case is a bug that will
surface later as silent corruption instead of a loud,
locatable failure. Strong invariants keep a codebase legible
and human-supervisable, which is the property the coming
harness loops most threaten.

**Evidence base:**

| Source | Finding |
|--------|---------|
| GitClear 2025 (211M changed lines) | Copy-pasted lines rose 8.3% (2021) to 12.3% (2024); duplicated blocks rose roughly 8x; refactoring fell from 25% of changed lines to under 10%; two-week churn nearly doubled |
| DORA 2024 | Each 25% increase in AI adoption is associated with a 7.2% drop in delivery stability and a 1.5% drop in throughput, even as perceived productivity rose |
| METR RCT 2025 (arXiv 2507.09089) | 16 experienced OSS developers, 246 tasks in mature repos: AI tools increased completion time 19% while developers believed they were 20% faster |
| Cognitive-bias study (arXiv 2601.08045) | 48.8% of observed programmer actions were biased; developer-LLM interaction accounted for 56.4% of those |
| Karpathy, "mortal terror of exceptions" | LLMs add defensive handlers for near-impossible cases because RL punishes exceptions. The primary source for this rule's core claim |

Caveats that bound these numbers: GitClear and DORA are
observational, so they establish correlation, not causation.
Defensive bloat specifically is under-measured; duplication
and churn are quantified, over-defensive code is mostly
anecdotal plus Karpathy. A Google enterprise RCT (arXiv
2410.12944) found AI sped 96 engineers about 21%, which cuts
the other way; context explains the split, since that was a
greenfield-style task rather than a mature repo with expert
maintainers.

**References:**

- Armin Ronacher, "The Coming Loop" (2026),
  https://lucumr.pocoo.org/2026/6/23/the-coming-loop/
- Karpathy on LLMs and exceptions,
  https://x.com/karpathy/status/1976077806443569355
- GitClear 2025,
  https://www.gitclear.com/ai_assistant_code_quality_2025_research
- DORA 2024, https://dora.dev/research/2024/dora-report/
- METR RCT, https://arxiv.org/abs/2507.09089
- `Skill(imbue:scope-guard)` (over-abstraction, sibling guard)
- `Skill(leyline:additive-bias-defense)` (challenge every addition)
- `Skill(pensive:safety-critical-patterns)` (the deliberate exception)
