---
module: conversion-traits
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 650
tags: [conversion, from, into, tryfrom, from_over_into, orphan-rule]
---

# Conversion Traits

Flags two conversion smells: implementing `Into` where `From` is the
preferred direction, and discarding the error of a fallible conversion
with `.unwrap()`. Both follow from the standard conversion-trait
contract: implement the most general trait, and surface (do not panic
away) the error `TryFrom` exists to report.

## What This Detects

The analyzer (`analyze_conversion_traits`) flags two shapes:

1. **`impl Into<X> for Y`**: recommend `impl From<Y> for X`. Detection
   anchors on a line-leading `impl ... Into<...> for <Type>`, so a
   generic *bound* `T: Into<U>` (which is correct) is never matched.
   `clippy::from_over_into`.
2. **`.try_into().unwrap()` / `T::try_from(..).unwrap()`** (and the
   `.expect(..)` variants): the fallible conversion's error is
   discarded. Recommend propagating it with `?` or handling it.

## Why From Over Into

The Rust API Guidelines (`C-CONV-TRAITS`) state the rule directly:

> The following conversion traits should never be implemented: `Into`,
> `TryInto`. These traits have a blanket impl based on `From` and
> `TryFrom`. Implement those instead.

The std `convert` module docs give the mechanism:

> As a library author, you should always prefer implementing `From<T>`
> or `TryFrom<T>` rather than `Into<U>` or `TryInto<U>`, as `From` and
> `TryFrom` provide ... equivalent `Into` or `TryInto` implementations
> for free, thanks to a blanket implementation in the standard library.

Implementing `From` also composes with the `?` operator: an error type
that is `From<E>` is usable in `?` through the standard error
conversion, which an `Into` impl does not wire into.

```rust
// Flag: forfeits the From direction and ?-composition
impl Into<Settings> for Config {
    fn into(self) -> Settings { Settings { timeout: self.timeout } }
}
// Preferred: From gives Into for free
impl From<Config> for Settings {
    fn from(c: Config) -> Self { Settings { timeout: c.timeout } }
}
```

## Why Not Discard the Conversion Error

`TryFrom` exists to make a fallible conversion's failure a value, not a
panic. `.try_into().unwrap()` throws that value away:

```rust
// Flag: an over-large value panics instead of being handled
let port: u16 = raw.try_into().unwrap();
// Surface the error
let port: u16 = raw.try_into()?;
```

`.unwrap()` is acceptable only where the value is statically known to
fit (tests, a checked invariant, a `const`); the reviewer confirms.

## Exclusions (Not Flagged)

- **Generic bounds**: `where T: Into<U>` and `fn f<T: Into<U>>(..)` are
  correct and idiomatic. Only line-leading `impl Into` blocks match.
- **Foreign target type (orphan rule)**: `impl Into<ForeignType> for
  Local` cannot be rewritten as `impl From<Local> for ForeignType` when
  `ForeignType` is defined in another crate; the orphan rule forbids it,
  so `Into` is the only legal direction (rust-clippy #9638, #6607). The
  detector cannot tell whether the target is foreign from one line, so
  the recommendation carries this caveat and the reviewer confirms.
- **`impl From<..>`**: already the preferred direction; never flagged.
- **Propagated conversions**: `try_into()?` keeps the error and is not
  flagged.
- **Comments**: a line in a `//` comment is not code.

The known false-positive class is the foreign-target `impl Into`; the
recommendation states the orphan-rule exception inline so the reviewer
can dismiss it without re-deriving the rule.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::from_over_into` | `impl Into` where `impl From` suffices |
| `clippy::unwrap_used` | `.unwrap()` that should handle the error |
| `clippy::wrong_self_convention` | `from_`/`into_` naming conventions |

## Output Section

```markdown
## Conversion Traits
### Issues Found
- [file:line] `impl Into<X> for Y`: implement `impl From<Y> for X`
  instead (From gives Into for free); exception if X is foreign
  (clippy::from_over_into)
- [file:line] `try_into().unwrap()`: discards the conversion error;
  propagate it with `?` (clippy::unwrap_used)
```

## Exit Criteria

- [ ] Line-leading `impl Into<X> for Y` is flagged with a concrete
  `impl From<Y> for X` recommendation and `clippy::from_over_into`
- [ ] Generic bounds `T: Into<U>` and `impl From<..>` are not flagged
- [ ] `.try_into().unwrap()` and `T::try_from(..).unwrap()` are flagged
  as a discarded conversion error; `try_into()?` is not
- [ ] The foreign-target orphan-rule exception is documented in the
  recommendation
- [ ] Lines in comments are not flagged
