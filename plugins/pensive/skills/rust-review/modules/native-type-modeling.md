---
module: native-type-modeling
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 700
tags: [enum, newtype, typestate, matches, ordering, from, tryfrom]
---

# Native Type Modeling

Detects code that compares or branches on bare primitives where a
native Rust type would let the compiler check every case. The
companion `builtin-preference.md` module covers conversion traits and
combinators; this module covers modeling state with the type system:
enums for comparison, the newtype pattern, type-state, and derived
ordering traits.

## What This Detects

The analyzer (`analyze_native_type_modeling`) flags two crisp,
low-false-positive ports:

1. **Stringly-typed comparison**: `status == "active"`,
   `mode != "fast"`. A value compared against a string literal is a
   missing enum. Model the states as an enum and compare with the
   `matches!` macro or derived `==`.
2. **Boolean blindness**: a function signature carrying two or more
   `: bool` parameters, like `fn paint(immediate: bool, antialias:
   bool)`. Call sites such as `paint(true, false)` are unreadable and
   silently transposable. Replace each flag with a two-variant enum.
3. **Integer state constants**: a named constant with a state-ish stem
   (`STATUS`, `STATE`, `MODE`, `KIND`, `PHASE`, `STEP`) and a plain
   decimal value, like `const STATUS_ACTIVE: u8 = 0;`. A group of these
   is a C-style enum waiting to happen. Detection requires a decimal
   literal so bitmask shifts (`1 << 2`) and hex are left for
   `bitflags`, not mis-flagged as enums.

Newtype and type-state are covered as guidance below rather than
auto-flagged: reliable static detection produces too many false
positives at I/O and storage boundaries.

## Why It Matters

