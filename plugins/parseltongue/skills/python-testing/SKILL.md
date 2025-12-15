---
name: python-testing
description: Python testing with pytest, fixtures, mocking, and TDD workflows. Use when writing unit tests, setting up test suites, or implementing test-driven development.
category: testing
tags: [python, testing, pytest, tdd, test-automation, quality-assurance]
tools: [test-analyzer, coverage-reporter, test-runner]
usage_patterns:
  - testing-implementation
  - test-suite-setup
  - test-refactoring
  - ci-cd-integration
complexity: intermediate
estimated_tokens: 900
progressive_loading: true
modules:
  - unit-testing
  - fixtures-and-mocking
  - test-infrastructure
  - testing-workflows
  - test-quality
  - async-testing
---

# Python Testing Hub

Testing patterns for pytest, fixtures, mocking, and TDD.

## Quick Start

1. **Assess Testing Needs**: Identify required testing patterns
2. **Configure pytest**: Set up test infrastructure
3. **Implement Tests**: Apply patterns from modules
4. **Run Coverage**: Verify test quality

## When to Use

- Writing unit tests for Python code
- Setting up test suites and infrastructure
- Implementing test-driven development (TDD)
- Creating integration tests for APIs and services
- Mocking external dependencies and services
- Testing async code and concurrent operations

## Modules

This skill provides focused modules for different testing aspects:

### Core Testing
- **unit-testing** - Fundamental unit testing patterns with pytest including AAA pattern, basic test structure, and exception testing
- **fixtures-and-mocking** - Advanced pytest fixtures, parameterized tests, and mocking patterns for external dependencies
- **async-testing** - Testing asynchronous Python code with pytest-asyncio including async fixtures and concurrent operation testing

### Infrastructure & Workflow
- **test-infrastructure** - Project configuration for pytest including pyproject.toml setup, test directory structure, and coverage configuration
- **testing-workflows** - Running tests, CI/CD integration, and automated testing workflows

### Quality
- **test-quality** - Best practices, anti-patterns to avoid, and quality criteria for Python tests

## Progressive Loading

Load modules based on your needs:
- Start with `unit-testing` for fundamental patterns
- Add `fixtures-and-mocking` for advanced test setup
- Include `test-infrastructure` when setting up new projects
- Use `testing-workflows` for CI/CD integration
- Reference `test-quality` for best practices
- Apply `async-testing` for asynchronous code

## Exit Criteria

- [ ] Tests follow AAA pattern
- [ ] Coverage meets project threshold (≥80%)
- [ ] All tests independent and reproducible
- [ ] CI/CD integration configured
- [ ] Clear test naming and organization
- [ ] No anti-patterns present
- [ ] Fixtures used appropriately
- [ ] Mocking only at boundaries
