---
name: loop-optimization
description: Decides hand-vs-compiler for loop transforms (unrolling, SIMD, fusion, branchless). Use when reviewing/authoring a hot loop or tempted to hand-optimize one.
alwaysApply: false
category: cross-plugin-patterns
tags:
  - performance
  - loops
  - vectorization
  - optimization
  - code-review
tools: []
complexity: intermediate
model_hint: standard
estimated_tokens: 1150
progressive_loading: false
modules: []
dependencies: []
---

# Loop Optimization: Hand vs Compiler

A decision rule for the five common loop transformations. Its value
is knowing when manual application is redundant (the compiler already
does it) or harmful (it defeats the vectorizer or fools your
benchmark).

## When To Use

- Reviewing a hot loop and a hand-rolled transform appears (unrolled
  body, shift-instead-of-multiply, bespoke SIMD).
- Authoring a loop that profiling proved hot, deciding whether to
  optimize it by hand.
- Pushing back on a "this is faster" claim about a loop micro-opt.

## When NOT To Use

- The loop is not proven hot by a profiler. Optimize nothing first.
- Architecture-level performance (caching layers, sharding): use
  `Skill(pensive:architecture-review)`.
- Detecting complexity hotspots (O(n^2) shapes):
  `Skill(pensive:performance-review)`.

## The decision rule

1. Profile first. No loop transform without a hot loop proven by a
   profiler.
2. In compiled languages (C, C++, Rust), trust the compiler for
   loop-invariant code motion and strength reduction: both run
   automatically at `-O2`/`-O3`, so the manual form is redundant. Leave
   unrolling to the compiler as well. Unlike the other two it is not on
   by default (GCC needs `-funroll-loops`), but the compiler owns the
   profitability decision and manual unrolling routinely defeats the
   auto-vectorizer.
3. If a loop will not vectorize, fix aliasing (`restrict` /
   `__restrict__`) and loop shape first. Confirm with an optimization
   report (`-fopt-info-vec-missed`, `-Rpass-missed=loop-vectorize`).
   Reach for intrinsics last and accept the portability cost.
4. The manual transforms that still pay: explicit SIMD on loops the
   compiler misses, loop fusion (guard against register and cache
   pressure), and multi-accumulator unrolling to break a floating-point
   reduction chain the compiler legally will not reorder.
5. In Python, the levers are: hoist invariants out of the loop,
   vectorize via NumPy, fuse passes via numexpr/Numba. Do not hand-unroll
   or hand-strength-reduce: the cost is bytecode dispatch, not loop
   control.
6. Branch elimination is a separate lever from the five transforms
   above, and the compiler will not apply it for you. Reach for it only
   on a profiled hot loop whose branch outcome depends on unpredictable
   data, and only after checking the production selectivity
   distribution.
7. Validate every claimed speedup on production-distribution data.

## Per-technique reality

| Technique | Helps where | When NOT to apply by hand |
|-----------|-------------|---------------------------|
| Unrolling | C/C++/Rust FP reduction chains (multi-accumulator) | Auto-vectorizable loops (defeats vectorizer); OOO CPUs; icache pressure; Python |
| SIMD / vectorization | C/C++/Rust loops the compiler misses; Python via NumPy | Before fixing aliasing/loop shape; short trip counts; unverified that emitted SIMD runs |
| Loop fusion | Bandwidth-bound array loops; Python via numexpr/Numba | When it spills registers or mixes strided access; compute-bound bodies; blocks vectorization |
| Hoisting (LICM) | Python (no compiler does it); C/C++/Rust only when aliasing blocks the proof | `-O2`+ compiled code: redundant and can lengthen live ranges |
| Strength reduction | Compilers do it; near-useless by hand | `-O2`+ compiled code: blocks the compiler's IV analysis and vectorization |
| Branch elimination (branchless) | Hot loops whose branch tracks unpredictable data | Predictable branches; selectivity stably skewed toward one side; sorted or clustered input; before profiling |

## Branch elimination (branchless)

A separate axis from the five transforms above. Those change loop
structure. This one removes control flow from inside the body. The
compiler will not do it for you. Rewriting a conditional push as an
unconditional store plus a conditional index advance changes which
memory the loop writes, so LLVM cannot apply it as a
semantics-preserving transformation.

The lever is branch misprediction, not instruction count. A branch
whose outcome tracks unpredictable data costs roughly 15-20 cycles per
miss. A predictable branch (loop conditions, bounds checks) is close to
free and needs no treatment at all.

Worked example: filtering 1M random `f64` values against a threshold on
an Intel i7-10875H.

| Selectivity | `.filter().collect()` | Branchless |
|---|---|---|
| 1% | 0.59 ms | 1.09 ms |
| 25% | 2.69 ms | 1.05 ms |
| 50% | 3.94 ms | 1.03 ms |
| 75% | 2.75 ms | 1.02 ms |
| 99% | 1.49 ms | 1.11 ms |

Read that table as variance, not speed. Branchless does not make the
loop faster. It makes the cost independent of the data, winning the 50%
worst case by about 4x and losing the 1% best case by about 2x. The
same 50% case on sorted input runs at 0.93 ms under the ordinary
branchy filter, beating branchless outright, because a sorted predicate
predicts perfectly.

The decision therefore turns on the production selectivity
distribution, not on any single benchmark row. Apply it when the
predicate is near-random and the worst case is what hurts. Skip it when
selectivity is stably skewed, or when input arrives sorted or clustered.

Two costs the timing column hides. The output buffer is allocated at
full input length, so a 1% filter over 1M `f64` reserves 8 MB to return
80 KB. And the branchless form is harder to read, which is a
maintenance cost paid on every future edit rather than once.

Source: https://www.greyblake.com/blog/branchless-rust/

## Two traps that invalidate "it is faster"

1. Synthetic-benchmark trap. A loop micro-opt validated on reused, small,
   or synthetic input can invert to slower on production data, because
   synthetic input hides effects such as branch misprediction on real
   value distributions. Benchmark on production-distribution data with
   optimizer barriers, or do not claim the win.
2. Emitted is not executed. Auto-vectorization fails silently. "The
   compiler emitted SIMD" does not mean "SIMD ran." Confirm with codegen
   or optimization reports, not source inspection.

Both traps tie into `Skill(imbue:proof-of-work)`: a speedup claim needs
evidence on representative data, not assertion.

## Exit Criteria

- [ ] The loop in question was profiled and is genuinely hot, or the
      recommendation is "do not optimize."
- [ ] For compiled languages, unrolling/LICM/strength-reduction were
      left to the compiler unless an optimization report shows the
      compiler failed (aliasing) and the manual form was verified faster.
- [ ] Any manual SIMD was preceded by an aliasing/loop-shape fix and a
      check that the vectorized path actually executes.
- [ ] Every speedup claim cites a benchmark on production-distribution
      data, not synthetic or reused input.
- [ ] Any branchless rewrite names the branch it removes, shows that
      branch is data-dependent and mispredicting, and reports the
      selectivity range it was measured across, not a single point.
