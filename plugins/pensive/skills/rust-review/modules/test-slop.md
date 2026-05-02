---
module: test-slop
category: detection
dependencies: [Read, Grep, Bash]
estimated_tokens: 600
---

# Test Slop

**AI-generated tests exist. They disproportionately
mirror the implementation rather than validate
behavior.**

The CodeRabbit / Larridin (2026) data is unambiguous:
AI-generated test suites pattern-match correctly but
catch nothing. Mutation testing exposes this faster than
code review can. This module covers the specific
patterns to delete or replace.

## Pattern 1: `it_works`-class names

```rust
// SLOP — the cargo-new default, almost always still there
#[test]
fn it_works() {
    assert_eq!(2 + 2, 4);
}
```

Rule: either delete it, or rename to assert one specific
behavior. `it_works` tells the next reader nothing about
what is being verified or what changes would break it.

Detection:

```bash
rg -n '#\[test\]\s*\nfn (it_works|test_default|test_something)' --type rust
```

## Pattern 2: tautological tests

```rust
// SLOP
#[test]
fn test_creation() {
    let foo = Foo::new();
    assert!(foo.is_some());  // Foo::new() returns Foo, not Option<Foo>
}

// SLOP
#[test]
fn test_construction() {
    let s = Server::new();
    assert!(true);  // literal noise
}
```

These tests assert nothing the type system does not
already prove. Delete on sight.

Detection:

```bash
# Tests that contain only assert!(true) or trivial unwrap
rg -A 5 "#\[test\]" --type rust | rg -B 5 "assert!\s*\(\s*true\s*\)"
```

## Pattern 3: re-implementing the function under test

```rust
// SLOP — test computes expected the same way the impl does
#[test]
fn test_double() {
    let input = vec![1, 2, 3];
    let expected: Vec<i32> = input.iter().map(|x| x * 2).collect();
    let actual = double_all(&input);
    assert_eq!(actual, expected);
}
```

If the test computes the expected value with the same
logic as the implementation, the test only verifies that
the implementation calls itself. The right pattern is
either:

- **Hand-coded fixtures**: `assert_eq!(double_all(&[1,2,3]), vec![2,4,6])`.
- **Property tests**: assert invariants (e.g. `for all x:
  double_all(x).len() == x.len() && all elements doubled`).
- **Golden-file tests**: serialize input → output → diff
  against checked-in expected.

Detection: this one is judgment-bound. Heuristic:

```bash
# Tests where the expected value is computed via iter/map/filter
rg -A 10 "#\[test\]" --type rust | rg "let expected.*=.*\.iter\(\)"
```

Surface for human review with `confidence: medium`.

## Pattern 4: mock-everything tests

```rust
// SLOP
#[tokio::test]
async fn test_handler() {
    let mock_db = MockDb::new();
    let mock_cache = MockCache::new();
    let mock_logger = MockLogger::new();

    let handler = Handler::new(mock_db.clone(), mock_cache.clone(), mock_logger.clone());
    handler.process().await;

    assert!(mock_db.was_called());
    assert!(mock_cache.was_called());
    assert!(mock_logger.was_called());
}
```

A test that mocks every collaborator and asserts that the
mock was called proves only that the orchestration calls
the orchestrator. The behavior under test (what
`process()` actually computes and persists) is not
verified.

Replace with:

- **Integration test**: real DB (sqlite or test container),
  real cache (in-memory), real logger (capturing).
- **Behavior test**: assert against the externally
  observable result, not against the call sequence.

Detection: count `Mock*` usages per test file:

```bash
rg "Mock[A-Z]\w+::" --type rust -c | sort -t: -k2 -nr | head -10
# Files with >5 Mock types per test are suspect
```

## Pattern 5: snapshot tests on non-deterministic data

```rust
// SLOP
#[test]
fn test_serialization_snapshot() {
    let user = User::new();  // generates UUID
    let serialized = serde_json::to_string(&user).unwrap();
    insta::assert_snapshot!(serialized);  // UUID changes every run
}
```

Snapshots on UUIDs, timestamps, hash maps with
non-deterministic iteration, or any randomness produce
flaky tests that get suppressed (`#[ignore]`) instead of
fixed.

