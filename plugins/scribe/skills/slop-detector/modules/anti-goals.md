---
module: anti-goals
category: safety
dependencies: [Read]
estimated_tokens: 500
---

# Anti-Goals: What NOT to Clean Up

**Aggressive de-slopping has its own failure modes.**

This module is the safety rail. Every other module in the
slop-detector tells you what to flag and remove; this one
tells you what to *leave alone* even when it pattern-
matches. The bar for deletion is higher than the bar for
flagging.

When in doubt: leave it alone, surface it as a finding,
and let a human decide.

## Class 1: Comments that earn their bytes

These look like slop on density alone but carry meaning
the code does not:

### Why-comments (always keep)

A comment that explains *why* a non-obvious decision was
made is the highest-value comment class. The code is the
"what"; comments earn their place by carrying the "why".

```rust
// We sleep 200ms specifically because the upstream
// rate-limiter buckets at 5/s; faster retries return
// 429 and waste a slot:
thread::sleep(Duration::from_millis(200));
```

This pattern-matches as a "magic constant with comment"
which §3.2 flags as marketing slop, but it is the
*opposite* of slop: the comment names the constraint that
makes the constant correct.

**Rule**: a comment that names a constraint, references an
upstream contract, or explains a counter-intuitive choice
is information the code cannot carry. Keep it.

### Safety comments on `unsafe` blocks (always keep)

```rust
// SAFETY: the caller has already validated that `idx`
// is within `slice.len()`; see the bounds check in
// `Buffer::insert` two frames up:
unsafe { *slice.as_ptr().add(idx) }
```

These are *required* by `clippy::undocumented_unsafe_blocks`
and are part of the contract the code makes with reviewers.
Stripping them removes the only proof the unsafe block is
correct.

### Structured-meaning comment prefixes (always keep)

Many codebases adopt structured prefixes for specific
comment classes. Examples:

```
// SAFETY: ...
// INVARIANT: ...
// LOCK ORDER: ...
// BLOCKING: ...
// PERFORMANCE: ...
// SECURITY: ...
// THREAD: ...
```

These are project-specific contracts. They are not slop
even if they look formulaic: the formula *is* the
contract. Audit before stripping; do not strip on pattern
match alone.

### Regression-pinning tests (always keep)

A test that looks trivial (`assert!(parse("").is_err())`)
may be pinning a regression. Deleting it because it "looks
slop" is exactly how the regression returns.

**Rule**: tests with bug-tracker references in their name
or comment (`test_regression_1234`, `// repro for #1234`)
must not be removed without an explicit decision that the
regression class is no longer relevant.

## Class 2: Code that should not be flattened

### `thiserror`-style error variants (do not collapse)

```rust
#[derive(Error)]
pub enum Error {
    #[error("connection refused")]
    ConnectionRefused,
    #[error("timeout after {0}s")]
    Timeout(u64),
    #[error("invalid response: {0}")]
    InvalidResponse(String),
    // ... 9 more variants, several rare ...
}
```

The "12 variants, of which 3 are ever constructed
internally" pattern from §6 looks like inflation, but
*public error enums are part of the API*. Removing
variants:
- Breaks downstream pattern-match exhaustiveness checks.
- Removes information that helps users handle specific
  failures.
- Cannot be reversed without a major-version bump.

**Rule**: never collapse public error variants without an
explicit major-version-bump decision.

### Small named helpers (do not inline)

```rust
fn is_ascii_alphabetic_or_underscore(c: char) -> bool {
    c.is_ascii_alphabetic() || c == '_'
}
```

This is two lines and looks like inflation, but the *name*
makes the calling code readable:

```rust
if is_ascii_alphabetic_or_underscore(c) { ... }
```

vs. the inlined version:

```rust
if c.is_ascii_alphabetic() || c == '_' { ... }
```

The inline reads as "checking ascii alpha or underscore";
the named version reads as "checking the leading-char
rule". The function carries domain meaning.

**Rule**: a one-line helper with a domain-specific name is
not slop. Inline only when the name adds no clarity over
the inline expression.

### `Result<T, MyError>` (do not "simplify" to `Box<dyn Error>`)

The "simplify the error type" instinct is *backward*
direction. Typed errors at API boundaries are correct;
boxed dynamic errors are tutorial code.

