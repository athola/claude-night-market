---
name: python-testing
description: |

Triggers: quality-assurance, test-automation, pytest, testing, python
  Python testing with pytest, fixtures, mocking, and TDD workflows.

  Triggers: pytest, unit tests, test fixtures, mocking, TDD, test suite, coverage,
  test-driven development, testing patterns, parameterized tests, unittest replacement,
  test coverage, pytest fixtures, async testing, test automation, pytest marks,
  test mocking, pytest plugins, integration tests, test discovery

  Use when: writing unit tests, setting up test suites, implementing TDD,
  configuring pytest, creating fixtures, async testing, writing integration tests,
  mocking dependencies, parameterizing tests, setting up CI/CD testing

  DO NOT use when: evaluating test quality - use pensive:test-review instead.
  DO NOT use when: infrastructure test config - use leyline:pytest-config.

  Consult this skill for Python testing implementation and patterns.
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
## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [Modules](#modules)
- [Core Testing](#core-testing)
- [Infrastructure & Workflow](#infrastructure-&-workflow)
- [Quality](#quality)
- [Progressive Loading](#progressive-loading)
- [Exit Criteria](#exit-criteria)


# Python Testing Hub

Testing patterns for pytest, fixtures, mocking, and TDD.

## Quick Start

1. **Install pytest and dependencies**:
   ```bash
   pip install pytest pytest-cov pytest-asyncio pytest-mock
   ```
   **Verification:** Run `pytest -v pytest-cov` to verify.

2. **Configure project** - Add to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   python_files = ["test_*.py"]
   addopts = "--cov=src --cov-report=html"
   ```
   **Verification:** Run `pytest -v` to verify tests pass.

3. **Create first test** - In `tests/test_example.py`:
   ```python
   def test_basic():
       assert 1 + 1 == 2
   ```
   **Verification:** Run `pytest -v` to verify tests pass.

4. **Run tests with coverage**:
   ```bash
   pytest --cov=src --cov-report=html
   ```
   **Verification:** Run `pytest -v --cov=src` to verify.

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

Load modules based on project requirements:
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
## Troubleshooting

### Common Issues

If tests are not discovered, verify that the test files follow the naming pattern `test_*.py` or `*_test.py`. You can run `pytest --collect-only` to confirm which tests are being identified by the runner. For import errors, confirm that the module under test is in your `PYTHONPATH` or install it in editable mode using `pip install -e .`. When async tests fail, verify that `pytest-asyncio` is installed and that the test functions are correctly decorated with `@pytest.mark.asyncio`.
