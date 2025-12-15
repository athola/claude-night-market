---
name: rust-review
description: Expert-level Rust audits covering ownership, concurrency, unsafe blocks, traits, and Cargo dependencies. Use for Rust-specific code review.
category: code-review
tags: [rust, ownership, concurrency, unsafe, traits, cargo]
tools: [borrow-checker-analyzer, unsafe-auditor, dependency-scanner]
usage_patterns:
  - rust-audit
  - unsafe-review
  - dependency-audit
  - concurrency-analysis
complexity: advanced
estimated_tokens: 400
progressive_loading: true
dependencies:
  - pensive:shared
  - imbue:evidence-logging
modules:
  - ownership-analysis.md
  - error-handling.md
  - concurrency-patterns.md
  - unsafe-audit.md
  - cargo-dependencies.md
---

# Rust Review Workflow

Expert-level Rust code audits with focus on safety, correctness, and idiomatic patterns.

## Quick Start

```bash
/rust-review
```

## When to Use

- Reviewing Rust code changes
- Auditing unsafe blocks
- Analyzing concurrency patterns
- Dependency security review
- Performance optimization review

## Required TodoWrite Items

1. `rust-review:ownership-analysis`
2. `rust-review:error-handling`
3. `rust-review:concurrency`
4. `rust-review:unsafe-audit`
5. `rust-review:cargo-deps`
6. `rust-review:evidence-log`

## Progressive Loading

Load modules as needed based on review scope:

**Quick Review** (ownership + errors):
- @include ownership-analysis.md
- @include error-handling.md

**Concurrency Focus**:
- @include concurrency-patterns.md

**Safety Audit**:
- @include unsafe-audit.md

**Dependency Review**:
- @include cargo-dependencies.md

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

### Correctness
- [ ] Error handling complete
- [ ] Concurrency patterns sound
- [ ] Tests cover critical paths

### Performance
- [ ] No unnecessary allocations
- [ ] Borrowing preferred over cloning
- [ ] Async properly non-blocking

### Idioms
- [ ] Standard traits implemented
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
- Risk: [assessment]
- Recommendation: [action]

## Dependencies
[cargo audit results]

## Recommendation
Approve / Approve with actions / Block
```

## Exit Criteria

- All unsafe blocks audited
- Concurrency patterns verified
- Dependencies scanned
- Evidence logged
- Action items assigned
