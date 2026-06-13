---
module: idiomatic-elision
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 600
tags: [lifetimes, elision, needless-return, expression-oriented, paths]
---

# Idiomatic Elision

Flags annotations the compiler already infers. Writing what elision
supplies is noise: it hides the signature's real shape and drifts out
of sync. Two ports are detected, both grounded in the Rust Reference.

## What This Detects

The analyzer (`analyze_idiomatic_elision`) flags:

1. **Needless lifetimes**: a function with a single named lifetime and
   no type parameters where exactly one input reference uses the
   lifetime and the output reuses it. Lifetime elision already assigns
   that input lifetime to the output, so the annotation is redundant
   (`clippy::needless_lifetimes`).
2. **Needless return**: a `return <expr>;` in the function tail
   position. A block's final expression (no semicolon) is its value, so
   the explicit `return` is redundant (`clippy::needless_return`).

## Lifetime Elision

The Rust Reference (`src/lifetime-elision.md`) gives three function
rules. Two produce the common redundant annotations:

- **Rule 2 (single input)**: if exactly one lifetime appears in the
  parameters, it is assigned to all elided output lifetimes.
- **Rule 3 (`&self`)**: with a `&self`/`&mut self` receiver, `self`'s
  lifetime is assigned to all elided output lifetimes.

```rust
// Flag: one input lifetime, reused on the output (rule 2)
fn substr<'a>(s: &'a str, until: usize) -> &'a str { &s[..until] }
// Elided:
fn substr(s: &str, until: usize) -> &str { &s[..until] }

// Flag: receiver lifetime, reused on the output (rule 3)
fn name<'a>(&'a self) -> &'a str { self.name }
// Elided:
fn name(&self) -> &str { self.name }
```

Where a lifetime is still required in a path, the Reference prefers the
anonymous placeholder `'_` over inventing a named one:

```rust
fn parser(&self) -> Parser<'_> { /* ... */ }   // not Parser<'a>
impl fmt::Debug for Wrapper<'_> { /* ... */ }
```

## Needless Return

A block's tail expression (the final operand with no trailing
semicolon) is the block's value, per `src/expressions/block-expr.md`.
Adding a semicolon turns it into a statement of unit type, so the
trailing `return ...;` is redundant:

```rust
// Flag
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
// Idiomatic
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

## Exclusions (Not Flagged)

- **Load-bearing lifetimes**: two input references tied to the same
  lifetime (`fn longest<'a>(x: &'a str, y: &'a str) -> &'a str`) cannot
  be elided; elision would give the inputs *distinct* lifetimes. The
  annotation carries meaning, so it is left alone.
- **Type parameters present**: a signature like `fn f<'a, T>(...)` is
  skipped; trait bounds can require the explicit lifetime, so this is
  the conservative case.
- **Early/guard returns**: a `return` followed by more code is control
  flow, not a tail expression, and is never flagged.
- **Bare `return;`**: only `return <expr>;` is flagged; an early bare
  `return;` is left to other lints.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::needless_lifetimes` | Explicit lifetimes elision would supply |
| `clippy::needless_return` | Trailing `return` over a tail expression |
| `clippy::extra_unused_lifetimes` | Declared lifetimes never used |
| `clippy::let_and_return` | `let x = ...; return x;` over `...` |

## Output Section

```markdown
## Idiomatic Elision
### Issues Found
- [file:line] Needless lifetime: elide it; one input lifetime is
  assigned to the output (clippy::needless_lifetimes)
- [file:line] Needless return: drop `return`; the tail expression is
  the value (clippy::needless_return)
```

## Exit Criteria

- [ ] Single-input-lifetime signatures whose output reuses the lifetime
  are flagged with an elision recommendation
- [ ] Two-input shared-lifetime and type-parameter signatures are not
  flagged (load-bearing / conservative skip)
- [ ] Trailing `return <expr>;` is flagged; early guard returns and
  bare `return;` are not
- [ ] The `'_` anonymous-lifetime preference for paths is documented
