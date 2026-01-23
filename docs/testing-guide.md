# Testing Guide

This guide covers testing in the Claude Night Market ecosystem, including pre-commit testing, test development, and troubleshooting.

## Table of Contents

- [Overview](#overview)
- [Pre-Commit Testing](#pre-commit-testing)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Overview

We test at three levels:
1. **Pre-commit hooks** run tests for changed plugins before allowing commits.
2. **Manual execution** allows for on-demand testing during development.
3. **CI/CD pipelines** verify code in continuous integration.

## Pre-Commit Testing

Pre-commit hooks automatically run all tests for changed plugins before allowing commits. This prevents broken code from entering the repository and provides fast feedback by limiting the scope to what changed.

### Workflow

When you commit changes, pre-commit runs automatically. If tests pass, the commit succeeds. If they fail, the commit is blocked, and you'll see a summary of the failures.

### Trigger Rules

The system decides which tests to run based on the files you modify. Modifying a plugin's Python files triggers that plugin's tests. Modifying multiple plugins triggers tests for all of them. Changes to command markdown files also trigger relevant tests. You can manually run all tests with `make test`.

### Configuration

The hook is defined in `.pre-commit-config.yaml`. It triggers on `.py` and `.md` file changes in plugins, runs automatically before every commit, and blocks commits if any tests fail.

## Test Coverage

### Plugins with Test Coverage

We maintain automated tests for the following plugins:

| Plugin | Test Framework | Test Count | Coverage |
|--------|---------------|------------|----------|
| **minister** | pytest | 145 tests | 98% |
| **spec-kit** | pytest | 184 tests | 90%+ |
| **pensive** | pytest | ~45 tests | 85%+ |
| **imbue** | pytest | ~40 tests | 80%+ |
| **sanctum** | pytest | ~35 tests | 85%+ |
| **abstract** | pytest | ~30 tests | 80%+ |
| **parseltongue** | pytest | ~25 tests | 75%+ |
| **conserve** | pytest | ~20 tests | 80%+ |
| **conjure** | pytest | ~15 tests | 75%+ |
| **memory-palace** | pytest | ~10 tests | 70%+ |

**Total**: ~550+ tests across 10 plugins

### Test Discovery

For each modified plugin, the hook first looks for a `Makefile` with a `test:` target. If not found, it falls back to running `pytest` directly via `pyproject.toml`. If neither is configured, it skips the plugin.

## Writing Tests

### Test Structure

Organize tests within the plugin directory:
```
plugins/<plugin>/
├── src/
│   └── <plugin>/
│       └── module.py
└── tests/
    ├── unit/           # Unit tests (isolated)
    ├── integration/    # Integration tests (plugin-level)
    ├── bdd/            # BDD scenarios
    └── conftest.py     # Shared fixtures
```

### Test Patterns

**Unit Tests**
Isolate logic to test specific functions or classes. For example, `test_create_initiative` should verify that a `ProjectTracker` correctly instantiates an initiative.

**Integration Tests**
Test the plugin end-to-end. `test_cli_status_command` might invoke the CLI runner to check the status command's output and exit code.

**BDD Tests**
Describe scenarios in a Given-When-Then format. These help verify user-facing behavior.

### Test Configuration

Configure `pytest` in `pyproject.toml` to set test paths, verbosity, and coverage options. Use `conftest.py` for shared fixtures.

## Running Tests

### Pre-Commit (Automatic)

Tests run automatically when you commit. Just `git add` and `git commit` as usual.

### Manual Execution

You can run tests manually using the runner script, `pytest`, or `make`.

```bash
# Test only changed plugins (based on staged files)
./scripts/run-plugin-tests.sh --changed

# Test all plugins
./scripts/run-plugin-tests.sh --all

# Test specific plugins
./scripts/run-plugin-tests.sh minister imbue sanctum
```

To run `pytest` directly:
```bash
cd plugins/minister
uv run python -m pytest tests/ -v
```

Using `make`:
```bash
cd plugins/minister
make test
```

### Performance

Test execution time depends on the scope. Testing a single plugin like `minister` takes 5-10 seconds. Full suite runs take 2-3 minutes. The hooks optimize for speed by testing only changed plugins, running in parallel, and using quiet mode.

## Troubleshooting

### Common Test Failures

If tests fail, review the output provided by the pre-commit hook. Fix the code or the test, then re-run manually to verify before attempting to commit again.

### Iron Law TDD Enforcement

We follow a strict rule: **No implementation without a failing test first.**

This prevents writing code based on assumptions. Before implementing a feature, write a test that fails. This proves the need for the code and guides its design.

**Self-Check Protocol**
If you catch yourself planning implementation before writing a test, stop. Write the failing test first. If you think you know what tests you need, document the failure before designing the solution.

**Enforcement Mechanisms**
We use SessionStart hooks to remind developers of this rule. The `proof-of-work` skill and `iron-law-enforcement.md` module provide further details and verification.

## Best Practices

**For Test Development**
Follow TDD: Write a test, watch it fail, write code to pass, then refactor. Use descriptive test names like `test_create_initiative_with_valid_data_succeeds`. Test one thing per test and use fixtures for setup. Keep tests fast by mocking external dependencies.

**For Plugin Maintainers**
Aim for 85% coverage. Keep tests isolated—avoid shared state. Document requirements and review failures promptly. Ensure all scripts in `scripts/` have corresponding tests.

**For Daily Development**
Run tests before committing. Fix tests incrementally. Never skip tests with `--no-verify` unless it is a dire emergency.

## CI/CD Integration

Testing integrates with our continuous integration pipelines. See [Quality Gates - CI/CD Integration](./quality-gates.md#cicd-integration) for details.

## Skipping Tests (Emergency Only)

In rare emergencies, you can skip tests. Use `SKIP=run-plugin-tests git commit -m "WIP: tests in progress"` or `git commit --no-verify`. Use this sparingly.

## See Also

- [Quality Gates](./quality-gates.md) - Complete quality system documentation
- [Plugin Development Guide](./plugin-development-guide.md) - Plugin development standards
- [Pre-commit configuration](../.pre-commit-config.yaml) - Hook definitions
- [Test Runner Script](../scripts/run-plugin-tests.sh) - Test execution script