**Rule**: never replace a typed error with `Box<dyn Error>`
or `anyhow::Error` in a public library API as part of a
slop sweep. That is an API-design decision, not a cleanup.

## Class 3: Files that must not be touched

### Generated code

```
build.rs output
prost/tonic generated modules
bindgen output
serde_derive/serde_json schemas
GraphQL codegen
OpenAPI/Swagger codegen
protoc output
```

Generated code follows the conventions of its generator.
It often looks bloated by human-written-code standards
because the generator is conservative. Editing it is
pointless: the next regeneration overwrites the changes.

**Rule**: detect generated code by header comment ("DO NOT
EDIT", "AUTOMATICALLY GENERATED", or generator-specific
markers) or by directory convention (`target/`,
`generated/`, `gen/`, `__generated__/`). Exclude from
all slop scans.

### Vendored / third-party code

Code copied from another project (with attribution)
follows the upstream's conventions. Reformatting it to
match local style breaks the ability to diff against
upstream for security updates.

**Rule**: directories named `vendor/`, `third_party/`,
`thirdparty/`, or `external/` are excluded from style
sweeps.

### Historical changelog entries

```
## [1.2.0] - 2024-03-15

- Added `parse_json` function with `comprehensive` error
  reporting.   <-- "comprehensive" is slop in new prose,
                   but this is a historical artifact.
```

Past releases are immutable. Editing changelog entries
rewrites history readers may have relied on (vendor
SBOMs, audit trails, blog-post backreferences).

**Rule**: anything before the `## [Unreleased]` header
in a CHANGELOG file is read-only.

### Migration scripts and historical fixtures

A test fixture that contains slop *because the original
input was sloppy* is correct as-is. The test exists to
prove the parser handles real-world slop, and "fixing"
the fixture removes the very thing under test.

**Rule**: directories named `fixtures/`, `golden/`,
`testdata/`, `examples/` (when used as test inputs) are
excluded from prose sweeps.

## Class 4: Patterns that look generated but are not

### Section headings that follow a template

```
## Installation
## Usage
## Configuration
## API Reference
## Contributing
## License
```

These look formulaic because every README has them. They
are not slop: they are the convention. Removing them
because they are predictable would make the README harder
to navigate, not easier.

**Rule**: structural conventions (canonical README
sections, standard rustdoc sections like `# Examples` /
`# Errors` / `# Panics`, conventional commit prefixes) are
not slop. Flag only when content *inside* the section
violates a rule.

### Em-dash density in narrative writing

§2.3 flags em-dash density >3 per 500 words as a signal.
This is a *heuristic*, not a rule. A novelist or essayist
who uses em dashes deliberately for rhythm is not
generating AI text.

**Rule**: em-dash density flags require human review
before edits. In narrative or literary genres, leave the
em dashes alone unless other signals also fire.

## Class 5: When a finding is "low confidence"

The slop-detector should never auto-apply low-confidence
fixes. From the structured-finding format in §10:

> The agent should **not** silently apply low-confidence
> fixes; surface them as findings with `confidence: low`
> and let a human decide.

Categories that default to `confidence: low`:

- Premature abstraction (§4.9): impossible to prove an
  abstraction is wrong without knowing future use.
- Generic name slop (§4.10): "Manager" is wrong in some
  domains and exactly right in others.
- Bullet-list-bloat: the right number of bullets depends
  on whether the content is actually enumerable.
- Em-dash density in narrative.
- Anything in `examples/` or under a `// AI-generated:
  do not delete` marker.

## Override mechanism

For unavoidable false positives, projects should support
inline ignore markers:

```html
<!-- slop-detector:ignore-next-line vocabulary -->
The comprehensive integration tests cover ...

<!-- slop-detector:ignore-block start -->
[block of intentionally-formulaic content]
<!-- slop-detector:ignore-block end -->
```

```rust
// slop-detector:allow(needless_clone)
let owned = borrowed.clone();
```

These are escape hatches, not silencers. Each ignore
marker should explain *why* in a trailing comment:

```html
<!-- slop-detector:ignore-next-line vocabulary
     reason: "comprehensive" is the documented test-suite
     name; renaming it breaks external references -->
```

Without the rationale, the ignore is itself a defect.
