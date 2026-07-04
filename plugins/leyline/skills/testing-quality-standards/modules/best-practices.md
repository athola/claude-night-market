---
name: best-practices
description: Testing best practices and principles
parent_skill: leyline:testing-quality-standards
category: infrastructure
estimated_tokens: 200
reusable_by: [pensive:test-review, parseltongue:python-testing]
---

# Testing Best Practices

## Core Principles

1. **Test behavior, not implementation** - Focus on what, not how
2. **One concept per test** - Keep tests focused
3. **Arrange-Act-Assert** - Consistent structure
4. **BDD language** - Given/When/Then for clarity
5. **Fast feedback** - Tests should run quickly

## Naming and Structure

6. **Descriptive names** - `test_user_creation_with_invalid_email_raises_error`
7. **Independent tests** - No shared state between tests
8. **Use fixtures** - Avoid setup duplication

## Boundaries and Coverage

9. **Mock at boundaries** - Only mock external dependencies
10. **Measure coverage** - Aim for meaningful, not just high

## Fake-Resistance

11. **Prefer properties over examples** - Where an invariant holds
    (round-trip, idempotence, ordering, conservation, non-negativity),
    assert the property and fuzz inputs instead of pinning a few
    hand-picked cases. Property-based tests cover cases you did not
    enumerate and resist the "passes but does not test" failure.
12. **Prove the test can fail** - A test that stays green when the
    behavior breaks is not evidence. Break the behavior on purpose
    (revert/mutation) and confirm the test goes red. See
    `Skill(imbue:proof-of-work)` module `verifier-integrity.md`.

## Exit Criteria

- Coverage thresholds documented and understood
- Quality metrics defined and measurable
- Anti-patterns identified and avoided
- Best practices applied consistently
