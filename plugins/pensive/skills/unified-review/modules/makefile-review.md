# Makefile Review

Audit Makefiles for best practices, deduplication, and portability. Load
this module from `Skill(pensive:unified-review)` when Makefiles are in
scope, or run it alone with `/makefile-review` or `/full-review makefile`.

Run `pytest plugins/pensive/tests/unit/skills/test_makefile_review.py`
to validate the module contract.

## When To Use

- Makefile changes or additions
- Build system optimization
- Portability improvements
- CI/CD pipeline updates
- Developer experience improvements

## When NOT To Use

- Creating new Makefiles - use abstract:make-dogfood
- Architecture review - use architecture-review

## Required Progress Items

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

@include modules/makefile-dependency-graph.md

### Step 3: Deduplication Audit (`makefile-review:dedup-candidates`)

@include modules/makefile-deduplication-patterns.md

### Step 4: Portability Check (`makefile-review:tooling-alignment`)

@include modules/makefile-portability-checks.md

### Step 5: Evidence Log (`makefile-review:evidence-logged`)

Use `imbue:proof-of-work` to record command outputs with file:line references.

Summarize findings:
- Severity (critical, major, minor)
- Expected impact
- Suggested refactors
- Owners and dates for follow-ups

## Progressive Loading

Load additional context as needed:

**Best Practices & Examples**: `@include modules/makefile-best-practices.md`

**Plugin Dogfood Checks**: `@include modules/makefile-plugin-dogfood-checks.md`
covers Makefile completeness analysis, target generation, and dogfooding
validation.

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

Write findings to `.review/findings.json`, run the citation verifier
(`Skill(imbue:review-core)` Step 5), and drop or label `UNVERIFIED` any
the verifier rejects.

## Exit Criteria

- [ ] Context mapped
- [ ] Dependencies analyzed
- [ ] Deduplication reviewed
- [ ] Portability checked
- [ ] Evidence logged
- [ ] Every reported finding carries a `Location` + verbatim `Anchor` confirmed
  by `citation_verifier.py` (exit `0`), or unverified findings were dropped
  or labeled `UNVERIFIED`

## Troubleshooting

**No Makefile found**: ensure `Makefile` or `*.mk` files exist in the
project root, or specify paths explicitly.

**Include directives not resolved**: run `rg -n "^include" -g'Makefile*'`
to trace include chains by hand.
