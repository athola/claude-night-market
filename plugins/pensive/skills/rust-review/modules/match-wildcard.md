---
module: match-wildcard
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 550
tags: [match, exhaustiveness, wildcard, enums, unreachable]
---

# Match Wildcard

A `match` over an enum is one of Rust's best safety nets: add a variant,
and every non-exhaustive `match` becomes a compile error pointing you at
the code to update. A wildcard `_ =>` arm cuts that net. This dimension
flags the catch-all arms that trade a compile error for a runtime panic
or a silent drop.

## What This Detects

The analyzer (`analyze_match_exhaustiveness`) flags three wildcard arm
shapes:

1. **`_ => unreachable!(...)`**: claims the wildcard can never be hit.
   Add a variant and the claim is false: it panics at runtime instead of
   failing to compile.
2. **`_ => panic!(...)` / `todo!()` / `unimplemented!()`**: the same
   exhaustiveness defeat, hidden behind a deliberate crash.
3. **`_ => {}`**: an empty arm that silently swallows every unmatched
   case; a new variant is dropped with no trace.

A `_ =>` arm that returns a real value (`_ => 0`, `_ => Color::Black`)
is **not** flagged: that is a legitimate default, common and correct
over open sets like integers, `char`, and strings.

## Why Exhaustiveness Matters

The Rust Reference match chapter
(`src/expressions/match-expr.md`) requires match arms to be exhaustive,
and a wildcard `_` pattern satisfies that by matching everything left
over. That is exactly the problem for a *closed* set like an enum: the
compiler can prove you covered every variant, but a `_` arm tells it not
to bother. The protection you paid for, an error when the type grows,
is gone.

## The Fix

```rust
// Flag: a new Shape variant becomes a runtime panic
match shape {
    Shape::Circle(r) => area_circle(r),
    Shape::Square(s) => s * s,
    _ => unreachable!(),
}

// Exhaustive: adding Shape::Triangle is now a compile error
match shape {
    Shape::Circle(r) => area_circle(r),
    Shape::Square(s) => s * s,
    Shape::Triangle(b, h) => 0.5 * b * h,
}
```

When you truly want a default for several variants, name them or use an
or-pattern (`Shape::Circle(_) | Shape::Square(_) => ...`) so the set
stays explicit. If a no-op is intentional, list the variants and add a
comment, rather than letting `_ => {}` absorb future ones.

## Exclusions (Not Flagged)

- **Default values**: `_ => <expr>` returning a real value is a normal
  open-set default (integers, `char`, `&str`).
- **Named catch-alls**: `other => handle(other)` binds the value and is
  not a bare wildcard.
- **Comments**: a wildcard arm shown in a `//` or `///` comment is not
  code.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::wildcard_enum_match_arm` | `_` arm over enum variants |
| `clippy::match_wildcard_for_single_variants` | `_` covering one named variant |
| `clippy::wildcard_in_or_patterns` | `_` mixed into an or-pattern |

Enabling `#[deny(clippy::wildcard_enum_match_arm)]` on enum-heavy
modules is the durable enforcement once the existing arms are fixed.

## Output Section

```markdown
## Match Wildcard
### Issues Found
- [file:line] `_ => unreachable!()`: a new enum variant becomes a
  runtime panic; list the variants explicitly
  (clippy::wildcard_enum_match_arm)
- [file:line] `_ => {}`: empty wildcard silently drops unmatched cases
  (clippy::wildcard_enum_match_arm)
```

## Exit Criteria

- [ ] `_ => unreachable!()` arms are flagged as wildcard_unreachable
- [ ] `_ => panic!`/`todo!`/`unimplemented!` arms are flagged as
  wildcard_panic
- [ ] `_ => {}` empty arms are flagged as wildcard_empty_arm
- [ ] `_ =>` arms returning a real value and named catch-alls are not
  flagged
- [ ] The open-set exclusion (integers/char/strings) is documented
