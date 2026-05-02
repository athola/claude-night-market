---
module: iterator-and-allocation-slop
category: detection
dependencies: [Read, Grep]
estimated_tokens: 600
---

# Iterator and Allocation Slop

**AI-generated Rust defaults to manual loops where
iterators read better, and to allocation where references
suffice. Both compile; both are slop.**

This module covers two of the highest-frequency AI Rust
anti-patterns: imperative loops the iterator API expresses
in one line, and unnecessary allocation that
borrow-checker capitulation produces. The clippy lints
catch most of this; the rest is judgment.

## Iterator slop

### Pattern 1: index-based loops

```rust
// SLOP
let mut sum = 0;
for i in 0..vec.len() {
    sum += vec[i];
}

// Idiomatic
let sum: i32 = vec.iter().sum();
```

Detector: `clippy::needless_range_loop`.

### Pattern 2: filter-then-push

```rust
// SLOP
let mut result = Vec::new();
for x in xs.iter() {
    if x.is_active() {
        result.push(x.id);
    }
}

// Idiomatic
let result: Vec<_> = xs.iter()
    .filter(|x| x.is_active())
    .map(|x| x.id)
    .collect();
```

### Pattern 3: map-filter-unwrap

```rust
// SLOP
let firsts: Vec<_> = xs.iter()
    .map(|x| x.first())
    .filter(|x| x.is_some())
    .map(|x| x.unwrap())
    .collect();

// Idiomatic
let firsts: Vec<_> = xs.iter()
    .filter_map(|x| x.first())
    .collect();
```

Detector: `clippy::manual_filter_map`.

### Pattern 4: collect-then-iterate

```rust
// SLOP
let intermediate: Vec<_> = xs.iter().map(transform).collect();
for item in intermediate {
    use_it(item);
}

// Idiomatic
for item in xs.iter().map(transform) {
    use_it(item);
}
```

Detector: `clippy::needless_collect`.

### Pattern 5: bool-match where if suffices

```rust
// SLOP
match flag {
    true => do_a(),
    false => do_b(),
}

// Idiomatic
if flag { do_a() } else { do_b() }
```

Detector: `clippy::match_bool`.

## Allocation slop

### Pattern A: `.clone()` to satisfy the borrow checker

The single most common AI-generated Rust anti-pattern. The
`rust-unofficial/patterns` book lists it as the canonical
anti-pattern: cloning to make a borrow-checker error go
away rather than to express ownership.

```rust
// SLOP
fn greet(name: String) {
    println!("Hello, {name}");
}
fn main() {
    let n = String::from("world");
    greet(n.clone());      // unnecessary clone
    greet(n.clone());
}

// Idiomatic
fn greet(name: &str) {
    println!("Hello, {name}");
}
fn main() {
    let n = String::from("world");
    greet(&n);
    greet(&n);
}
```

Detection heuristic: any `.clone()` on a `String`,
`Vec<_>`, `HashMap<_,_>`, `Arc<Mutex<_>>`, or large
struct that is *not* paired with a comment explaining
the ownership rationale. If it disappeared, would the
borrow checker complain? If yes, the right fix is
usually to take a borrowed reference (`&str`, `&[T]`,
`&T`).

Detectors: `clippy::redundant_clone`,
`clippy::clone_on_ref_ptr`.

### Pattern B: owned parameters that should borrow

| Slop signature | Idiomatic signature |
|---|---|
| `fn f(s: &String)` | `fn f(s: &str)` |
| `fn f(v: &Vec<T>)` | `fn f(v: &[T])` |
| `fn f(s: String)` (read-only) | `fn f(s: &str)` |
| `fn f(v: Vec<T>)` (read-only) | `fn f(v: &[T])` |
| `fn f(b: Box<T>)` (no boxing reason) | `fn f(t: T)` |

Detector: `clippy::ptr_arg` catches `&Vec<T>` and `&String`.

### Pattern C: `format!` then convert

