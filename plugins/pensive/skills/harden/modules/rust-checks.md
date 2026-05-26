# Rust Hardening Checks

Detectors for Rust codebases. The Rust ecosystem ships strong
default safety; the harden skill verifies the discipline is
actually applied and the supply chain is curated.

For a deep ownership/unsafe audit, the skill defers to
`Skill(pensive:rust-review)`. This module focuses on the
hardening posture (capability use, supply-chain hygiene,
side-channel defense) and frontier 2025-2026 practices.

## Detection ruleset

| ID | Check | CWE / RustSec | NIST SSDF | Detection signal |
|----|-------|---------------|-----------|------------------|
| RS01 | Crate root lacks `#![forbid(unsafe_code)]` and does not declare audited unsafe | CWE-119 | PW.5 | `lib.rs`/`main.rs` without forbid; no `audit/unsafe.md` |
| RS02 | Unsafe block without `// SAFETY:` comment | CWE-119 | PW.7 | `unsafe {` not preceded by `// SAFETY:` line |
| RS03 | `unwrap()` / `expect()` on caller-supplied data | CWE-754 | PW.5 | `.unwrap()` after `parse()`, `from_str`, `serde::from_*` on external input |
| RS04 | `panic!` reachable from request handler | CWE-754 | PW.5 | `panic!`, `unimplemented!`, `unreachable!` on user-input branches |
| RS05 | `cargo audit` not wired to CI | RV.1 | RV.1 | no `cargo audit` step in `.github/workflows/*.yml` |
| RS06 | `cargo deny` config missing or not enforced | RV.1 | PW.4 | no `deny.toml` or CI step missing |
| RS07 | `cargo vet` audits stale / missing for new deps | RV.2 | PW.4 | `supply-chain/audits.toml` does not cover new entries in `Cargo.lock` |
| RS08 | Comparing secrets with `==` | CWE-208 | PW.5 | `==` between `&[u8]` typed as token/secret/digest; should be `subtle::ConstantTimeEq` |
| RS09 | Secrets not zeroized on drop | CWE-316 | PW.5 | secret-typed struct without `Zeroize`/`ZeroizeOnDrop` |
| RS10 | Async cancellation un-safe | CWE-362 | PW.5 | `tokio::select!` arms with non-cancel-safe futures (e.g., `BufReader::read_to_end`) |
| RS11 | `Mutex::lock().unwrap()` in hot path | CWE-754 | PW.5 | poisoned-lock unwrap reachable from public API |
| RS12 | Source replacement to private registry without integrity pin | CWE-494 | PW.4 | `[source.crates-io]` `replace-with` without checksum |
| RS13 | Git dependency without `rev=` | CWE-494 | PW.4 | `git = "..."` without `rev = "..."` (mutable target) |
| RS14 | Build script (`build.rs`) reads files outside `OUT_DIR` | CWE-829 | PW.6 | `build.rs` opens path containing `..` |
| RS15 | `serde(deny_unknown_fields)` missing on auth-bearing structs | CWE-1287 | PW.5 | struct deriving `Deserialize` for an auth/config payload without `#[serde(deny_unknown_fields)]` |
| RS16 | Compiler hardening flags absent | CWE-1244 | PW.6 | `.cargo/config.toml` missing `RUSTFLAGS` for stack protection / CFI |
| RS17 | `unsafe impl Send/Sync` without proof | CWE-362 | PW.7 | `unsafe impl (Send|Sync) for ...` without SAFETY comment |
| RS18 | FFI without bounds annotation | CWE-787 | PW.5 | `extern "C"` function with `*const T` / `*mut T` arg with no length param |

## Tooling integration

```bash
# Vulnerability scan against RustSec advisory DB
cargo audit --json > /tmp/harden-cargo-audit.json

# Policy enforcement (license, advisory, source, ban list)
cargo deny check --format json 2>/tmp/harden-deny.json

# Cryptographic-supply-chain audit
cargo vet check 2>&1 | tee /tmp/harden-vet.log

# Unsafe block inventory (third-party tool; requires install)
cargo geiger --output-format json > /tmp/harden-geiger.json

# Mutation testing (high-leverage; expensive)
cargo mutants --in-diff origin/main..HEAD --no-times --json
```

The harden report joins these on file:line and advisory ID.

## Capability-style hardening (frontier 2025-2026)

| From | To | Why |
|------|-----|-----|
| `std::fs` ambient access | `cap-std::fs::Dir` capability | filesystem ops require an explicit handle, not a path |
| raw `socket`/`std::net` | `cap-std::net` | network endpoints are capabilities, not strings |
| environment-driven config | `secrecy::SecretString` for secrets | wrapper prevents `Debug`/`Display` leaks |
| ad-hoc retry loops | `tower::retry` with backoff and budget | bounded resource consumption (CWE-400) |

These are recommendations, not blocking findings — surface in
the report as MEDIUM advisories with the rationale in the
proposal.

## Concurrency hardening

| Pattern | Replace with | Reason |
|---------|--------------|--------|
| naked `std::sync::Mutex` in hot path | `parking_lot::Mutex` (no poisoning, smaller, faster) | reduces unwrap-on-poison footguns |
| ad-hoc `Arc<Mutex<HashMap>>` | `dashmap::DashMap` | lock-free reads, sharded writes |
| `tokio::sync::Mutex` held across `await` | `parking_lot::Mutex` for short critical sections | avoid tokio scheduler stalls |
| `loom`-untested concurrent code | wire `cargo test --features loom` for lock-free types | model-checks all interleavings |

## Compiler hardening flags

In `.cargo/config.toml`:

```toml
[target.'cfg(all())']
rustflags = [
    # Stack-smashing protection
    "-C", "force-frame-pointers=yes",
    # Disable sources of UB
    "-D", "warnings",
    # Treat unsafe-op-without-unsafe-fn as error in 2024 edition
    "-D", "unsafe_op_in_unsafe_fn",
]
```

For sanitizer-instrumented test runs:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu
```

## Output schema

Same as `python-checks.md`. Each Rust finding emits a single
proposal with diff, blast radius, reversal plan, and expected
test. RustSec IDs go in the citation column when applicable.
