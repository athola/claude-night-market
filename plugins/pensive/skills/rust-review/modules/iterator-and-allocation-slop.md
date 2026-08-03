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

### Pattern 6: hand-rolled loop optimization

```rust
// SLOP: manually unrolled, defeats the auto-vectorizer
let mut sum = 0u32;
let mut i = 0;
while i + 4 <= v.len() {
    sum += v[i] + v[i + 1] + v[i + 2] + v[i + 3];
    i += 4;
}
while i < v.len() {
    sum += v[i];
    i += 1;
}

// Idiomatic: let LLVM unroll and vectorize the iterator
let sum: u32 = v.iter().sum();
```

Rust compiles through LLVM, which unrolls, hoists invariants, and
strength-reduces at `-O2`/`-O3`. Hand-rolling these is redundant, and
manual unrolling commonly blocks the vectorizer. Manual SIMD
(`std::simd`, intrinsics) is justified only on a loop the compiler
provably failed to vectorize, after fixing aliasing, and verified by a
codegen check (not "I see SIMD in the source").

No single clippy lint covers this; it is judgment. Decision rule and
the two benchmark traps: `Skill(leyline:loop-optimization)`.

#### The branchless exception

Branch elimination is the one hand-rolled loop transform LLVM will
not do for you, so Pattern 6 does not apply to it.

```rust
// Ordinary: one unpredictable branch per element
input.iter().copied().filter(|&x| x > threshold).collect()

// Branchless: store unconditionally, advance the index conditionally
let mut out = vec![0.0; input.len()];
let mut n = 0;
for &x in input {
    out[n] = x;
    n += (x > threshold) as usize;
}
out.truncate(n);
```

The rewrite stores every element and lets the comparison decide
where the next one lands. LLVM cannot generate this itself: writing
to slots the original never touched is not a semantics-preserving
transformation, so it has to come from the author.

**Do not flag this as slop when all three hold.** The loop is a
profiled hot path. The predicate depends on unpredictable data, so
the branch actually mispredicts (a sorted or stably-skewed predicate
predicts well and needs nothing). And the author reports measurements
across a selectivity range rather than one point.

**Do flag it when any are missing**, and flag these costs even when
it is justified:

- It flattens cost, it does not reduce it. On measured 1M-element
  `f64` data it won the 50% worst case by about 4x and lost the 1%
  best case by about 2x. On sorted input the plain branchy filter beat
  it outright.
- The output buffer is allocated at full input length. A 1% filter
  over 1M `f64` reserves 8 MB to return 80 KB, which interacts badly
  with the allocation guidance below.

Full technique table, the benchmark numbers, and the source:
`Skill(leyline:loop-optimization)`.

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

### Pattern E2: `Box<dyn Trait>` or `&dyn Trait` in a hot inner loop

This is distinct from Pattern E. The box itself may be
justified: the problem is calling a `dyn` method millions of
times when the method body is tiny.

```rust
// Potentially slow: dyn dispatch in the inner loop
let decoders: Vec<Box<dyn ColumnDecoder>> = build_decoders(&schema, &batch);

for i in 0..n_rows {
    for d in &decoders {
        d.write_to_row(i, &mut row);  // indirect call every iteration
    }
}
```

**Why it matters**: each `dyn` call goes through a vtable
(`call *0x18(%rax)`). The compiler cannot inline across that
boundary, so it cannot fuse the inner loop, vectorize small
stores, or eliminate the function-call prologue/epilogue overhead.
When the method body is ~25 instructions (a null check, a bit
flip, a 4-byte move), the prologue/epilogue and indirect
jump overhead can represent 40–50% of total runtime.

Note: `&dyn Trait` has the same problem as `Box<dyn Trait>`.
The issue is dynamic dispatch, not heap allocation.

**Fix 1: flip the loop order (batch-first)**: iterate
all rows for each decoder, not all decoders for each row.
The dyn dispatch cost is paid once per decoder per batch
instead of once per cell:

```rust
let mut rows: Vec<WriteRow> = (0..n_rows)
    .map(|i| WriteRow::new(&segment, key_array.value(i)))
    .collect();

for d in &decoders {
    d.write_to_rows(0, &mut rows[..]);  // dispatch once per decoder
}
```

**Fix 2: enum dispatch**: replace `dyn Trait` with a
closed enum. The compiler can monomorphize and inline each
variant:

```rust
enum ColDecoder {
    F32(F32Decoder),
    Utf8(Utf8Decoder),
    Bool(BoolDecoder),
}

impl ColDecoder {
    #[inline(always)]
    fn write_to_row(&self, index: usize, row: &mut WriteRow) {
        match self {
            ColDecoder::F32(d) => d.write_to_row(index, row),
            ColDecoder::Utf8(d) => d.write_to_row(index, row),
            ColDecoder::Bool(d) => d.write_to_row(index, row),
        }
    }
}
```

**When to flag**: any `Vec<Box<dyn Trait>>` or `Vec<&dyn Trait>`
iterated inside an inner loop where the method body is
inlineable. The Java/JVM analogy is instructive: the JVM
de-virtualizes and inlines at JIT time; rustc cannot cross
the `dyn` boundary. If reviewers come from JVM backgrounds,
this is the most important Rust performance lesson to surface.

Detection:

```bash
# Find Vec<Box<dyn>> that appear inside nested loops
rg "Vec<Box<dyn" --type rust -n

# Find dyn method calls inside for loops (heuristic)
rg -A 5 "for .* in" --type rust | rg "\.write_to|\.decode|\.encode|\.process"
```

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