Enums turn runtime string and integer checks into compile-time
exhaustiveness checks. Adding a variant produces a compile error at
every match site instead of a silent fallthrough. This is the
"make invalid states unrepresentable" principle: it predates Rust,
coined by Yaron Minsky (Jane Street, OCaml) and popularized by Scott
Wlaschin (F# for Fun and Profit / Domain Modeling Made Functional),
and reached the Rust community through Alexis King's "Parse, Don't
Validate." A product of boolean flags is representationally complete
but semantically loose: it admits combinations that type-check but
have no domain meaning, and each is a latent bug.

## 1. Enums for Comparison

```rust
// Flag: stringly typed — the compiler cannot check the cases
fn is_billable(status: &str) -> bool {
    status == "active" || status == "trial"
}

// Native: enum + matches!, exhaustive and self-documenting
enum Status { Active, Trial, Suspended, Cancelled }

fn is_billable(status: Status) -> bool {
    matches!(status, Status::Active | Status::Trial)
}
```

`matches!` (stable since Rust 1.42, no import) returns `bool` for a
pattern check and composes inside `.filter()` and `while` conditions.
Use it instead of a `match` whose arms only return `true`/`false`
(`clippy::match_like_matches_macro`). Use a full `match` or `if let`
when you must bind data out of the variant.

For a public library enum that may gain variants later, mark it
`#[non_exhaustive]` so downstream `match` arms must include a `_`
wildcard and adding a variant is not a breaking change. Do **not**
apply `#[non_exhaustive]` to crate-internal enums: it forces wildcard
arms that defeat the exhaustiveness check you want.

## 2. Boolean Blindness

```rust
// Flag: two bool params — paint(true, false) is unreadable
fn paint(immediate: bool, antialias: bool) { /* ... */ }

// Native: enums make call sites self-documenting
enum PaintMode { Immediate, Deferred }
enum AntiAlias { On, Off }
fn paint(mode: PaintMode, aa: AntiAlias) { /* ... */ }
// paint(PaintMode::Immediate, AntiAlias::Off)
```

`clippy::fn_params_excessive_bools` warns past a threshold of bool
parameters. A single, genuinely binary, self-evident parameter
(`set_visible(bool)`) is idiomatic and is not flagged.

## 3. Integer State Constants

```rust
// Flag: C-style integer constants standing in for an enum
const STATUS_ACTIVE: u8 = 0;
const STATUS_SUSPENDED: u8 = 1;
const STATUS_CLOSED: u8 = 2;

// Native: an enum the compiler checks; add discriminants only when
// the on-the-wire integer values matter
#[repr(u8)]
enum Status { Active = 0, Suspended = 1, Closed = 2 }
```

Detection requires a state-stemmed name and a plain decimal value, so
a composable bitmask is left alone:

```rust
// Not flagged: a mask is a `bitflags` candidate, not an enum
const STATE_MASK: u32 = 1 << 2;
```

Use the `bitflags` crate (or an explicit `#[repr]` enum with discrete
discriminants) when the values combine; reach for a plain enum when
they are mutually exclusive states.

## 4. Newtype Pattern (Guidance)

Wrap a primitive in a single-field tuple struct to get a distinct,
zero-cost type that is not interchangeable with the underlying type
(unlike a `type` alias):

```rust
struct Miles(f64);
struct Kilometers(f64);
// add_distance(miles, km) no longer compiles by accident
```

A newtype enforces an invariant only when its field is **private**
and the only constructor validates:

```rust
mod email {
    pub struct Email(String);          // field private to the module
    impl Email {
        pub fn new(s: &str) -> Result<Self, Invalid> { /* validate */ }
    }
}
```

A name alone is not type safety (Alexis King, "Names are not type
safety"): `Email(raw)` from inside the module still bypasses the
check, so keep the field private and route callers through `new`.

## 5. Type-State (Guidance)

Encode lifecycle state in the type so invalid operations do not
compile. A `Connection<Authenticated>` exposes `request()`; a
`Connection<Disconnected>` does not. Strom & Yemini introduced
typestate in 1986; Cliffle's "The Typestate Pattern in Rust" is the
canonical Rust reference.

Reserve type-state for safety-critical or protocol APIs. Multiple
practitioners (corrode.dev, Cliffle, greyblake/nutype) independently
warn it raises cognitive load, yields obscure compiler errors, grows
binary size through monomorphization, and is awkward with collections
of mixed-state items. When transitions are runtime-determined, use a
plain enum state machine instead.

## 6. Derived Ordering And Comparison

Derive `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash`/`Default` rather
than hand-writing them, and replace three-way `if`/`else if` ladders
with a `match` on `Ordering`:

```rust
// Flag: comparison chain (clippy::comparison_chain)
if x > y { a() } else if x < y { b() } else { c() }

// Native: exhaustive, evaluates the comparison once
match x.cmp(&y) {
    Ordering::Greater => a(),
    Ordering::Less => b(),
    Ordering::Equal => c(),
}
```

Hand-write an impl only when semantics differ from the field-wise
derive (a non-zero `Default`, an `Ord` that ignores a cache field).
Keep `Hash` and `Eq` consistent: deriving one and hand-writing the
other can violate the `Hash`/`Eq` contract.

## Exclusions (Not Flagged)

These guardrails come from cross-source practitioner consensus; a
finding that hits one of them is a false positive.

- **Storage and protocol boundaries**: you still parse untyped
  external data (JSON strings, DB integers, CLI args) into the enum
  once at the edge. The principle governs the internal domain model,
  not the wire or serialization format. A permissive type at a
  `serde`/DB boundary is correct, not a defect.
- **Empty-string checks** (`s == ""`): an emptiness test, not a
  stringly-typed enum candidate (prefer `.is_empty()` separately).
- **Single self-evident bool**: one binary local flag does not need
  an enum.
- **Genuinely evolving business rules**: encode only what is *truly
  impossible*, not what is merely *currently disallowed*. Hard-coding
  every transient rule into types creates migration cost
  ("'Make invalid states unrepresentable' considered harmful").
- **Open/extensible variant sets**: when downstream crates must add
  cases, a trait object beats an enum.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::match_like_matches_macro` | `match` returning only `true`/`false` |
| `clippy::comparison_chain` | `if`/`else if` ladder over `Ordering` |
| `clippy::fn_params_excessive_bools` | Too many `bool` parameters |
| `clippy::derivable_impls` | Manual impl that `#[derive]` handles |
| `clippy::derive_partial_eq_without_eq` | `PartialEq` derive missing `Eq` |

## Output Section

```markdown
## Native Type Modeling
### Issues Found
- [file:line] Stringly-typed comparison: model as enum, compare with
  `matches!` (clippy::match_like_matches_macro)
- [file:line] Boolean blindness (2 bool params): take two-variant
  enums (clippy::fn_params_excessive_bools)

### Recommendations
- Model internal state as enums; parse to them once at the boundary
- Keep newtype fields private with validating constructors
- Reserve type-state for safety-critical/protocol APIs
```

## Exit Criteria

- [ ] Stringly-typed comparisons (`x == "literal"`) are flagged with
  an enum + `matches!` recommendation
- [ ] Function signatures with two or more `: bool` params are flagged
  as boolean blindness; single-bool signatures are not
- [ ] Empty-string comparisons and `matches!` lines are not flagged
- [ ] Newtype, type-state, and derived-ordering guidance is present
  with explicit storage-boundary and over-application exclusions
