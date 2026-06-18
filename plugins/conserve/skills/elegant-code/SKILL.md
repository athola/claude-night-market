---
name: elegant-code
description: Guide minimal code via a decision ladder with full safety, edge, and negative-case coverage. Use when adding code, choosing a dependency, or auditing a diff.
alwaysApply: false
category: conservation
tags:
- minimalism
- yagni
- decision-ladder
- dependency-discipline
- additive-bias
tools: []
complexity: low
model_hint: fast
estimated_tokens: 900
---

# Elegant Code

> Write the minimal, elegant code that fully solves the problem:
> its performance, its edge cases, and its failure cases. Minimal
> is not fewest lines. It is no incidental complexity, with
> nothing essential omitted.

## What this skill is (and is not)

This skill codifies a discipline that strong models already
exhibit *some* of the time. Its value is not teaching a missing
capability. Its value is three things:

1. A shared **vocabulary** (the rungs, the floor) that review
   skills can point at, so "you skipped rung 2" is a concrete,
   auditable note.
2. **Consistency**: the ladder is applied every time, not just
   when the model happens to think of it.
3. A **guard**: the negligence floor below is never traded away
   for brevity.

It is the generative counterpart to the review-side contract in
`leyline:additive-bias-defense`.

## When To Use

- Before adding a function, file, class, abstraction, or
  dependency.
- When choosing between reuse and writing new code.
- When auditing a diff for lines that can be deleted.

## When NOT To Use

- Throwaway scripts or one-time migrations where review cost is
  near zero.
- Cases where the negligence floor (below) is in play: there,
  add the guard first and optimize length second.

## The Decision Ladder

Walk the rungs in order. Climb down only when the current rung
does not hold. Stop at the first rung that solves the problem.

| # | Rung | Ask | Stop here when | Example |
|---|------|-----|----------------|---------|
| 1 | Need-to-exist | Does this need to exist at all? | The requirement is speculative or already met. Delete or defer. | "Config loader for a value used once" -> inline the value |
| 2 | Builtin / stdlib | Can a language builtin or the standard library do it? | The stdlib covers it. | `str.zfill`, `f"{n:05d}"`, `pathlib`, `itertools` |
| 3 | Native platform | Is there a native platform or framework feature? | The platform already ships it. | `URLSession` retry, `fetch`, framework validators |
| 4 | Installed dependency | Is an already-installed, audited dependency enough? | A dep in the lockfile covers it. | reuse `requests`/`urllib3` backoff before adding `tenacity` |
| 5 | A few lines | Can it be one line or a small explicit block? | A short, obvious block solves it. | a 20-line retry loop over a retry framework |

A *new* dependency is the last resort, below rung 5, not rung 4.
Before adding one, verify it actually exists and is safe with
`Skill(imbue:dependency-verification)`: generated code imports
non-existent packages at measurable rates, and recurring fake
names enable slopsquatting (arXiv 2406.10279, USENIX 2025).

Prefer reuse of an installed, audited dependency over both a new
dependency and a hand-rolled reinvention. Zero-dependency code is
not automatically cheaper: it relocates the maintenance and bug
surface into your own tree (see `references/sources.md`).

## What minimal must still cover

Minimal does not mean fewest lines. It means no incidental
complexity, with nothing essential omitted. The decision ladder
removes incidental code: reinvention, speculative abstraction,
needless dependencies. Three things are essential and are never
traded for brevity.

### Correctness and safety (the negligence floor)

Never cut for brevity. A review must never propose deleting these
as "extra code":

- Trust-boundary and input validation on untrusted data.
- Authorization checks (permission gates, row-level security).
- Data-loss handling (transactions, idempotency keys, retries
  that cannot double-charge).
- Error handling on fallible I/O.
- Security-relevant paths (authn, secrets, crypto).
- Accessibility.

