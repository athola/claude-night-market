---
name: unsafe-audit
description: Unsafe block auditing, FFI contracts, and safety invariants
category: rust-review
tags: [unsafe, ffi, safety, invariants]
---

# Unsafe & FFI Audit

detailed audit of unsafe code and FFI boundaries.

## Unsafe Block Invariants

For each `unsafe` block, document:
- Pointer validity requirements
- Aliasing rules adherence
- Memory ordering guarantees
- Uninitialized memory handling
- FFI contracts

## SAFETY Comments

Every unsafe block must have:
- Clear safety comment
- Invariant documentation
- Caller requirements
- Pre/post conditions

## FFI Boundaries

Audit `extern "C"` interfaces:
- Representation alignment (`#[repr(C)]`)
- Ownership transfer semantics
- Resource cleanup guarantees
- Error code translation
- Null pointer handling

## Safe Abstraction Wrappers

Recommend wrapping unsafe in safe APIs:
```rust
// Wrap unsafe in safe API
pub fn safe_operation(ptr: NonNull<Data>) -> Result<(), Error> {
    // SAFETY: ptr is non-null and properly aligned
    // Caller guarantees exclusive access
    unsafe {
        (*ptr.as_ptr()).process()
    }
}
```

## Memory Pinning (mlock)

When reviewing real-time or latency-sensitive code that calls
`libc::mlock` or `libc::munlock`, audit all four production
gotchas before approving:

**RLIMIT_MEMLOCK**: Linux default is 64KB. Any `mlock` on a
buffer larger than the process rlimit silently returns `ENOMEM`.
Flag code that does not check the rlimit or document the
deployment's `securityContext`/`ulimit` setting.

**Page alignment**: `mlock` operates at page granularity (4KB
on x86). Locking a byte slice that is not page-aligned pins
adjacent memory belonging to other allocations. Require
`posix_memalign` or `std::alloc::Layout::from_size_align` with
`page_size()` alignment on the underlying buffer.

**ENOMEM fallback**: `mlock` can fail with `ENOMEM` at runtime
(e.g., when a co-located process allocates unexpectedly). Treat
as a recoverable error: fall back to un-pinned buffers and emit
a metric. Code that `unwrap()`s or ignores the return value is
a production bug.

**Lifetime coupling**: the buffer must outlive the lock.
`munlock` must be called before the slice is freed. Require a
SAFETY comment on every `pin_buffer`/`unpin_buffer` call site
that documents the lifetime guarantee.

```rust
// SAFETY: `buf` is page-aligned (allocated via posix_memalign),
// lives for the duration of the audio pipeline, and RLIMIT_MEMLOCK
// has been raised to 16MB in the container securityContext.
// munlock is called in AudioBuffer::drop.
unsafe { pin_buffer(&ring_buf)? };
```

**Cross-platform note**: macOS uses `mlock` (same interface),
Windows uses `VirtualLock`. If the crate must be
cross-platform, audit for the platform guard or check whether
a wrapper crate is used instead of raw `libc` calls.

**Production context**: the canonical symptom of a missing
`mlock` is inconsistent latency spikes in production that
disappear on dev machines. The kernel pages out long-lived
audio or ring-ring buffers when a co-resident large allocation
(e.g., ML model weights) forces a page eviction. The
page-fault on next buffer access adds 100–380ms of p99 latency
that `tokio-console` will not surface, because the task
scheduling itself is fast; the delay is in the kernel.

## Common Unsafe Patterns

Check for:
- Raw pointer dereferences
- Mutable static access
- Type transmutations
- Inline assembly
- Trait object manipulation

## Undefined Behavior Checks

Verify absence of:
- Use after free
- Double free
- Null pointer dereferences
- Data races in unsafe code
- Invalid enum discriminants

## Output Section

```markdown
## Unsafe Audit
### [U1] file:line
- Invariants: [documented]
- Risk: [high/medium/low]
- SAFETY comment: [present/missing]
- Recommendation: [action]

### Summary
- Total unsafe blocks: X
- Properly documented: Y
- Action required: Z
```
