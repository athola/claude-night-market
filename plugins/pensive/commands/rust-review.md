---
name: rust-review
description: Expert-level Rust audits for safety and correctness.
---

# Rust Review Command

Expert-level Rust audits for safety and correctness.

## Usage

```bash
/rust-review
```

## What It Does

Invoke `Skill(pensive:rust-review)`, which carries the audit workflow and
the output format. The dimensions below are what this command reviews.

1. **Borrowing & Lifetimes**: Check ownership patterns
2. **Error Handling**: Evaluate Result/Option usage
3. **Concurrency**: Review async and sync primitives; flag
   multi-task orchestration torn down with consecutive
   `JoinHandle::abort()` calls around an `mpsc`-shared sink
   (suggest a single `select!` loop when branches are
   cancel-safe)
4. **Unsafe & FFI**: Audit unsafe blocks
5. **Traits & Generics**: Check API design
6. **Cargo Dependencies**: Scan for issues
7. **Idiomatic Type Use**: Conversions (`From`/`TryFrom` over
   `Into`/`TryInto`, no discarded `try_into().unwrap()`), deref-coercion
   parameters (`&str`/`&[T]`/`&Path` over `&String`/`&Vec<T>`/`&PathBuf`),
   and elision (needless lifetimes, explicit `-> ()` unit returns)
8. **Memory & Allocation**: Flag unbounded collections fed from
   external sources (cap with a named `MAX_*` const), hot-path
   recompute that should be memoized behind a generation
   counter, and serial blocking I/O in loops over unbounded
   sets (bound concurrency, add per-call timeouts)

## Scope

- Ownership correctness
- Memory safety
- Thread safety
- FFI boundaries
- Dependency security

## Output

- Safety audit results
- Concurrency analysis
- Unsafe block documentation
- Dependency scan
- Recommendations