This floor is evidence-backed, not a slogan. The dangerous
failure mode in generated code is *omission*: roughly 45% of
AI-generated samples carry a security flaw, with a measured
~2.74x vulnerability rate versus human code, driven by missing
validation, missing authorization, and missing error handling
(Veracode 2025). CVE-2025-48757 is a concrete case: generated
schemas shipped without row-level security policies. An absent
guard is not zero bugs. It is one latent bug per untrusted input.

### Performance

Handle the expected input size and the hot path: avoid accidental
quadratic loops, N+1 queries, and unbounded memory growth. Do not
micro-optimize speculatively. Premature, speculative optimization
is itself incidental complexity, so YAGNI applies to performance
too. Optimize what the known input size or a profiler justifies,
not what feels fast.

### Edge and negative cases

The negative path is part of the spec, not extra code. Cover
empty, `None`, and zero inputs; boundary values; malformed or
hostile input; partial failure and timeouts; and concurrency
where it applies. Code that handles only the happy path is not
minimal. It is unfinished.

## Elegance, not terseness

Prefer the clearest expression a reader can verify, not the
cleverest or the shortest. Terseness and cleverness raise review
cost and defect risk: dense one-liners hide edge cases, and
correctness-only evaluation misses the maintainability they cost
(arXiv 2407.11470). Elegance is minimal incidental complexity
plus maximal clarity, which is not the same as minimal characters.

## Why minimal (stated honestly)

The case for less code rests on surfaces you can measure, not on
a clean "fewer lines means fewer bugs" law. That law is not
empirically settled: studies find weak or absent correlation
between complexity metrics and defect rate (arXiv 1912.01142,
1912.04014). Argue instead from:

- **Attack surface**: fewer imports and branches are fewer places
  for a known failure mode (hallucinated import, unhandled path).
- **Review cost**: a document, and a diff, costs the sum of its
  readers' time. Less code is less to review correctly.
- **Token and latency cost**: shorter output is cheaper to
  generate and faster to run.
- **Iteration risk**: additive self-refinement is not free. One
  study measured a +37.6% rise in critical vulnerabilities after
  five refinement rounds (arXiv 2506.11022). Bias the loop toward
  deletion, then stop.

## Verification hooks

After writing, cross-check deletability with real tools instead
of guessing from the diff. Gate each behind `command -v` and fall
back cleanly when absent.

```bash
# JS/TS: unused files, exports, dependencies
command -v knip >/dev/null && knip || echo "knip absent; skipping"

# Python: dead code
command -v vulture >/dev/null && vulture . || echo "vulture absent; skipping"

# Rust: unused dependencies (nightly)
command -v cargo-udeps >/dev/null && cargo +nightly udeps \
  || echo "cargo-udeps absent; skipping"
```

Treat tool output as *candidates*, not verdicts. Code reachable
only via reflection, dynamic dispatch, or framework magic can be
flagged as dead while being live. Cross-check against the
negligence floor before deleting anything.

## How this composes

| Skill | Relationship |
|-------|--------------|
| `imbue:dependency-verification` | Rung 4/new-dep gate: confirm a package exists before adding it |
| `leyline:additive-bias-defense` | Review-side burden-of-proof contract this skill generates against |
| `conserve:code-quality-principles` | KISS/YAGNI principles this ladder operationalizes pre-code |
| `conserve:unbloat` | Whole-codebase cleanup (this skill is per-change) |
| `imbue:scope-guard` | Feature-level worthiness (this skill is line and dependency level) |
| `pensive:harden` | Security review that enforces the negligence floor |

The `/conserve:elegant-code-review` command applies this ladder to
the current working diff.

## Exit Criteria

- [ ] Each addition was walked down the ladder, and the chosen
      rung is stated (for example, "rung 2: stdlib `zfill`").
- [ ] Any new dependency passed `Skill(imbue:dependency-verification)`
      and reuse of an installed dependency was ruled out first.
- [ ] Every untrusted input has its negligence-floor guard present
      (validation, authorization, error handling).
- [ ] A deletion tool was run, or its absence was noted, and no
      flagged candidate that is a guard was deleted.
