---
module: evidence-backed-claims
category: detection
dependencies: [Grep, Read, Bash]
estimated_tokens: 600
---

# Evidence-Backed Claims

**Every quality claim must point to evidence in the same
repository. No evidence, delete the claim.**

This module operationalizes the §2.4 README rule from the
AI slop playbook. It is the highest-leverage prose check
for crate/library/project READMEs, because feature-list
buzzword soup is the most common AI-generated README
failure mode.

## The rule

For each quality claim, the repository must contain the
evidence that backs it. If the evidence does not exist,
the claim is marketing slop and must be deleted.

## Required-evidence table

| Claim | Required evidence |
|-------|-------------------|
| "Production-ready" | CI workflow, release process doc, version >= 1.0, named adopters |
| "Fast" / "Blazing fast" / "High-performance" | `benches/` directory with reproducible benchmark + numbers |
| "Memory-safe" / "Safe" | `#![forbid(unsafe_code)]`, audited unsafe blocks, or fuzz harness |
| "Zero-cost" | benchmark vs. equivalent unabstracted code |
| "Type-safe" | named the type system property, or strict mode enabled |
| "Fault-tolerant" | tests covering the failure modes named |
| "Resilient" | retry logic + tests of failure paths |
| "Scalable" | load tests, capacity numbers, or deployment story |
| "Battle-tested" | named adopters, version history, issue-resolution track |
| "Robust" | replace with concrete error-handling guarantees + test coverage |
| "Idiomatic" | replace with "passes [linter] -- -D warnings" |
| "Secure" | threat model, audit reference, or `cargo audit`/equivalent in CI |
| "Easy to use" | three-line "minimal example" that actually runs |
| "Well-tested" | coverage % from a real run, or test count |
| "Well-documented" | docs.rs / readthedocs link with non-trivial content |
| "Cross-platform" | named platforms with CI matrix |
| "Lightweight" | binary size, dep count, or LOC number |
| "No dependencies" | empty `[dependencies]` or named exceptions |

## Detection

For each claim word/phrase in the README and other
public-facing docs, check whether the corresponding
evidence exists.

### Pattern 1: simple grep + file existence

```bash
# Does the README claim "production-ready"?
grep -i 'production[- ]ready' README.md

# Then verify the evidence:
[ -d ".github/workflows" ] && echo "CI exists" || echo "MISSING: CI"
[ -f "RELEASE.md" ] || [ -f "RELEASING.md" ] && echo "release doc exists" || echo "MISSING: release process"
grep -E '^version = "[1-9]' Cargo.toml *.toml 2>/dev/null || echo "MISSING: version >= 1.0"
```

### Pattern 2: claim → benchmark cross-reference

```bash
# Does the README claim "fast"?
grep -iE '\b(fast|blazing|high[- ]performance)\b' README.md

# Then verify benchmarks exist with results:
[ -d "benches/" ] || [ -d "benchmarks/" ] || echo "MISSING: benches dir"
ls benches/ 2>/dev/null | grep -E '\.(rs|py|js|ts)$' || echo "MISSING: benchmark sources"

# And ideally that BENCHMARKS.md exists with numbers:
[ -f "BENCHMARKS.md" ] && echo "results documented" || echo "WARN: no published results"
```

### Pattern 3: safety claims vs. unsafe usage

```bash
# Does the README claim "safe" or "memory-safe"?
grep -iE 'memory[- ]safe|"safe"' README.md

# Then verify the project enforces it:
grep -r '#!\[forbid(unsafe_code)\]' src/ && echo "unsafe forbidden"

# Or that any unsafe blocks have SAFETY comments:
unsafe_count=$(rg -c 'unsafe\s*\{' src/ | awk -F: '{s+=$2} END {print s}')
safety_count=$(rg -c '// SAFETY:' src/ | awk -F: '{s+=$2} END {print s}')
[ "$unsafe_count" -gt 0 ] && [ "$safety_count" -lt "$unsafe_count" ] && \
  echo "FAIL: $unsafe_count unsafe blocks, only $safety_count SAFETY comments"
```

## README-specific anti-patterns

Beyond claim verification, the playbook §2.4 lists
structural anti-patterns common in AI-generated READMEs:

### Pattern A: Features-list-as-first-section

A good README opens with:
1. One sentence: what it is.
2. Minimal working example (5-15 lines, runnable).
3. Install instruction.

Then features, configuration, contributing, etc.

Detection: if the first section after the title is a
bullet list of features, flag for restructuring.

### Pattern B: TOC in a short README

A 200-line README does not need a table of contents.
GitHub auto-generates one. Detection:

```bash
lines=$(wc -l < README.md)
has_toc=$(grep -c '## Table of Contents\|## Contents' README.md)
[ "$lines" -lt 300 ] && [ "$has_toc" -gt 0 ] && \
  echo "FAIL: README is short enough that TOC is noise"
```

### Pattern C: Emoji-prefixed feature bullets

Lines like:

```
- 🚀 Fast
- 🔒 Safe
- 🎯 Easy
```

Strip the emoji; if the bullet still says something, keep
the bullet. If the bullet only had value because of the
emoji, delete it.

Detection:

```bash
grep -E '^- (\\xF0\\x9F|🚀|🔒|🎯|✨|⚡)' README.md
```

### Pattern D: "Why X?" section that doesn't compare

A "Why our crate?" section that recites generic benefits
("safe, fast, easy") without naming specific alternatives
or making falsifiable claims is slop. Either:
- Rewrite to compare against named alternatives with
  specifics.
- Delete the section.

### Pattern E: Status badges that don't match reality

A green CI badge for a workflow that no longer exists is
worse than no badge.

Detection:

```bash
# Extract badge URLs
grep -oE 'https://img.shields.io/[^)]+|https://github.com/[^/]+/[^/]+/actions/[^)]+' README.md

# Verify each linked workflow exists and is green
# (manual check, or use gh-actions API)
```

### Pattern F: `-rs` / `-rust` suffix in crate name

Per Rust API Guidelines: redundant. Detection in
`Cargo.toml`:

```bash
grep -E '^name = ".*-(rs|rust)"' Cargo.toml && echo "REDUNDANT suffix"
```

(Same applies to `-py`/`-python`, `-js`/`-javascript`,
`-go`/`-golang` in their respective ecosystems, flag
the redundancy.)

## Output format

```
[FINDING N]
file:        README.md
line:        12
category:    evidence-backed-claims/unverified-claim
severity:    medium
confidence:  high
evidence:    > A blazing-fast, production-ready, memory-safe
             > library for parsing JSON:
rationale:   Three claims in one sentence, none backed:
             - "blazing-fast": no benches/ directory
             - "production-ready": no CI, version 0.1.2
             - "memory-safe": no #![forbid(unsafe_code)]
                and 14 unsafe blocks in src/, only 3 with
                SAFETY comments
fix:         Either:
             1. Add the evidence (benches, CI, audit unsafe)
                and keep the claims.
             2. Replace with: "A library for parsing JSON.
                Pre-1.0; benchmarks in progress."
             Default to option 2 unless option 1 is on
             the actual roadmap.
```

## Anti-goal

This module is *not* a vibe check. It does not flag claims
that are *imprecise*: only claims that are *unevidenced*.
"Fast" is fine if `benches/` exists. "Safe" is fine if
unsafe blocks are documented. The bar is evidence, not
modesty.

When in doubt: flag for human review. The cost of a false
positive (a real claim deleted) is higher than the cost of
a false negative (a false claim left in).
