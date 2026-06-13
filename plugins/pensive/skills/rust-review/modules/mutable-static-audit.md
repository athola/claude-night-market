---
module: mutable-static-audit
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 550
tags: [static-mut, globals, data-race, atomics, oncelock, unsafe]
---

# Mutable Static Audit

`static mut` is shared mutable global state with no synchronization. It
needs `unsafe` to touch, and every touch is a promise the author upholds
the aliasing and thread-safety rules by hand. This dimension flags every
`static mut` declaration and points at the safe replacement.

## What This Detects

The analyzer (`analyze_mutable_statics`) flags any `static mut`
declaration, including with leading visibility qualifiers:

```rust
static mut COUNTER: u64 = 0;          // flagged
pub static mut REGISTRY: *mut u8 = core::ptr::null_mut();  // flagged
```

A plain `static` (immutable) and a `const` are not flagged; only the
`mut` form is shared mutable state.

## Why `static mut` Is Dangerous

The Rust Reference static items chapter
(`src/items/static-items.md`) is explicit:

- "an `unsafe` block is required when either reading or writing a
  mutable static variable."
- Mutable statics exist because "one of Rust's goals is to make
  concurrency bugs hard to run into, and this is obviously a very large
  source of race conditions or other bugs."

Since Rust 2024, taking a reference to a `static mut` is the
deny-by-default `static_mut_refs` lint: the pattern is being designed
out of the language because creating a `&`/`&mut` to one is almost
always undefined behavior in the presence of any concurrency or
re-entrancy.

## The Fix

Pick the synchronized primitive that matches the access pattern:

```rust
use std::sync::atomic::{AtomicU64, Ordering};
static COUNTER: AtomicU64 = AtomicU64::new(0);   // counters / flags
COUNTER.fetch_add(1, Ordering::Relaxed);

use std::sync::OnceLock;
static CONFIG: OnceLock<Config> = OnceLock::new();  // set-once globals
CONFIG.get_or_init(Config::load);

use std::sync::Mutex;
static STATE: Mutex<State> = Mutex::new(State::new());  // shared data
STATE.lock().unwrap().update();
```

- **`OnceLock` / `LazyLock`**: a global initialized once, read freely
  after.
- **`Atomic*`**: lock-free counters, flags, and ids.
- **`Mutex` / `RwLock`**: arbitrary shared mutable data with
  synchronized access.

Each is safe code, needs no `unsafe`, and the compiler enforces the
threading contract instead of the author.

## Exclusions (Not Flagged)

- **Immutable `static`**: read-only global data is `Sync` and safe.
- **`const`**: a compile-time constant, not a single-address global.
- **Comments**: `static mut` mentioned in a `//` or `///` comment is
  not a declaration.

## Related Lints

| Lint | Detects |
|------|---------|
| `static_mut_refs` (rustc, deny-by-default 2024) | References to a `static mut` |
| `clippy::needless_late_init` | State that should be a one-shot init |

## Output Section

```markdown
## Mutable Static Audit
### Issues Found
- [file:line] `static mut` shared mutable global: replace with
  `OnceLock`/`LazyLock`, an `Atomic*`, or a `Mutex`/`RwLock`
  (deny-by-default static_mut_refs)
```

## Exit Criteria

- [ ] Every `static mut` declaration (with or without `pub`) is flagged
- [ ] Immutable `static` and `const` declarations are not flagged
- [ ] `static mut` inside a comment is not flagged
- [ ] Each finding names a thread-safe alternative and the
  `static_mut_refs` lint
