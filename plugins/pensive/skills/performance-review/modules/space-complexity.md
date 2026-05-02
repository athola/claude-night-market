---
module: space-complexity
description: AST patterns for space-complexity hotspot detection
parent_skill: performance-review
category: code-quality
tags:
- space-complexity
- memory
- ast
- python
---

# Space Complexity Detectors

Three AST patterns that signal likely space-complexity hotspots.
Each detector cites the AST node it matches, the heuristic, and
a concrete fix.

## S1: Unbounded `.append()` inside nested loops (MEDIUM)

**AST shape**: `ast.Call` whose `func` is `ast.Attribute` named
`append`, found while the loop stack has depth >= 2.

**Why it matters**: A single-loop accumulator is bounded by the
input size, which is usually fine. A nested-loop accumulator
grows multiplicatively (n×m or n²) and is the typical "result
explosion" pattern that drives memory exhaustion.

**Note**: The detector deliberately does not flag single-loop
appends. They are common, expected, and rarely a hotspot. If
single-loop accumulation becomes a problem, that is a runtime
profiling concern handled by
`Skill(parseltongue:python-performance)`.

**Fix**: If the consumer can iterate, yield instead of
materialize:

```python
def all_pairs(xs):
    for x in xs:
        for y in xs:
            yield (x, y)  # streaming, O(1) space
```

When the full list is genuinely needed, document the size
bound:

```python
# Bounded: |xs| <= 100, so output <= 10000 pairs.
out = [(x, y) for x in xs for y in xs]
```

## S2: List wrapping a generator inside a reducer (LOW)

**AST shape**: `ast.Call` to one of `sum`, `max`, `min`, `any`,
`all`, `sorted`, `set`, `frozenset`, where the first arg is
itself an `ast.Call` to `list`, `dict`, `tuple`, or `set` with
an `ast.GeneratorExp` as its first argument.

**Why it matters**: `max(list(g))` allocates the full list, then
walks it. The wrapper is redundant: reducers accept generators
directly.

**Fix**:

```python
# Before
return max(list(x * 2 for x in xs))

# After
return max(x * 2 for x in xs)
```

For `sorted` / `set` the wrapper is sometimes intentional (to
force evaluation), but it's still cheaper to let `sorted` /
`set` consume the generator directly.

## S3: Per-iteration allocation inside a loop (MEDIUM)

**AST shape**: `ast.Call` inside a loop body where either:

- The `func` is an `ast.Attribute` with name `copy`, or
- The `func` is an `ast.Name` of `dict`, `list`, or `tuple`
  with a non-comprehension first argument (the comprehension
  case is a builder, not a copy).

**Why it matters**: `base.copy()` per iteration allocates a new
container N times. If only one or two fields change per
iteration, a single allocation outside the loop with selective
mutation costs less.

**Fix**: Hoist when possible.

```python
# Before
for x in items:
    snapshot = base.copy()
    snapshot["key"] = x
    out.append(snapshot)

# After (when downstream tolerates shared dict identity):
shared = {**base}
for x in items:
    shared["key"] = x
    out.append(dict(shared))  # explicit copy at the boundary
```

When the snapshots must be independent, keep `.copy()` but
move it outside the loop if possible, or use
`copy.deepcopy` once and patch.

## What is NOT in this module

- **S4 (closure capture)** was scoped in the plan but deferred:
  reliable detection requires control-flow analysis beyond
  single-pass AST. Revisit when gauntlet's graph integration
  matures.
- **Numerical-stability concerns** (precision loss, overflow):
  use `Skill(pensive:math-review)`.
- **String-builder patterns**: covered by T4 in
  `time-complexity.md` since the dominant cost is time
  (quadratic concat), not space.

## Test references

`plugins/pensive/tests/skills/test_performance_review.py`:

- `test_s1_unbounded_append_in_loop`
- `test_s2_list_wrapping_generator_in_reducer`
- `test_s3_copy_inside_loop`

Each test feeds a synthetic snippet through the visitor and
asserts the expected severity and line.
