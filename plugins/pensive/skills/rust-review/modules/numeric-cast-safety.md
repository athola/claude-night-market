---
module: numeric-cast-safety
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 600
tags: [casts, truncation, precision, try-from, numeric]
---

# Numeric Cast Safety

The `as` operator never fails and never warns. It silently truncates,
wraps, changes sign, and drops precision. This dimension flags the casts
where the shape alone proves a loss is possible, so the author can reach
for a checked conversion instead.

## What This Detects

The analyzer (`analyze_numeric_cast_safety`) flags three shapes:

1. **Length truncation**: `.len()`, `.count()`, or `.capacity()` (each
   returns `usize`, 64-bit on common targets) cast to a narrower
   fixed-width integer, e.g. `buf.len() as u32`. An over-large length
   wraps to a small wrong value (`clippy::cast_possible_truncation`).
2. **Narrowing to a byte**: any `as u8` / `as i8`. Nothing is narrower
   than a byte, so the cast cannot be a lossless widening; it truncates
   the upper bits, and `u8`/`i8` swaps reinterpret sign
   (`clippy::cast_possible_truncation`).
3. **Precision loss to `f32`**: any `as f32`. From `f64` it drops
   mantissa bits; from `i64`/`u64` it loses precision past 2^24
   (`clippy::cast_precision_loss`).

## Why `as` Hides Bugs

The Rust Reference type-cast rules
(`src/expressions/operator-expr.md`) spell out the silent behavior:

- "Casting from a larger integer to a smaller integer (e.g. `u32` ->
  `u8`) will truncate."
- Float-to-int "rounds towards zero", `NaN` becomes `0`, and
  out-of-range values "saturate" to the type's min/max instead of
  erroring.
- Integer-to-float "produces the closest possible float", which past
  2^24 (`f32`) or 2^53 (`f64`) is not the original value.

None of this is a compile error and none of it warns by default, so a
truncating cast reads as deliberate even when it is a bug.

## The Fix

```rust
// Flag: a usize length truncated to u32
let n = data.len() as u32;
// Checked: an over-large length is an error, not a wrapped value
let n = u32::try_from(data.len())?;

// Flag: narrowing to a byte
let b = value as u8;
let b = u8::try_from(value)?;

// Lossless widening uses From/Into, never `as`
let wide: u64 = small.into();      // not `small as u64`
```

Use `TryFrom`/`try_into` when the conversion can fail (narrowing) and
`From`/`into` when it cannot (widening). Keep `as` only where truncation
is the documented intent (e.g. hashing, deliberate `& 0xFF`).

## Exclusions (Not Flagged)

- **Widening / index casts**: `as usize`, `as u64`, `as i64`, `as u128`
  are the common safe-widening targets and are not flagged.
- **Pointer casts**: `as *const T` / `as *mut T` are not numeric
  conversions and are skipped.
- **Inferred target**: `as _` defers the type to the compiler and is
  left alone.
- **Comments**: a cast shown in a `//` comment is not code.

The known false-positive class is a genuinely lossless `as u8`/`as i8`
on a value already known to fit; the reviewer confirms intent and the
recommendation is still the safer `try_from`.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::cast_possible_truncation` | Narrowing integer casts |
| `clippy::cast_precision_loss` | Integer-to-float precision loss |
| `clippy::cast_sign_loss` | Casts that drop or flip the sign |
| `clippy::cast_lossless` | Widening `as` that should be `from`/`into` |
| `clippy::ptr_as_ptr` | `as` pointer casts over `.cast()` |

## Output Section

```markdown
## Numeric Cast Safety
### Issues Found
- [file:line] Length truncation: `.len() as u32` truncates a usize;
  use `u32::try_from(...)` (clippy::cast_possible_truncation)
- [file:line] Narrowing to byte: `as u8` cannot widen; use
  `u8::try_from(...)` (clippy::cast_possible_truncation)
- [file:line] Precision loss: `as f32` can lose precision; prefer
  `f32::from(...)` where lossless (clippy::cast_precision_loss)
```

## Exit Criteria

- [ ] `.len()`/`.count()`/`.capacity()` cast to a narrower integer is
  flagged as a length truncation
- [ ] `as u8` / `as i8` casts are flagged as narrowing-to-byte
- [ ] `as f32` casts are flagged as precision loss
- [ ] `as usize`, pointer casts (`as *const`/`as *mut`), and `as _` are
  not flagged
- [ ] Each finding names the `TryFrom`/`From` alternative and the
  clippy lint
