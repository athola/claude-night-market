# Rust Review

This module covers progressive-loading for Rust review skills:
which review-concern modules to load when auditing Rust source
for safety, ownership, concurrency, error handling, and
idiomatic style. The companion to `cargo-patterns.md`, which
covers the build-tool layer rather than the source layer.

## When This Module Applies

Load this module when the task involves:

- Reviewing `.rs` files for correctness, safety, or style.
- Auditing `unsafe` blocks for soundness.
- Investigating ownership, lifetimes, or borrow-checker errors.
- Reviewing async or threaded code for race conditions.

For dependency or workspace concerns, load `cargo-patterns.md`.
This module focuses on the source-code review surface.

## Slice the Review Surface First

A "Rust review" mega-module covering every concern is too
large. The progressive load splits by concern.

| Concern | Module | Token Estimate |
|---------|--------|----------------|
| Ownership and borrowing | `ownership-rules.md` | 600 |
| Unsafe audit | `unsafe-rules.md` | 700 |
| Error handling | `error-handling.md` | 500 |
| Concurrency | `concurrency-rules.md` | 700 |
| Async (`tokio`, `async-std`) | `async-rules.md` | 600 |
| Idiomatic style | `style-rules.md` | 400 |
| Performance and allocation | `performance-rules.md` | 500 |

Most reviews exercise two or three concerns, not all seven. The
hub selects based on the file content and explicit user signals.

## Detect Concerns by Source Inspection

A simple regex pass over the file picks the relevant concerns.

```bash
# Unsafe blocks present
rg --type rust 'unsafe (fn|impl|trait|\{)' path/

# Async present
rg --type rust 'async fn|\.await\b' path/

# Concurrency primitives present
rg --type rust 'std::sync|std::thread|crossbeam|rayon' path/

# Custom error types
rg --type rust 'thiserror|impl Error for|enum.*Error' path/
```

Each match triggers loading the matching sub-module. A file with
no `unsafe` and no async only loads ownership and error
handling.

## Concrete Example: Result Handling

The error-handling sub-module documents the patterns that come
up in every Rust review.

```rust
use std::fs;
use std::io;
use std::path::Path;

fn read_config(path: &Path) -> Result<String, io::Error> {
    fs::read_to_string(path)
}

// Propagate with ?
fn load(path: &Path) -> Result<Config, ConfigError> {
    let text = read_config(path).map_err(ConfigError::Io)?;
    let config: Config = toml::from_str(&text).map_err(ConfigError::Parse)?;
    Ok(config)
}

#[derive(Debug, thiserror::Error)]
enum ConfigError {
    #[error("io error: {0}")]
    Io(#[from] io::Error),
    #[error("parse error: {0}")]
    Parse(#[from] toml::de::Error),
}
```

`thiserror` is a real crate by David Tolnay. The `#[from]`
attribute generates `From` impls so the `?` operator does the
conversion automatically.

## Concrete Example: Unsafe Audit Checklist

The unsafe sub-module documents the contract checks every
reviewer must run.

```rust
// SAFETY: This block dereferences a raw pointer obtained from
// `Box::into_raw` exactly once, after which it is reboxed.
// The pointer is non-null and properly aligned because it
// came from a valid Box.
unsafe {
    let b = Box::from_raw(ptr);
    drop(b);
}
```

The review rule is that every `unsafe` block must have a
`// SAFETY:` comment documenting the invariants the caller is
asserting. Blocks without the comment are review-blockers.

## Concrete Example: Concurrency Smell

The concurrency sub-module documents common races.

```rust
use std::sync::{Arc, Mutex};
use std::thread;

// SMELL: lock held across .await
async fn bad(state: Arc<Mutex<Vec<u32>>>) {
    let mut guard = state.lock().unwrap();
    guard.push(1);
    do_async_work().await;  // holds lock across await
}

// FIX: drop guard before await
async fn good(state: Arc<Mutex<Vec<u32>>>) {
    {
        let mut guard = state.lock().unwrap();
        guard.push(1);
    }
    do_async_work().await;
}
```

Holding a `std::sync::Mutex` across an `.await` point is a
common deadlock source. For locks held across awaits, use
`tokio::sync::Mutex` instead.

## Pitfalls

1. **Loading every concern**: A file with no `unsafe` does not
   need the unsafe sub-module. Detect concerns first.
2. **Treating `unwrap` as a review block**: In tests and
   examples, `unwrap` is acceptable. In library code paths, it
   is a finding. Context matters.
3. **Skipping the `// SAFETY:` rule**: Unsafe blocks without
   safety comments are the highest-value finding in a Rust
   review. Always load the unsafe sub-module when any unsafe
   block is present.
4. **Confusing tokio Mutex and std Mutex**: They have the same
   API surface but different blocking behavior. The async
   sub-module documents when to use each.
5. **One review for source and dependencies**: Cargo audit and
   source review are separate concerns with separate tools.
   Keep them in `cargo-patterns.md` and this module
   respectively.

## Cross-Reference

See `cargo-patterns.md` for the build-tool layer and the parent
`SKILL.md` for how Rust modules plug into the hub-and-spoke
pattern.
