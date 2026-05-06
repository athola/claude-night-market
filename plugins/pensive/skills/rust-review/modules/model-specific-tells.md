---
module: model-specific-tells
category: meta-guidance
dependencies: [Read, Grep]
estimated_tokens: 600
---

# Model-Specific Tells

**Calibrate the audit weighting to the model that
generated the code. GPT fabricates; Claude omits;
reasoning-mode amplifies both.**

This module is meta-guidance: it tells the rust-review
audit *which* of its other modules to weight more heavily
based on which model produced the code under review. If
you cannot determine the model, run the full audit. The
2025-Q1 2026 cross-evaluation work (Sonar leaderboard,
Anthropic + DEV.to benchmarks) makes the calibration
defensible.

## GPT-5.x family (Codex, direct API)

**Default failure mode: fabrication.** Confidently invents
function names, library methods, config keys, API
endpoints, and lint names that look plausible but do not
exist.

Audit weighting:

- **High**: verify every `use` statement resolves. Verify
  every `Cargo.toml` entry exists on crates.io. Verify
  every method call against the relevant crate version.
  Verify every `cfg(...)` flag is actually defined.
  Verify every `#[clippy::...]` lint name appears in the
  upstream lint index.
- **High**: concurrency mistakes. Sonar measured ~470
  concurrency issues per million lines (MLOC) for
  GPT-5.2 High, nearly 2x the next-closest model. Audit
  `Send`/`Sync` bounds, `MutexGuard` lifetimes across
  `.await`, channel patterns, `Arc` cycles, and atomics.
  See `concurrency-patterns.md`.
- **Medium**: over-thorough doc-comment headers (parameter
  tables and usage examples on trivial functions). Trim;
  see `error-messages.md` for the doc-comment-bloat rule.
- **Medium**: Python-style defensive patterns (try-everything,
  log-everything) translated mechanically into Rust
  `Result` chains. Collapse with `?` or fold into typed
  errors. See `error-handling.md`.

Detection commands:

```bash
# Verify every use statement
rg "^use\s+" --type rust | sort -u > used.txt
# Cross-reference with declared deps
rg '^[a-z_]+\s*=' Cargo.toml | awk -F'=' '{print $1}' | tr -d ' "' | sort -u > deps.txt
# Diff (any dep used but not declared = potential phantom)

# Verify every cfg flag has a setter
rg "cfg\(([a-z_]+)\)" -o --no-filename --type rust | sort -u

# Verify every clippy::* lint name (cross-reference against upstream index)
rg "clippy::[a-z_]+" -o --no-filename --type rust | sort -u
```

## Claude 4.x family (Sonnet, Opus, Claude Code)

**Default failure mode: omission.** Silently skips edge
cases, drops match arms, leaves `None` paths unhandled,
defaults to `unreachable!()` without justification.

Audit weighting:

- **High**: non-exhaustive `match` arms. Sonar measured
  resource-management leaks at ~195/MLOC for Sonnet 4.5,
  nearly 4x the GPT-5.1 baseline. Audit explicit `Drop`
  order, `File`/socket close paths, scope-bound locks,
  any custom `Drop` impl.
- **High**: missing error paths. Look for `Option::None`
  handled as `unreachable!()` without a `// SAFETY:`
  or invariant comment justifying the unreachability.
- **High**: edge cases not in the test suite. The
  diagnostic question: *for every input domain, what
  happens?* If the test suite mirrors the implementation
  (asserts the same paths the implementation takes),
  the omitted cases are not covered. Use mutation testing
  (`cargo mutants`) to expose this.
- **Medium**: "behavior-preserving refactors" that leave
  dead branches in place because the model copied
  surrounding idioms verbatim. Read commit messages
  skeptically.
- **Medium**: safety-caveat-heavy doc comments on
  innocuous functions. Strip the caveats; keep the
  `# Safety` block only when actual unsafety exists.

Detection commands:

```bash
# Look for unreachable!() and panic!("not reachable") without SAFETY/invariant
rg -B 2 'unreachable!\(\)' --type rust | rg -v 'SAFETY|INVARIANT|invariant'

# Find non-exhaustive match arms (likely false positives, surface only)
rg "match\s+\w+\s*\{" --type rust -A 20 | grep -B 2 "_ =>" | head -40

# Custom Drop impls (high blast-radius for resource leaks)
rg "impl Drop for" --type rust

# Mutation testing exposes omission
cargo mutants --workspace 2>/dev/null | head -50
```

## Gemini 3.x

**Default failure mode: control-flow errors.** Sonar
measured ~200 control-flow mistakes per MLOC, ~4x Opus
4.5 Thinking. Off-by-one loops, missed early returns,
incorrect match arms, monolithic functions.

Audit weighting:

- **High**: branch correctness in any function over ~50
  lines. Read every branch top-to-bottom; check for the
  early-return that should have been there.
- **High**: off-by-one in any loop with manual indexing
  (`for i in 0..n` vs. `for x in slice`). See
  `collection-types.md` for the `clippy::needless_range_loop`
  detector.
- **Medium**: monolithic functions (>100 lines) that
  could be refactored into named helpers.

## Any "Thinking" / "Reasoning" / "High-effort" mode

**Verbosity scales with reasoning depth.** The Sonar
leaderboard plot puts bubble size = verbosity, x-axis =
pass rate; both grow together. Reasoning-mode output
needs *aggressive* trimming by default. The reasoning
surfaces in:

- Higher cyclomatic complexity per function.
- Longer parameter lists.
- More cleverness (lifetime tricks, `impl Trait`
  combinators where a concrete type would do).
- More layers of abstraction.

All compound the maintenance bill. Read reasoning-mode
output as a *first draft*, not as production code.

Detection: run `cargo clippy --all-targets -- -W
clippy::cognitive_complexity -W clippy::too_many_lines`
and treat the resulting warnings as load-bearing, not
cosmetic.

## When you cannot tell which model

Default to running the full audit. It is never wrong,
just sometimes redundant.

**Heuristic for inferring the model from artifacts**:

| Signal | Likely source |
|---|---|
| Lots of `Box<dyn Error>` returns + tutorial-style doc comments | GPT-family from a "convert this Python to Rust" prompt |
| `unreachable!()` without SAFETY comment, sparse tests | Claude-family from a refactoring prompt |
| 150-line function with 7 sequential `if let` + lots of mut | Gemini-family from a "implement this from spec" prompt |
| 200-character lifetime annotations and `impl Trait` chains | Any model in reasoning mode |
| "As a large language model" leaks | Bug, regardless of model — escalate to scribe:slop-detector |

These are heuristics, not proofs. Use them to *weight*
the audit, not to attribute authorship.

## Currency note

The model-specific multipliers above are tied to specific
model versions and dates (Q4 2025 / Q1 2026). Model
behavior changes faster than this module can. The
*pattern* (model families have predictable failure
profiles, reasoning amplifies verbosity) will persist;
the specific numbers will not.

Re-validate against:

- Sonar's live LLM leaderboard.
- Latest CodeRabbit / Apiiro / Veracode reports.
- Your own internal defect data.

See `Skill(scribe:slop-detector)` module
`empirical-baseline.md` for the full citation list and
the language-agnostic version of this calibration.
