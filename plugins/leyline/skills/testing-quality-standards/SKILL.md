---
name: testing-quality-standards
description: |
  Shared testing quality metrics and standards for cross-plugin use. Referenced
  by pensive:test-review and parseltongue:python-testing.

  Triggers: testing standards, quality metrics, coverage thresholds, test quality,
  anti-patterns, testing best practices, quality gates

  Use when: evaluating test quality, setting coverage thresholds, identifying
  testing anti-patterns, establishing quality standards

  DO NOT use when: simple scripts without quality requirements.

  Consult this skill when establishing testing quality standards.
category: infrastructure
tags: [testing, quality, standards, metrics]
dependencies: []
estimated_tokens: 400
provides:
  patterns: [coverage-thresholds, quality-metrics, anti-patterns]
---

# Testing Quality Standards

Shared quality standards and metrics for testing across all plugins in the Claude Night Market ecosystem.

## Coverage Thresholds

| Level | Coverage | Use Case |
|-------|----------|----------|
| Minimum | 60% | Legacy code |
| Standard | 80% | Normal development |
| High | 90% | Critical systems |
| detailed | 95%+ | Safety-critical |

## Quality Metrics

### Structure
- [ ] Clear test organization
- [ ] Meaningful test names
- [ ] Proper setup/teardown
- [ ] Isolated test cases

### Coverage
- [ ] Critical paths covered
- [ ] Edge cases tested
- [ ] Error conditions handled
- [ ] Integration points verified

### Maintainability
- [ ] DRY test code
- [ ] Reusable fixtures
- [ ] Clear assertions
- [ ] Minimal mocking

### Reliability
- [ ] No flaky tests
- [ ] Deterministic execution
- [ ] No order dependencies
- [ ] Fast feedback loop

## Detailed Topics

For implementation patterns and examples:

- **[Anti-Patterns](modules/anti-patterns.md)** - Common testing mistakes with before/after examples
- **[Best Practices](modules/best-practices.md)** - Core testing principles and exit criteria

## Integration with Plugin Testing

This skill provides foundational standards referenced by:
- `pensive:test-review` - Uses coverage thresholds and quality metrics
- `parseltongue:python-testing` - Uses anti-patterns and best practices
- `sanctum:test-*` - Uses quality checklist for test validation

Reference in your skill's frontmatter:
```yaml
dependencies: [leyline:testing-quality-standards]
```
