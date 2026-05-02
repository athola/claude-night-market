---
module: async-slop
category: detection
dependencies: [Read, Grep]
estimated_tokens: 500
---

# Async Slop

**AI defaults to `async` and `tokio::spawn` even where
sync code is faster, simpler, and correct.**

This module covers the high-frequency async patterns that
look idiomatic but are not. The clippy lints catch some;
the rest is structural.

## Pattern 1: `async fn` that contains no `.await`

```rust
// SLOP
async fn compute_total(items: &[Item]) -> u64 {
    items.iter().map(|i| i.price).sum()
}
```

If the function body has no `.await`, it has no reason
to be `async`. Async coloring is contagious: this
function is callable only from async contexts, forcing
every caller to also be `async`. Strip `async` from the
signature unless the body actually awaits.

Detection:

```bash
rg -A 10 "async fn " --type rust | rg -L "\.await"
# Functions without .await in the next 10 lines
```

(Heuristic; manual review needed since `.await` may be
deeper.)

## Pattern 2: blocking I/O inside an async runtime

```rust
// SLOP
async fn read_config() -> Result<String> {
    Ok(std::fs::read_to_string("config.toml")?)
}

// SLOP
async fn rate_limit_wait() {
    std::thread::sleep(Duration::from_secs(1));  // blocks the runtime
}

// SLOP
async fn query_db(conn: &Connection) -> Result<Vec<Row>> {
    conn.query("SELECT ...")?  // blocking driver
}
```

Blocking calls inside `async` block the entire executor
thread, defeating the runtime's concurrency model.

Fix:

```rust
// Use the async equivalent
async fn read_config() -> Result<String> {
    Ok(tokio::fs::read_to_string("config.toml").await?)
}

// Or wrap blocking work in spawn_blocking
async fn rate_limit_wait() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// For unavoidable blocking work
async fn query_db(conn: Arc<Connection>) -> Result<Vec<Row>> {
    let conn = conn.clone();
    tokio::task::spawn_blocking(move || conn.query("SELECT ..."))
        .await?
}
```

Detection:

```bash
# Find blocking ops inside async functions (heuristic)
rg -B 5 "(std::fs::|std::thread::sleep|std::net::TcpStream)" --type rust |
  rg -B 5 "async fn"
```

## Pattern 3: `tokio::spawn` for synchronous-equivalent work

```rust
// SLOP
async fn handle_request(req: Request) -> Response {
    let result = tokio::spawn(async move {
        compute_response(&req)
    }).await.unwrap();
    result
}
```

Spawning a task only to immediately await its single
completion is equivalent to a direct call, plus the
overhead of task creation, scheduling, and a join. Just
call the function:

```rust
async fn handle_request(req: Request) -> Response {
    compute_response(&req)
}
```

`tokio::spawn` is for *concurrent* work: when the
spawned task should make progress while the caller does
something else, or when the task should outlive the
caller. A spawn-then-immediately-await is a smell.

## Pattern 4: `async-trait` on synchronous-equivalent traits

```rust
// SLOP
#[async_trait]
trait Greeter {
    async fn greet(&self, name: &str) -> String;
}
```

If the implementation has no `.await` and just returns a
synchronous value, `async-trait` adds heap allocation
(`Box<dyn Future>`) for nothing. Make the trait sync:

```rust
trait Greeter {
    fn greet(&self, name: &str) -> String;
}
```

Use `async-trait` only when at least one implementation
genuinely awaits.

## Pattern 5: explicit `Pin<Box<dyn Future>>` returns

```rust
// SLOP
fn fetch_data(url: &str) -> Pin<Box<dyn Future<Output = Result<Data>> + Send>> {
    Box::pin(async move {
        // body
    })
}
```

Modern Rust supports `impl Future` in return position:

```rust
// Idiomatic
fn fetch_data(url: &str) -> impl Future<Output = Result<Data>> + Send {
    async move {
        // body
    }
}
```

`Pin<Box<dyn Future>>` is needed only for trait method
returns or when storing futures in collections.

