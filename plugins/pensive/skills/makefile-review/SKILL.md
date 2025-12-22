---
name: makefile-review
description: |
  Audit Makefiles for duplication, portability, and idiomatic GNU Make usage.

  Triggers: Makefile review, build system, GNU Make, portability, deduplication,
  pattern rules, automatic variables, dependency graph

  Use when: auditing Makefiles, reviewing build system, checking portability,
  eliminating recipe duplication

  DO NOT use when: creating new Makefiles - use abstract:make-dogfood.
  DO NOT use when: architecture review - use architecture-review.

  Use this skill for Makefile audit and optimization.
category: build
tags: [makefile, build, make, portability, automation]
tools: [dependency-mapper, dedup-finder, portability-checker]
usage_patterns:
  - makefile-audit
  - build-optimization
  - portability-review
  - deduplication
complexity: intermediate
estimated_tokens: 150
progressive_loading: true
dependencies: [pensive:shared, imbue:evidence-logging]
modules:
  - dependency-graph
  - deduplication-patterns
  - portability-checks
  - best-practices
---

# Makefile Review Workflow

Audit Makefiles for best practices, deduplication, and portability.

## Quick Start

```bash
/makefile-review
```

## When to Use

- Makefile changes or additions
- Build system optimization
- Portability improvements
- CI/CD pipeline updates
- Developer experience improvements

## Required TodoWrite Items

1. `makefile-review:context-mapped`
2. `makefile-review:dependency-graph`
3. `makefile-review:dedup-candidates`
4. `makefile-review:tooling-alignment`
5. `makefile-review:evidence-logged`

## Workflow

### Step 1: Map Context (`makefile-review:context-mapped`)

Confirm baseline:
```bash
pwd && git status -sb && git diff --stat
```

Find Make-related files:
```bash
rg -n "^include" -g'Makefile*'
rg --files -g '*.mk'
```

Document changed targets, project goals, and tooling requirements.

### Step 2: Dependency Graph (`makefile-review:dependency-graph`)

@include modules/dependency-graph.md

### Step 3: Deduplication Audit (`makefile-review:dedup-candidates`)

@include modules/deduplication-patterns.md

### Step 4: Portability Check (`makefile-review:tooling-alignment`)

@include modules/portability-checks.md

### Step 5: Evidence Log (`makefile-review:evidence-logged`)

Use `imbue:evidence-logging` to record command outputs with file:line references.

Summarize findings:
- Severity (critical, major, minor)
- Expected impact
- Suggested refactors
- Owners and dates for follow-ups

## Progressive Loading

Load additional context as needed:

**Best Practices & Examples**: `@include modules/best-practices.md`

## Output Format

```markdown
## Summary
Makefile review findings

## Context
- Files reviewed: [list]
- Targets changed: [list]

## Dependency Analysis
[graph and issues]

## Duplication Candidates
### [D1] Repeated command
- Locations: [list]
- Recommendation: [pattern rule]

## Portability Issues
[cross-platform concerns]

## Missing Targets
- [ ] help
- [ ] format
- [ ] lint

## Recommendation
Approve / Approve with actions / Block
```

## Exit Criteria

- Context mapped
- Dependencies analyzed
- Deduplication reviewed
- Portability checked
- Evidence logged
