---
module: float-equality
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 500
tags: [float, ieee-754, equality, epsilon, precision]
---

# Float Equality

`f32` and `f64` are IEEE-754 types whose arithmetic rounds. Two values
that are mathematically equal often differ in their last bits, so an
exact `==` or `!=` test silently does the wrong thing. This dimension
flags equality comparisons against a floating-point literal so the author
switches to a tolerance.

## What This Detects

The analyzer (`analyze_float_equality`) flags `==` and `!=` where one
operand is a floating-point literal. A float literal is recognized by a
decimal point (`1.5`, `0.0`) or a float type suffix (`2f32`, `1.0f64`).
The literal may sit on either side of the operator:

- `ratio == 1.5`
- `3.14 == angle`
- `total != 0.0`
- `x == 2.0f32`

An integer literal (`count == 5`) has neither a decimal point nor a
float suffix and is left alone, as is every ordering comparison
(`x >= 1.5`), which is well defined on floats.

## Why Exact Comparison Misleads

The Rust Reference defines `f32`/`f64` as IEEE-754 single and double
precision (`src/types/numeric.md`). The classic demonstration is
`0.1 + 0.2 != 0.3`: each literal is rounded to the nearest representable
value, the sum carries its own rounding, and the result is one bit away
from the literal `0.3`. The comparison compiles, runs, and quietly takes
the wrong branch. Exact-zero checks (`== 0.0`) are sometimes intentional,
but even those are usually better written against a small epsilon.

## The Fix

```rust
// Flag: exact equality on a rounded value
if ratio == 1.5 { adjust(); }

// Checked: compare the magnitude of the difference to a tolerance
if (ratio - 1.5).abs() < f64::EPSILON { adjust(); }

// A domain epsilon is clearer when units have scale
const TOL: f64 = 1e-6;
if (measured - expected).abs() < TOL { accept(); }
```

Compare `(a - b).abs()` to `f64::EPSILON` (or `f32::EPSILON`) for values
near 1.0, or to a domain-specific tolerance when the quantities are large
or small. Where you truly need exact bits (round-trip serialization, a
sentinel), compare the bit pattern with `a.to_bits() == b.to_bits()` and
say why in a comment.

## Exclusions (Not Flagged)

- **Integer comparisons**: `count == 5` has no float literal.
- **Ordering comparisons**: `<`, `<=`, `>`, `>=` are well defined on
  floats and never match.
- **Ranges**: `0.0..1.0` uses `..`, not an equality operator.
- **Comments**: a comparison shown in a `//` comment is not code.

A known limitation is a float literal inside a string on the same line;
this conservative, line-based pass does not strip string contents.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::float_cmp` | `==`/`!=` between floating-point values |
| `clippy::float_cmp_const` | Exact comparison against a const float |
| `clippy::float_equality_without_abs` | Difference compared without `abs` |

## Output Section

```markdown
## Float Equality
### Issues Found
- [file:line] Exact float comparison `ratio == 1.5`; rounding makes
  `==` unreliable. Compare `(ratio - 1.5).abs() < f64::EPSILON`
  (clippy::float_cmp)
```

## Exit Criteria

- [ ] `==`/`!=` against a decimal float literal (`1.5`, `0.0`) is flagged
- [ ] A type-suffixed literal (`2f32`, `1.0f64`) is flagged
- [ ] A literal on either side of the operator is flagged
- [ ] Integer comparisons, ordering comparisons, and ranges are not
  flagged
- [ ] Each finding names the epsilon/tolerance alternative and
  `clippy::float_cmp`