## Pattern 6: `MutexGuard` held across `.await`

```rust
// SLOP — deadlock risk
async fn update_count(state: &Arc<Mutex<State>>) {
    let mut guard = state.lock().unwrap();
    guard.count += 1;
    save_to_disk(&guard).await;  // holds guard across await
}
```

Holding a sync `Mutex` guard across `.await` blocks the
runtime if any other task tries to acquire the same lock.
For async paths, use:

- `tokio::sync::Mutex` (async-aware, can hold guards
  across `.await`).
- Or restructure to drop the guard before awaiting:

```rust
async fn update_count(state: &Arc<Mutex<State>>) {
    let snapshot = {
        let mut guard = state.lock().unwrap();
        guard.count += 1;
        guard.clone()
    };  // guard dropped here
    save_to_disk(&snapshot).await;
}
```

This is the GPT-5.x signature failure (Sonar measured
~470 concurrency issues per MLOC for GPT-5.2 High); see
`model-specific-tells.md`.

## Pattern 7: re-implementing `select!` / `join!` manually

If you find yourself manually polling multiple futures
with `Pin::new` and `Poll`, you almost certainly want
`tokio::select!` or `tokio::join!`. Hand-rolled polling
is a strong signal that the model copied something it
should not have.

Detection:

```bash
rg "Pin::new" --type rust -B 2 -A 5 | rg -B 2 "fn poll"
```

## Pattern 8: `Send + Sync` bounds added "in case"

```rust
// SLOP
fn add<T: Send + Sync + Clone + Debug>(a: T, b: T) -> T { ... }
```

Trait bounds should be added because the function
*needs* them, not as defensive over-spec. `Send`/`Sync`
on a function that runs synchronously, `Clone` on a
function that doesn't clone, `Debug` on a function that
doesn't print: all noise.

The right rule: add the bound when the compiler complains
without it. Remove the bound when removing it does not
cause a compile error.

## Detection commands

```bash
# Catch most async slop with clippy
cargo clippy --all-targets -- \
  -W clippy::async_yields_async \
  -W clippy::large_futures \
  -D warnings

# Manual scans for the structural patterns
rg "async fn " --type rust -A 10 | grep -L "\.await"  # Pattern 1
rg "tokio::spawn.*\.await" --type rust                # Pattern 3
rg "#\[async_trait\]" --type rust                     # Pattern 4
rg "Pin<Box<dyn Future" --type rust                   # Pattern 5
rg -B 5 "\.await" --type rust | rg -B 5 "\.lock\(\)"  # Pattern 6
rg "Send \+ Sync" --type rust                         # Pattern 8
```

## False positives

Some async patterns are correct and should stay:

- `async fn` with no `.await` is fine in a trait
  implementation when other implementations need
  `.await`.
- `tokio::spawn` is fine when the task should outlive
  the caller, or when the caller does work in parallel.
- `Send + Sync` bounds are required when the type *will*
  be sent across threads (axum handlers, tokio tasks).

When in doubt, comment the rationale: `// async because
trait requires it; this impl is sync` or `// spawn so
metrics flush in parallel with shutdown`.

## Output format

Per `Skill(scribe:slop-detector)` module
`structured-finding-output.md`. Severity:

- **High**: pattern 6 (MutexGuard across await; deadlock
  risk).
- **Medium**: patterns 2 (blocking inside async), 3
  (spawn-then-await), 4 (async-trait on sync method).
- **Low**: patterns 1 (vacuous async), 5 (Pin<Box<dyn
  Future>>), 8 (defensive Send+Sync).

Pattern 6 is the highest-blast-radius async finding;
escalate to `severity: high` and to a senior reviewer.

## Integration

Async slop lands in Pass 5 of the multi-pass cleanup
workflow (`Skill(scribe:slop-detector)` module
`cleanup-workflow.md`). For GPT-family-generated
codebases, weight pattern 6 detection most heavily;
for Claude-family codebases, weight pattern 1 (the
"behavior-preserving refactor leaves async fn that no
longer awaits anything") most heavily. See
`model-specific-tells.md`.
