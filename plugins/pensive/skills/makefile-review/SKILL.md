---
name: makefile-review
description: Audits Makefiles for build correctness, portability, and recipe duplication. Use when reviewing a Makefile or before committing Makefile changes.
globs: "**/Makefile"
alwaysApply: false
category: build
tags:
- makefile
- build
- make
- portability
- automation
tools: []
usage_patterns:
- makefile-audit
- build-optimization
- portability-review
- deduplication
complexity: intermediate
model_hint: standard
estimated_tokens: 150
progressive_loading: true
dependencies:
- imbue:proof-of-work
- imbue:review-core
- imbue:structured-output
modules:
- modules/dependency-graph.md
- modules/deduplication-patterns.md
- modules/portability-checks.md
- modules/best-practices.md
- modules/plugin-dogfood-checks.md
---
## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [Required TodoWrite Items](#required-todowrite-items)
- [Workflow](#workflow)
- [Step 1: Map Context (`makefile-review:context-mapped`)](#step-1:-map-context-(makefile-review:context-mapped))
- [Step 2: Dependency Graph (`makefile-review:dependency-graph`)](#step-2:-dependency-graph-(makefile-review:dependency-graph))
- [Step 3: Deduplication Audit (`makefile-review:dedup-candidates`)](#step-3:-deduplication-audit-(makefile-review:dedup-candidates))
- [Step 4: Portability Check (`makefile-review:tooling-alignment`)](#step-4:-portability-check-(makefile-review:tooling-alignment))
- [Step 5: Evidence Log (`makefile-review:evidence-logged`)](#step-5:-evidence-log-(makefile-review:evidence-logged))
- [Progressive Loading](#progressive-loading)
- [Output Format](#output-format)
- [Summary](#summary)
- [Testing](#testing)

## Testing

Run `pytest plugins/pensive/tests/skills/test_makefile_review.py` to verify review logic.

# Makefile Review Workflow

Audit Makefiles for best practices, deduplication, and portability.

## Quick Start

```bash
/makefile-review
```

## When To Use

- Makefile changes or additions
- Build system optimization
- Portability improvements
- CI/CD pipeline updates
- Developer experience improvements

## When NOT To Use

- Creating new Makefiles - use abstract:make-dogfood
- Architecture review - use architecture-review

## Required TodoWrite Items

1. `makefile-review:context-mapped`
2. `makefile-review:dependency-graph`
3. `makefile-review:dedup-candidates`
4. `makefile-review:tooling-alignment`
5. `makefile-review:evidence-logged`
6. `makefile-review:findings-verified`

## Workflow

### Step 1: Map Context (`makefile-review:context-mapped`)

Confirm baseline:
```bash
pwd && git status -sb && git diff --stat
```
**Verification:** Run `git status` to confirm working tree state.

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

Use `imbue:proof-of-work` to record command outputs with file:line references.

Summarize findings:
- Severity (critical, major, minor)
- Expected impact
- Suggested refactors
- Owners and dates for follow-ups

## Progressive Loading

Load additional context as needed:

**Best Practices & Examples**: `@include modules/best-practices.md`

**Plugin Dogfood Checks**: `@include modules/plugin-dogfood-checks.md` - Makefile completeness analysis, target generation, and dogfooding validation.

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
- Anchor: `verbatim source text at file:line`
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

## Verify Findings Are Grounded (`makefile-review:findings-verified`)

Write findings to `.review/findings.json` and run the citation verifier
as `Skill(imbue:review-core)` Step 5 describes. Only findings the
verifier passes enter the report. Drop or label `UNVERIFIED` the rest.

## Exit Criteria

- Context mapped
- Dependencies analyzed
- Deduplication reviewed
- Portability checked
- Evidence logged
- Every reported finding carries a `Location` + verbatim `Anchor` confirmed
  by `citation_verifier.py` (exit `0`), or unverified findings were dropped
  or labeled `UNVERIFIED`
## Troubleshooting

### Common Issues

**No Makefile found**
Ensure `Makefile` or `*.mk` files exist in the project root or specify paths explicitly.

**Include directives not resolved**
Run `rg -n "^include" -g'Makefile*'` to trace include chains manually.
