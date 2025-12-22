---
name: test-review
description: |
  Evaluate and upgrade test suites with TDD/BDD rigor, coverage tracking,
  and quality assessment.

  Triggers: test audit, test coverage, test quality, TDD, BDD, test gaps,
  test improvement, coverage analysis, test remediation

  Use when: auditing test suites, analyzing coverage gaps, improving test
  quality, evaluating TDD/BDD compliance

  DO NOT use when: writing new tests - use parseltongue:python-testing.
  DO NOT use when: updating existing tests - use sanctum:test-updates.

  Use this skill for test suite evaluation and quality assessment.
category: testing
tags: [testing, tdd, bdd, coverage, quality, fixtures]
tools: [coverage-analyzer, scenario-evaluator, gap-finder]
usage_patterns:
  - test-audit
  - coverage-analysis
  - quality-improvement
  - gap-remediation
complexity: intermediate
estimated_tokens: 200
progressive_loading: true
dependencies: [pensive:shared, imbue:evidence-logging]
modules:
  - framework-detection
  - coverage-analysis
  - scenario-quality
  - remediation-planning
---

# Test Review Workflow

Evaluate and improve test suites with TDD/BDD rigor.

## Quick Start

```bash
/test-review
```

## When to Use

- Reviewing test suite quality
- Analyzing coverage gaps
- Before major releases
- After test failures
- Planning test improvements

## Required TodoWrite Items

1. `test-review:languages-detected`
2. `test-review:coverage-inventoried`
3. `test-review:scenario-quality`
4. `test-review:gap-remediation`
5. `test-review:evidence-logged`

## Progressive Loading

Load modules as needed based on review depth:

- **Basic review**: Core workflow (this file)
- **Framework detection**: Load `modules/framework-detection.md`
- **Coverage analysis**: Load `modules/coverage-analysis.md`
- **Quality assessment**: Load `modules/scenario-quality.md`
- **Remediation planning**: Load `modules/remediation-planning.md`

## Workflow

### Step 1: Detect Languages (`test-review:languages-detected`)

Identify testing frameworks and version constraints.
→ **See**: `modules/framework-detection.md`

Quick check:
```bash
find . -maxdepth 2 -name "Cargo.toml" -o -name "pyproject.toml" -o -name "package.json" -o -name "go.mod"
```

### Step 2: Inventory Coverage (`test-review:coverage-inventoried`)

Run coverage tools and identify gaps.
→ **See**: `modules/coverage-analysis.md`

Quick check:
```bash
git diff --name-only | rg 'tests|spec|feature'
```

### Step 3: Assess Scenario Quality (`test-review:scenario-quality`)

Evaluate test quality using BDD patterns and assertion checks.
→ **See**: `modules/scenario-quality.md`

Focus on:
- Given/When/Then clarity
- Assertion specificity
- Anti-patterns (dead waits, mocking internals, repeated boilerplate)

### Step 4: Plan Remediation (`test-review:gap-remediation`)

Create concrete improvement plan with owners and dates.
→ **See**: `modules/remediation-planning.md`

### Step 5: Log Evidence (`test-review:evidence-logged`)

Record executed commands, outputs, and recommendations.
→ **See**: `imbue:evidence-logging`

## Test Quality Checklist (Condensed)

- [ ] Clear test structure (Arrange-Act-Assert)
- [ ] Critical paths covered (auth, validation, errors)
- [ ] Specific assertions with context
- [ ] No flaky tests (dead waits, order dependencies)
- [ ] Reusable fixtures/factories

## Output Format

```markdown
## Summary
[Brief assessment]

## Framework Detection
- Languages: [list] | Frameworks: [list] | Versions: [constraints]

## Coverage Analysis
- Overall: X% | Critical: X% | Gaps: [list]

## Quality Issues
[Q1] [Issue] - Location - Fix

## Remediation Plan
1. [Action] - Owner - Date

## Recommendation
Approve / Approve with actions / Block
```

## Integration Notes

- Use `imbue:evidence-logging` for reproducible evidence capture
- Reference `imbue:diff-analysis` for risk assessment
- Format output using `imbue:structured-output` patterns

## Exit Criteria

- Frameworks detected and documented
- Coverage analyzed and gaps identified
- Scenario quality assessed
- Remediation plan created with owners and dates
- Evidence logged with citations
