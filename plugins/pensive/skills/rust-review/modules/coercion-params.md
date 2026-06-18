---
module: coercion-params
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 650
tags: [coercion, deref, ptr_arg, borrowing, slices, parameters]
---

# Coercion Params

Flags parameters typed as an owned-type reference (`&String`, `&Vec<T>`,
`&PathBuf`) where the borrowed form (`&str`, `&[T]`, `&Path`) is strictly
more general. A borrowed-slice parameter accepts both an owned value's
borrow and an already-borrowed one through deref coercion, so the
owned-type reference needlessly narrows the callers the function admits.

## What This Detects

The analyzer (`analyze_coercion_params`) flags three parameter shapes:

1. **`&String`**: recommend `&str`. `String: Deref<Target = str>`.
2. **`&Vec<T>`**: recommend `&[T]`. `Vec<T>: Deref<Target = [T]>`.
3. **`&PathBuf`**: recommend `&Path`. `PathBuf: Deref<Target = Path>`.

Detection keys on the typed-binding form `: &Type` (predominantly
function parameters). The leading colon excludes return types
(`-> &String`), and requiring the `&` adjacent to the type name excludes
the load-bearing `&mut String` / `&mut Vec<T>` cases. An optional
lifetime (`&'a String`) is tolerated. This mirrors `clippy::ptr_arg`.

## Why Coercion Makes the Borrowed Form More General

The Rust Reference type-coercions chapter (`src/type-coercions.md`)
lists deref coercion among the allowed coercions:

> `&T` or `&mut T` to `&U` if `T` implements `Deref<Target = U>`.

and lists function-call arguments as a coercion site:

> Arguments for function calls: the value being coerced is the actual
> parameter, and it is coerced to the type of the formal parameter.

Because the argument position is a coercion site, a `fn g(s: &str)`
accepts a `&String` (the compiler inserts the deref) and a `&str`. A
`fn g(s: &String)` accepts only a `&String`. The borrowed-slice
parameter is therefore a superset of the callers the owned-type
reference admits.

```rust
// Flag: only callers holding a String can call this
fn count_words(text: &String) -> usize { text.split(' ').count() }
// More general: &String and &str both coerce in
fn count_words(text: &str) -> usize { text.split(' ').count() }

// Flag
fn sum(xs: &Vec<i64>) -> i64 { xs.iter().sum() }
// More general
fn sum(xs: &[i64]) -> i64 { xs.iter().sum() }
```

## Exclusions (Not Flagged)

The deref-coercion argument only holds for a shared, immutable borrow
whose body does not need the owned type. The detector and reviewer must
leave these alone:

- **`&mut String` / `&mut Vec<T>`**: a slice cannot grow. If the body
  calls `push`, `push_str`, `clear`, `truncate`, `reserve`,
  `try_reserve`, `extend_from_slice`, `pop`, or other length-changing
  methods, the owned-type reference is required (rust-clippy #8463,
  #9067, #9542). The `&mut` form is not matched.
- **`&Box<T>`**: `clippy::ptr_arg` deliberately does not flag `&Box<T>`;
  neither does this detector.
- **Owned-only method use**: a `&Vec<T>` whose value is `.clone()`d to
  obtain an owned `Vec`, or that uses `Vec`/`String`-specific API
  (`capacity`, `as_mut_vec`), genuinely needs the owned type. This is
  beyond a single-line check; the reviewer confirms before changing.
- **Trait-fixed signatures**: a parameter type imposed by a trait
  definition or `impl Trait for T` method is a binding contract and
  cannot be narrowed (rust-clippy #8410). Confirm the signature is
  free before recommending.
- **Generic / bound positions**: deref coercion does not satisfy a
  generic type parameter; a value flowing into `T` of `fn f<T:
  Bound>(x: T)` is not coerced. Do not narrow there.
- **Macro-hidden use, FFI, and `extern` ABI**: a `Vec`-only method may
  live inside a macro the line scan cannot see; `extern "C"` signatures
  fix the concrete type. `clippy::ptr_arg` skips non-Rust ABI.
- **Comments**: a signature shown in a `//` comment is not code.

The known false-positive class is a `&Vec<T>`/`&String` parameter that
the body needs as the owned type for one of the reasons above; the
reviewer confirms the borrow is read-only and self-contained before
applying the change.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::ptr_arg` | `&String`/`&Vec<T>`/`&PathBuf`/`&Cow` params |
| `clippy::needless_pass_by_value` | Owned param taken by value, only read |
| `clippy::ptr_as_ptr` | `as` pointer casts over `.cast()` |

## Output Section

```markdown
## Coercion Params
### Issues Found
- [file:line] `&String` param: take `&str`; deref coercion accepts both,
  so `&str` is strictly more general (clippy::ptr_arg)
- [file:line] `&Vec<T>` param: take `&[T]` (clippy::ptr_arg)
- [file:line] `&PathBuf` param: take `&Path` (clippy::ptr_arg)
```

## Exit Criteria

- [ ] `: &String`, `: &Vec<T>`, and `: &PathBuf` typed parameters are
  flagged with the borrowed-slice recommendation and `clippy::ptr_arg`
- [ ] `&mut String` / `&mut Vec<T>` parameters are not flagged (the
  owned-type reference is load-bearing for growth)
- [ ] `&Box<T>`, by-value owned params, and already-borrowed `&str` /
  `&[T]` parameters are not flagged
- [ ] Signatures in comments are not flagged
- [ ] Each finding names the borrowed alternative and cites the
  deref-coercion rationale
