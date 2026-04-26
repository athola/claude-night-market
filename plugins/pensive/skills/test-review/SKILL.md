---
name: test-review
description: 'Evaluate test suites for coverage gaps and TDD/BDD compliance. Use when auditing tests before release or after a major feature.'
version: 1.9.0
alwaysApply: false
category: testing
tags:
- testing
- tdd
- bdd
- coverage
- quality
- fixtures
tools: []
usage_patterns:
- test-audit
- coverage-analysis
- quality-improvement
- gap-remediation
complexity: intermediate
model_hint: standard
estimated_tokens: 200
progressive_loading: true
dependencies:
- pensive:shared
- imbue:proof-of-work
modules:
- framework-detection
- coverage-analysis
- scenario-quality
- remediation-planning
- content-assertion-quality
---
## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [Required TodoWrite Items](#required-todowrite-items)
- [Progressive Loading](#progressive-loading)
- [Workflow](#workflow)
- [Step 1: Detect Languages (`test-review:languages-detected`)](#step-1:-detect-languages-(test-review:languages-detected))
- [Step 2: Inventory Coverage (`test-review:coverage-inventoried`)](#step-2:-inventory-coverage-(test-review:coverage-inventoried))
- [Step 3: Assess Scenario Quality (`test-review:scenario-quality`)](#step-3:-assess-scenario-quality-(test-review:scenario-quality))
- [Step 4: Plan Remediation (`test-review:gap-remediation`)](#step-4:-plan-remediation-(test-review:gap-remediation))
- [Step 5: Log Evidence (`test-review:evidence-logged`)](#step-5:-log-evidence-(test-review:evidence-logged))
- [Test Quality Checklist (Condensed)](#test-quality-checklist-(condensed))
- [Output Format](#output-format)
- [Summary](#summary)
- [Framework Detection](#framework-detection)
- [Coverage Analysis](#coverage-analysis)
- [Quality Issues](#quality-issues)
- [Remediation Plan](#remediation-plan)
- [Recommendation](#recommendation)
- [Integration Notes](#integration-notes)
- [Exit Criteria](#exit-criteria)


# Test Review Workflow

Evaluate and improve test suites with TDD/BDD rigor.

## Quick Start

```bash
/test-review
```
**Verification:** Run `pytest -v` to verify tests pass.

## When To Use

- Reviewing test suite quality
- Analyzing coverage gaps
- Before major releases
- After test failures
- Planning test improvements

## When NOT To Use

- Writing new tests - use parseltongue:python-testing
- Updating existing tests - use sanctum:test-updates

## Required TodoWrite Items

1. `test-review:languages-detected`
2. `test-review:coverage-inventoried`
3. `test-review:scenario-quality`
4. `test-review:invariant-preservation`
5. `test-review:gap-remediation`
6. `test-review:evidence-logged`

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
**Verification:** Run the command with `--help` flag to verify availability.

### Step 2: Inventory Coverage (`test-review:coverage-inventoried`)

Run coverage tools and identify gaps.
→ **See**: `modules/coverage-analysis.md`

Quick check:
```bash
git diff --name-only | rg 'tests|spec|feature'
```
**Verification:** Run `pytest -v` to verify tests pass.

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
→ **See**: `imbue:proof-of-work`

## Test Quality Checklist (Condensed)

- [ ] Clear test structure (Arrange-Act-Assert)
- [ ] Critical paths covered (auth, validation, errors)
- [ ] Specific assertions with context
- [ ] No flaky tests (dead waits, order dependencies)
- [ ] Reusable fixtures/factories
- [ ] Invariant-encoding tests intact (see below)

### Invariant-Encoding Tests

Tests do not just verify behavior — they encode design
invariants. A test that asserts "module A never imports
from module B" encodes a layer boundary. A test that
asserts "this function is pure" encodes a concurrency
model. These tests are load-bearing in ways that
coverage metrics cannot capture.

**During review, check:**

1. **Were invariant-encoding tests removed or weakened?**
   A test that enforced an architectural boundary,
   data structure constraint, or API contract should
   not be deleted without naming the invariant being
   abandoned and escalating to human judgment.

2. **Were test expectations changed to match a broken
   implementation?** If an assertion value changed, ask:
   did the *requirement* change, or did the agent change
   the test to make its code pass? The latter is the
   single most dangerous form of test tampering.

3. **Are new invariants encoded as tests?** When a design
   decision is made (choice of data structure, module
   boundary, error strategy), there should be at least
   one test whose failure would signal that the
   invariant was violated.

**Red flag patterns:**

| Pattern | Risk |
|---------|------|
| `@pytest.mark.skip` added to a passing test | Invariant being silently dropped |
| Assertion changed from specific to broad | Constraint being relaxed |
| Test renamed to describe new behavior | Old invariant erased from history |
| Test deleted "because it tested old code" | Invariant removed without replacement |

**When invariant erosion is detected:**

Do NOT approve. Flag as a BLOCKING quality issue and
present the three options to the human:

1. **Preserve**: Revert the test change, fix the
   implementation to satisfy the invariant
2. **Layer**: Keep the invariant test, add the new
   behavior alongside it (accepting inelegance)
3. **Revise**: The invariant is genuinely wrong — remove
   the old test AND write a new test encoding the
   replacement invariant

This is a judgment call that models get wrong far too
often. Default to option 1 (preserve) when no human is
available.

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
**Verification:** Run the command with `--help` flag to verify availability.

## Integration Notes

- Use `imbue:proof-of-work` for reproducible evidence capture
- Reference `imbue:diff-analysis` for risk assessment
- Format output using `imbue:structured-output` patterns

## Exit Criteria

- Frameworks detected and documented
- Coverage analyzed and gaps identified
- Scenario quality assessed
- Remediation plan created with owners and dates
- Evidence logged with citations
## Troubleshooting

### Common Issues

**Tests not discovered**
Ensure test files match pattern `test_*.py` or `*_test.py`. Run `pytest --collect-only` to verify.

**Import errors**
Check that the module being tested is in `PYTHONPATH` or install with `pip install -e .`

**Async tests failing**
Install pytest-asyncio and decorate test functions with `@pytest.mark.asyncio`
