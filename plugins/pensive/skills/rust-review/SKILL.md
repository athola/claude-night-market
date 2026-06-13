---
name: rust-review
description: Audits Rust code for unsafe blocks, ownership issues, and Cargo dependency risks. Use when reviewing Rust code or before merging Rust changes.
globs: "**/*.rs"
alwaysApply: false
category: code-review
tags:
- rust
- ownership
- concurrency
- unsafe
- traits
- cargo
tools: []
usage_patterns:
- rust-audit
- unsafe-review
- dependency-audit
- concurrency-analysis
complexity: advanced
model_hint: deep
estimated_tokens: 400
progressive_loading: true
dependencies:
- pensive:shared
- imbue:proof-of-work
- imbue:review-core
- imbue:structured-output
modules:
- ownership-analysis.md
- error-handling.md
- concurrency-patterns.md
- unsafe-audit.md
- cargo-dependencies.md
- silent-returns.md
- collection-types.md
- sql-injection.md
- cfg-test-misuse.md
- error-messages.md
- duplicate-validators.md
- builtin-preference.md
- native-type-modeling.md
- idiomatic-elision.md
- numeric-cast-safety.md
- mutable-static-audit.md
- match-wildcard.md
- transmute-audit.md
- float-equality.md
- mem-forget-audit.md
- repr-packed-audit.md
- model-specific-tells.md
- iterator-and-allocation-slop.md
- test-slop.md
- async-slop.md
---
## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [Required TodoWrite Items](#required-todowrite-items)
- [Progressive Loading](#progressive-loading)
- [Core Workflow](#core-workflow)
- [Rust Quality Checklist](#rust-quality-checklist)
- [Safety](#safety)
- [Correctness](#correctness)
- [Performance](#performance)
- [Idioms](#idioms)
- [Output Format](#output-format)
- [Summary](#summary)
- [Ownership Analysis](#ownership-analysis)
- [Error Handling](#error-handling)
- [Concurrency](#concurrency)
- [Unsafe Audit](#unsafe-audit)
- [[U1] file:line](#[u1]-file:line)
- [Dependencies](#dependencies)
- [Recommendation](#recommendation)
- [Exit Criteria](#exit-criteria)


# Rust Review Workflow

Expert-level Rust code audits with focus on safety, correctness, and idiomatic patterns.

## Quick Start

```bash
/rust-review
```
**Verification:** Run the command with `--help` flag to verify availability.

## When To Use

- Reviewing Rust code changes
- Auditing unsafe blocks
- Analyzing concurrency patterns
- Dependency security review
- Performance optimization review

## When NOT To Use

- General code review without Rust - use unified-review
- Performance profiling - use parseltongue:python-performance pattern

## Required TodoWrite Items

1. `rust-review:ownership-analysis`
2. `rust-review:error-handling`
3. `rust-review:concurrency`
4. `rust-review:unsafe-audit`
5. `rust-review:cargo-deps`
6. `rust-review:native-modeling`
7. `rust-review:idiomatic-elision`
8. `rust-review:numeric-cast-safety`
9. `rust-review:mutable-static-audit`
10. `rust-review:match-wildcard`
11. `rust-review:transmute-audit`
12. `rust-review:float-equality`
13. `rust-review:mem-forget-audit`
14. `rust-review:repr-packed-audit`
15. `rust-review:evidence-log`
16. `rust-review:findings-verified`

## Progressive Loading

Load modules as needed based on review scope:

**Quick Review** (ownership and errors):
- See `modules/ownership-analysis.md` for borrowing and lifetime analysis
- See `modules/error-handling.md` for Result/Option patterns

**Concurrency Focus**:
- See `modules/concurrency-patterns.md` for async and sync primitives

**Safety Audit**:
- See `modules/unsafe-audit.md` for unsafe block documentation
- See `modules/mutable-static-audit.md` for `static mut` globals and
  their thread-safe replacements
- See `modules/numeric-cast-safety.md` for truncating and
  precision-losing `as` casts
- See `modules/match-wildcard.md` for catch-all arms that defeat enum
  exhaustiveness
- See `modules/transmute-audit.md` for `mem::transmute`/`transmute_copy`
  calls that reinterpret bytes with no layout check
- See `modules/repr-packed-audit.md` for `#[repr(packed)]` layouts whose
  field borrows become unaligned references

**Correctness Audit**:

- See `modules/float-equality.md` for `==`/`!=` against float literals
- See `modules/mem-forget-audit.md` for `mem::forget` leaks and no-op
  `drop(&x)` reference drops

**Dependency Review**:
- See `modules/cargo-dependencies.md` for vulnerability scanning

**Idiomatic Patterns**:
- See `modules/builtin-preference.md` for conversion traits and builtin preference
- See `modules/native-type-modeling.md` for enums-over-primitives,
  newtype, type-state, and derived ordering
- See `modules/idiomatic-elision.md` for lifetime elision and
  expression-oriented returns

## Core Workflow

1. **Ownership Analysis**: Check borrowing, lifetimes, clone patterns
2. **Error Handling**: Verify Result/Option usage, propagation
3. **Concurrency**: Review async patterns, sync primitives
4. **Unsafe Audit**: Document invariants, FFI contracts
5. **Dependencies**: Scan for vulnerabilities, updates
6. **Evidence Log**: Record commands and findings

## Rust Quality Checklist

### Safety
- [ ] All unsafe blocks documented with SAFETY comments
- [ ] FFI boundaries properly wrapped
- [ ] Memory safety invariants maintained
- [ ] No `static mut` globals; shared state uses `OnceLock`/`LazyLock`,
  atomics, or a `Mutex`/`RwLock`
- [ ] No `mem::transmute`/`transmute_copy`; bytes converted with
  `from_le_bytes`/`from_bits`/`bytemuck` or pointers with `.cast()`
- [ ] `#[repr(packed)]` fields copied out before borrowing (no unaligned
  references)
- [ ] No `mem::forget` leaks (use `ManuallyDrop`/scope) and no no-op
  `drop(&x)` reference drops
- [ ] `mlock`/`munlock` calls: RLIMIT verified, page-aligned,
  ENOMEM handled

### Correctness
- [ ] Error handling complete
- [ ] Concurrency patterns sound
- [ ] Lossy `as` casts (length truncation, `as u8`/`i8`, `as f32`)
  replaced with `TryFrom`/`From`
- [ ] Enum matches exhaustive; no `_ => unreachable!()`/`panic!`/`{}`
  catch-alls
- [ ] Floats compared with a tolerance, not exact `==`/`!=` against a
  float literal
- [ ] Tests cover critical paths

### Performance
- [ ] No unnecessary allocations
- [ ] Borrowing preferred over cloning
- [ ] Async properly non-blocking

### Idioms
- [ ] Standard traits implemented
- [ ] Conversion traits preferred over helper functions
- [ ] Stringly-typed values and boolean flags modeled as enums
- [ ] Domain invariants encoded with newtypes (private field +
  validating constructor) or type-state where warranted
- [ ] Comparison/ordering traits derived, not hand-written
- [ ] Lifetimes elided where elision rules apply; `'_` in paths
- [ ] Trailing `return` dropped in favor of the tail expression
- [ ] Error types well-designed
- [ ] Documentation complete

## Output Format

```markdown
## Summary
Rust audit findings

## Ownership Analysis
[borrowing and lifetime issues]

## Error Handling
[error patterns and issues]

## Concurrency
[async and sync patterns]

## Unsafe Audit
### [U1] file:line
- Invariants: [documented]
- Anchor: `verbatim source text at file:line`
- Risk: [assessment]
- Recommendation: [action]

## Native Type Modeling
[stringly-typed comparisons, boolean blindness, newtype/type-state notes]

## Idiomatic Elision
[needless lifetimes, trailing returns the compiler infers]

## Numeric Cast Safety
[length-truncating, byte-narrowing, and f32 precision-losing `as` casts]

## Mutable Static Audit
[`static mut` globals and their thread-safe replacements]

## Match Wildcard
[catch-all `_ =>` arms that defeat enum exhaustiveness]

## Transmute Audit
[`mem::transmute`/`transmute_copy` calls and their typed replacements]

## Float Equality
[exact `==`/`!=` comparisons against float literals]

## Mem Forget Audit
[`mem::forget` leaks and no-op `drop(&x)` reference drops]

## Repr Packed Audit
[`#[repr(packed)]` layouts whose field borrows become unaligned]

## Dependencies
[cargo audit results]

## Recommendation
Approve / Approve with actions / Block
```
**Verification:** Run the command with `--help` flag to verify availability.

## Verify Findings Are Grounded (`rust-review:findings-verified`)

Every finding must cite a real location and a verbatim anchor. Write
findings to `.review/findings.json` and confirm each citation resolves:

```bash
python plugins/imbue/scripts/citation_verifier.py \
  --findings .review/findings.json --repo-root .
```

Drop or label `UNVERIFIED` any finding the verifier fails (exit `1`); only
verified findings enter the report. See `Skill(imbue:review-core)` Step 5
and `Skill(imbue:structured-output)` for the schema.

## Exit Criteria

- All unsafe blocks audited
- Concurrency patterns verified
- Dependencies scanned
- Evidence logged
- Action items assigned
- Every reported finding carries a `Location` + verbatim `Anchor` confirmed by `citation_verifier.py` (exit `0`), or unverified findings were dropped or labeled `UNVERIFIED`