```rust
// SLOP
let s = format!("{}", x);

// Idiomatic (when Display is implemented)
let s = x.to_string();

// Inverse SLOP
let s = x.to_string();
let s = format!("{s}{rest}");

// Idiomatic (build the string once)
let s = format!("{x}{rest}");
```

Detectors: `clippy::useless_format`, `clippy::str_to_string`.

### Pattern D: redundant allocation

```rust
// SLOP
let owned = borrowed.to_owned();
fn take_str(s: &str) { ... }
take_str(&owned);

// Idiomatic — borrow directly
take_str(borrowed);

// SLOP
let s = String::new();
let s = s + "hello" + " " + "world";

// Idiomatic
let s = String::from("hello world");
```

### Pattern E: `Box::new(...)` without indirection reason

```rust
// SLOP
let x = Box::new(42_u64);
fn use_it(n: u64) { ... }
use_it(*x);

// Idiomatic
let x = 42_u64;
use_it(x);
```

Heap allocation is justified for:
- `dyn Trait` objects (`Box<dyn Error>`, `Box<dyn Future>`).
- Recursive types (`Box<Node>`).
- Large stack-frame avoidance (uncommon; measure first).
- Pinning requirements (`Pin<Box<T>>`).

Anywhere else, `Box::new` is unjustified allocation.

### Pattern F: `Vec` for fixed small set

```rust
// SLOP
let primes: Vec<u32> = vec![2, 3, 5, 7, 11];

// Idiomatic for small, fixed-size
let primes: [u32; 5] = [2, 3, 5, 7, 11];

// Or for stack-allocated growable
let primes: SmallVec<[u32; 5]> = smallvec![2, 3, 5, 7, 11];
```

This one is judgment: arrays for compile-time-known
sizes, `SmallVec`/`ArrayVec` for "usually small but
sometimes grows", `Vec` for genuinely dynamic.

## Detection commands

```bash
# Catch most iterator slop with clippy
cargo clippy --all-targets -- \
  -W clippy::needless_range_loop \
  -W clippy::manual_filter_map \
  -W clippy::needless_collect \
  -W clippy::filter_map_next \
  -W clippy::map_unwrap_or \
  -W clippy::match_bool \
  -W clippy::needless_match \
  -D warnings

# Catch most allocation slop with clippy
cargo clippy --all-targets -- \
  -W clippy::redundant_clone \
  -W clippy::clone_on_ref_ptr \
  -W clippy::ptr_arg \
  -W clippy::useless_format \
  -W clippy::str_to_string \
  -W clippy::redundant_allocation \
  -D warnings

# Manual scan: every .clone() in the codebase
rg "\.clone\(\)" --type rust -n | head -50
# For each: ask "would the borrow checker complain if removed?"
```

## False positives

Some `.clone()` calls are correct and should stay:

- **Async / spawn boundaries**: cloning an `Arc<T>` to
  send into `tokio::spawn` is required, not slop.
- **Genuine ownership transfer**: when two callers each
  need to mutate independently from the same source.
- **Intentional defensive copy**: in security-sensitive
  paths where the original might be modified by an
  attacker. Mark with `// COPY: defense against ...`.

When in doubt, comment the rationale next to the
`.clone()`. A `.clone()` with a one-line "why" comment
is documented intent; a `.clone()` with no comment is
slop.

## Output format

For each finding, use the
`Skill(scribe:slop-detector)` module
`structured-finding-output.md` format. Severity is
`medium` for individual iterator/allocation slop;
`high` if the same pattern appears 5+ times in the same
file (suggests systematic AI-generation rather than
isolated mistake).

## Integration

Iterator and allocation slop typically lands in Pass 5
(code idiom sweep) of the multi-pass cleanup workflow
(see `Skill(scribe:slop-detector)` module
`cleanup-workflow.md`). Run after the linter floor
(Pass 1) clears, since clippy will flag most of these
automatically.
