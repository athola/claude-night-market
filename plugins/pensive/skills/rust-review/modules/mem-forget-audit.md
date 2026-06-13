---
module: mem-forget-audit
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 550
tags: [drop, destructor, leak, mem-forget, raii]
---

# Mem Forget Audit

Rust runs destructors deterministically at end of scope. Two calls
quietly defeat that guarantee: `mem::forget(x)` skips the destructor and
leaks whatever the value owns, and `drop(&x)` drops a reference, which is
a no-op that leaves the owned value alive. This dimension flags both so
the reviewer can confirm the cleanup is intentional.

## What This Detects

The analyzer (`analyze_mem_forget`) flags two shapes:

1. **`mem::forget`**: a `forget(x)` call, whether written
   `mem::forget`, `std::mem::forget`, or an imported bare `forget`. The
   value is consumed but its destructor never runs.
2. **`drop(&x)`**: a `drop(...)` call whose argument starts with `&`. It
   drops the borrow, not the value, so the destructor still has not run
   and the resource lives on.

A method call (`cache.forget(key)`, `guard.drop()`) is left alone: the
regex requires a non-`.` character before the name. An owning
`drop(value)` is the correct idiom and is not flagged.

## Why This Leaks or No-ops

The Rust Reference destructors chapter (`src/destructors.md`) describes
the automatic, scope-based destructor that `mem::forget` opts out of.
Forgetting a `File` leaks the descriptor, forgetting a `MutexGuard`
poisons nothing but never unlocks, and forgetting a `Box` leaks the
allocation. `forget` is safe (leaking is not unsound), which is exactly
why it slips through review.

`drop(&x)` is the mirror-image mistake: `drop` consumes its argument, and
a shared reference is `Copy`, so dropping the reference compiles and does
nothing. The author believes the value is gone; it is not.

## The Fix

```rust
// Flag: forget skips the destructor and leaks
mem::forget(guard);

// Defer cleanup explicitly with ManuallyDrop
let mut slot = ManuallyDrop::new(guard);
// ... later, when you have decided ownership ...
unsafe { ManuallyDrop::drop(&mut slot) };

// Or hand the resource across an FFI boundary as a raw pointer,
// documenting who frees it.
let raw = Box::into_raw(boxed);   // not mem::forget(boxed)

// Flag: dropping a reference is a no-op
drop(&resource);
// Drop the owned value (or just let it fall out of scope)
drop(resource);
```

Use `ManuallyDrop` when cleanup must be deferred, `Box::into_raw` /
`into_raw_fd` when handing ownership across a boundary, and plain scope
exit otherwise. For `drop`, pass the owned value, not a borrow.

## Exclusions (Not Flagged)

- **Method calls**: `cache.forget(key)`, `guard.drop()` are user methods,
  not the std functions.
- **Owning drop**: `drop(value)` (no leading `&`) is the correct way to
  end a value early.
- **Comments**: a `forget` shown in a `//` comment is not code.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::mem_forget` | `mem::forget` on a `Drop` type |
| `clippy::drop_ref` | `drop` of a reference (a no-op) |
| `clippy::forget_ref` | `forget` of a reference (a no-op) |
| `clippy::mem_forget` | Leaks that should be `ManuallyDrop` or scope |

## Output Section

```markdown
## Mem Forget Audit
### Issues Found
- [file:line] `mem::forget` skips the destructor and leaks the resource;
  use `ManuallyDrop` or let the value drop at scope end
  (clippy::mem_forget)
- [file:line] `drop(&x)` drops a reference (a no-op); drop the owned
  value `drop(x)` (clippy::drop_ref)
```

## Exit Criteria

- [ ] `mem::forget(...)` and an imported bare `forget(...)` are flagged as
  `mem_forget`
- [ ] `drop(&x)` is flagged as `drop_ref`
- [ ] Method calls (`cache.forget(...)`) and owning `drop(value)` are not
  flagged
- [ ] A `forget` inside a `//` comment is not flagged
- [ ] Each finding names the `ManuallyDrop`/scope alternative and the
  clippy lint