Fix: use `BTreeMap` instead of `HashMap` for stable
iteration; inject a deterministic clock; use a fixed
UUID for testing; or assert on shape rather than
literal value.

Detection:

```bash
# Look for snapshot assertions near time/uuid usage
rg -B 3 "assert_snapshot" --type rust | rg -B 3 "(Uuid|Instant|Now|HashMap)"
```

## Pattern 6: one giant `test_everything()`

```rust
// SLOP
#[test]
fn test_full_flow() {
    // 200 lines asserting 30 unrelated things
}
```

A failing assertion stops the test, so subsequent
assertions never run; you only learn one failure per
suite execution. Split into focused tests.

Detection:

```bash
# Long test bodies (heuristic: tests with >50 lines of body)
awk '/^#\[test\]/ {start=NR; lines=0}
     /^fn / && start>0 {fn_start=NR}
     fn_start>0 {lines++}
     /^}$/ && fn_start>0 {if (lines > 50) print FILENAME":"start" length="lines; start=0; fn_start=0}' \
  $(find . -name "*.rs" -path "*/tests/*")
```

## Pattern 7: hidden side-effects

```rust
// SLOP
#[test]
fn test_persists() {
    let path = PathBuf::from("/tmp/test_output.json");  // hard-coded path
    write_to(&path, data);
    // ... no cleanup, races with parallel test runs
}

// SLOP
#[test]
fn test_api_call() {
    let resp = reqwest::blocking::get("https://api.example.com/data").unwrap();
    // real network call; flaky, slow, leaks
}
```

Use `tempfile::TempDir` for filesystem isolation,
`wiremock` or `httpmock` for HTTP isolation. Tests that
touch shared mutable state (filesystem, network,
database, env vars) without isolation cannot be parallel
and cannot be reliable.

Detection:

```bash
# Hard-coded /tmp paths
rg "/tmp/" --type rust tests/

# Real network calls in tests
rg "(reqwest|hyper)::.*\.get\(\"http" --type rust tests/
```

## Pattern 8: `#[ignore]` without a comment

```rust
// SLOP
#[test]
#[ignore]
fn test_flaky_thing() { ... }
```

A test marked ignored without explanation is technical
debt with no removal date. Either:

1. Fix the underlying flakiness.
2. Add a comment naming the bug or environment requirement
   (`#[ignore = "requires DB; #1234"]`).
3. Delete the test.

Detection:

```bash
# Find #[ignore] without trailing reason
rg "#\[ignore\]\s*$" --type rust
```

## Positive patterns to use instead

When pure functions are under-covered, prefer:

- **Property-based tests** (`proptest`, `quickcheck`):
  assert invariants over random inputs.
- **Golden-file tests**: serialize input → process →
  diff vs. checked-in expected output.
- **Mutation testing** (`cargo mutants`): proves the
  remaining tests catch real behavior changes.

## Mutation testing as the cheapest signal

The fastest way to expose AI-generated test slop is to
run mutation testing:

```bash
cargo install cargo-mutants
cargo mutants --workspace
```

Mutants that survive (the test suite still passes after
the mutation) indicate uncovered behavior. AI-generated
test suites typically have 60%+ surviving mutants because
they assert what the implementation does rather than what
the contract requires. A healthy human-written test suite
typically catches 70-90% of mutants.

For CI, run `cargo mutants` on a sampled subset (the most
recently changed files) to keep runtime under 10 minutes.

## Output format

Per the `Skill(scribe:slop-detector)` module
`structured-finding-output.md` format. Severity:

- **High**: any test in patterns 4 (mock-everything),
  5 (non-deterministic snapshot), 7 (hidden side-effects).
- **Medium**: any test in patterns 1 (`it_works`),
  2 (tautology), 6 (giant test).
- **Low**: any test in pattern 3 (re-implementation;
  judgment-bound).

Always surface pattern-3 findings as `confidence: medium`
since the line between "tests the contract" and
"re-implements the function" is genuinely subjective.

## Integration

Test slop landed in Pass 8 of the multi-pass cleanup
workflow (see `Skill(scribe:slop-detector)` module
`cleanup-workflow.md`). Run after architecture pass
(Pass 7) since refactoring can invalidate tests.
