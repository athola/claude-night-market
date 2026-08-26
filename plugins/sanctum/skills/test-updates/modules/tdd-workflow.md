---
name: tdd-workflow
description: What TDD means for generated tests in this repository, deferring the cycle itself to superpowers
parent_skill: sanctum:test-updates
category: testing
estimated_tokens: 250
---

# TDD for Generated Tests

## The Cycle Lives Elsewhere

`Skill(superpowers:test-driven-development)` carries RED-GREEN-REFACTOR:
the phases, what each one forbids, and why watching the test fail is
not optional. This skill already declares it as a dependency, and this
module used to restate all of it in 140 lines.

That restatement is gone. A second copy of a general practice is not
free even when it agrees: it is a second thing to keep current, and
the two drift apart silently because nothing checks them against each
other. What follows is only what is true here and not there.

## Generated Tests Are Supposed to Fail

`sanctum:test-updates` writes tests before the code exists, so a run
that goes red immediately after generation is the tool working. Read
the failure before treating it as one.

| What you see | What it means |
|--------------|---------------|
| Assertion fails | Expected. This is RED |
| ImportError, SyntaxError, fixture error | A defect in the generated test. Fix it now |
| Passes on the first run | The behavior already existed, or the test asserts nothing |

The third row is the one that costs time later. A generated test that
passes before any implementation is usually asserting something
trivially true, and it will keep passing after the behavior breaks.

## Where the Local Conventions Are

- Docstring shape, GIVEN/WHEN/THEN: `modules/bdd-patterns.md`
- Assertion depth and coverage thresholds:
  `Skill(leyline:testing-quality-standards)`
- Fixtures, markers, and `conftest.py` layout:
  `Skill(leyline:pytest-config)`
- Whether a test is a real guard: `modules/quality-validation.md`

## Exit Criteria

- [ ] Every generated test failed once for a reason that names the
      missing behavior, not a missing import
- [ ] No generated test passed before its implementation existed
- [ ] The suite is green before the change is reported complete
