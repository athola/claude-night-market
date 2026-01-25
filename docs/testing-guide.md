# Testing Guide

This guide covers testing in the Claude Night Market ecosystem, including pre-commit testing, test development, and troubleshooting.

## Table of Contents

- [Overview](#overview)
- [Pre-Commit Testing](#pre-commit-testing)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Advanced Testing](#advanced-testing)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Overview

We test at three levels:
1. **Pre-commit hooks** run tests for changed plugins before allowing commits.
2. **Manual execution** allows for on-demand testing during development.
3. **CI/CD pipelines** verify code in continuous integration.

## Pre-Commit Testing

Pre-commit hooks automatically run all tests for changed plugins before allowing commits. This prevents broken code from entering the repository and provides fast feedback by limiting the scope to changes.

### Workflow

When you commit changes, pre-commit runs automatically. If tests pass, the commit succeeds. If they fail, the commit is blocked, and you'll see a summary of the failures.

### Trigger Rules

The system runs tests based on modified files. Modifying a plugin's Python files triggers that plugin's tests. Modifying multiple plugins triggers tests for all of them. Changes to command markdown files also trigger relevant tests. You can manually run all tests with `make test`.

### Configuration

The hook is defined in `.pre-commit-config.yaml`. It triggers on `.py` and `.md` file changes in plugins, runs automatically before every commit, and blocks commits if any tests fail.

## Test Coverage

### Plugins with Test Coverage

We maintain automated tests for the following plugins:

| Plugin | Test Framework | Test Count | Coverage | Advanced |
|--------|---------------|------------|----------|----------|
| **abstract** | pytest | 331 tests | 68% | mutation |
| **minister** | pytest | 145 tests | 98% | mutation |
| **spec-kit** | pytest | 184 tests | 90%+ | - |
| **sanctum** | pytest | 60+ tests | 85%+ | - |
| **scry** | pytest | 53+ tests | 80%+ | integration |
| **pensive** | pytest | ~45 tests | 85%+ | - |
| **imbue** | pytest | ~40 tests | 80%+ | mutation |
| **parseltongue** | pytest | ~25 tests | 75%+ | - |
| **conserve** | pytest | ~20 tests | 80%+ | mutation, bench |
| **conjure** | pytest | ~15 tests | 75%+ | mutation, bench |
| **memory-palace** | pytest | ~10 tests | 70%+ | mutation, bench |
| **leyline** | pytest | ~10 tests | 75%+ | mutation, bench |

**Total**: ~938+ tests across 12 plugins

**Advanced Testing:**
- **mutation**: Mutation testing with mutmut
- **bench**: Performance benchmarking
- **integration**: End-to-end workflow tests

### Test Discovery

For each modified plugin, the hook first looks for a `Makefile` with a `test:` target. If not found, it defaults to running `pytest` directly via `pyproject.toml`. If neither is configured, it skips the plugin.

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

Run `pytest` directly:
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

Test execution time depends on the scope. Testing a single plugin like `minister` takes 5-10 seconds. Full suite runs take two to three minutes. The hooks optimize for speed by testing only changed plugins, running in parallel, and using quiet mode.

### Output Verbosity

The test runner uses **conditional verbosity** to balance clean output with debugging needs:

- **On success**: Shows brief `✓ Tests passed` message with quiet output
- **On failure**: Automatically re-runs with full verbose output for debugging

This means you get error details immediately without manually re-running failed tests:

```bash
$ ./scripts/run-plugin-tests.sh broken-plugin
Testing broken-plugin...
  ✗ Tests failed
Re-running with verbose output:
[Full pytest output with error details]
```

## Advanced Testing

Beyond standard unit/integration tests, several plugins support advanced testing methodologies.

### Mutation Testing

**Purpose**: Verify test quality by mutating code and checking if tests catch changes.

**Available in**: abstract, conserve, imbue, leyline, memory-palace, minister, conjure

**Usage**:
```bash
cd plugins/abstract
make mutation-test
```

**Requirements**: Install `mutmut` via `pip install mutmut`. Gracefully skips if not installed.

**How it works**: Mutmut modifies your source code (e.g., changes `>` to `<`, flips boolean values) and re-runs tests. If tests still pass with mutated code, your tests may not be thorough enough.

### Performance Benchmarking

**Purpose**: Track performance regression for critical operations.

**Available in**: conjure (API latency), memory-palace (memory operations), leyline (token estimation), conserve (bloat detection)

**Usage**:
```bash
cd plugins/conjure
make benchmark
```

**Requirements**: Install `pytest-benchmark` via `pip install pytest-benchmark`. Gracefully skips if not installed.

**Output**: Shows execution time statistics sorted by mean duration.

### Memory Profiling

**Purpose**: Identify memory usage patterns and potential leaks.

**Available in**: conjure, memory-palace, leyline, conserve

**Usage**:
```bash
cd plugins/memory-palace
make memory-profile
```

**Requirements**: Install `memory_profiler` via `pip install memory_profiler`.

**Note**: Currently shows placeholder message. Configure by creating profiling scripts in `tests/performance/`.

### Integration Testing

**Purpose**: Test complete workflows end-to-end with external dependencies.

**Example**: `scry` plugin tests VHS→ffmpeg→GIF workflow

**Usage**:
```bash
cd plugins/scry
pytest tests/test_workflow_integration.py -v
```

**Markers**: Tests use `@pytest.mark.requires_vhs` and `@pytest.mark.requires_ffmpeg` to skip gracefully when dependencies unavailable.

## Troubleshooting

### Common Test Failures

If tests fail, review the output provided by the pre-commit hook. Fix the code or the test, then re-run manually to verify before attempting to commit again.

### Iron Law TDD Enforcement

We follow a strict rule: **No implementation without a failing test first.**

This prevents writing code based on assumptions. Before implementing a feature, write a test that fails to prove the need for the code and guide its design.

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
