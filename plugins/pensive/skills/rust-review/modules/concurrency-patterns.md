---
name: concurrency-patterns
description: Arc/Mutex/RwLock usage, async patterns, and concurrency safety
category: rust-review
tags: [concurrency, async, sync, deadlock, atomics]
---

# Concurrency Patterns

Analysis of concurrent and async code patterns in Rust.

## Synchronization Primitives

Review primitives usage:
- `Arc`, `Mutex`, `RwLock`
- `Atomic*` types
- `tokio::sync` (mpsc, broadcast, watch)
- `Send`/`Sync` bounds

## Async Patterns

Check async code:
- No blocking in async functions
- Proper `spawn_blocking` usage
- Guards dropped before awaiting
- Cancellation safety
- Task spawning patterns

## Best Practices

```rust
// Good: Drop guard before await
async fn update(data: Arc<Mutex<Data>>) {
    let value = {
        let guard = data.lock().await;
        guard.value.clone()
    }; // Guard dropped
    process(value).await;
}
```

## Deadlock Prevention

Identify potential deadlocks:
- Lock ordering consistency
- Nested locks
- Await points while holding locks
- Circular dependencies

## Data Race Detection

Check for:
- `static mut` misuse
- Shared mutable state
- Missing synchronization
- Race conditions

## Send/Sync Bounds

Verify:
- Proper trait bounds
- Thread safety guarantees
- Cross-thread data transfer
- Closure captures

## Common Issues

- Blocking in async context
- Guards held across await points
- Inconsistent lock ordering
- Missing bounds on generics
- Unsafe Send/Sync implementations

## Output Section

```markdown
## Concurrency
### Issues Found
- [file:line] Guard held across await: [details]
- [file:line] Potential deadlock: [scenario]

### Recommendations
- [concurrency improvements]
```
