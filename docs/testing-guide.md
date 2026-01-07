# Testing Guide

Guide to testing in the Claude Night Market ecosystem, covering pre-commit testing, test development, and troubleshooting.

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

The project uses automated testing at multiple levels:

1. **Pre-commit hooks**: Run tests for changed plugins before allowing commits.
2. **Manual execution**: Run tests on-demand for development.
3. **CI/CD pipelines**: Test in continuous integration.

Tests are enforced by pre-commit hooks, preventing broken code from entering the repository.

## Pre-Commit Testing

Pre-commit hooks automatically run all tests for changed plugins before allowing commits. This prevents broken code from entering the repository and provides fast feedback by only testing changed plugins.

### Workflow

When all tests pass:

```bash
$ git add plugins/minister/src/minister/tracker.py
$ git commit -m "feat: improve tracker logic"

# Pre-commit runs automatically:
Run Tests for Changed Plugins...........................................Passed
[code-cleanup-1.2.1 abc1234] feat: improve tracker logic
 1 file changed, 10 insertions(+), 5 deletions(-)
```

When tests fail:

```bash
$ git add plugins/minister/src/minister/tracker.py
$ git commit -m "feat: improve tracker logic"

# Pre-commit runs automatically:
Run Tests for Changed Plugins...........................................Failed
- hook id: run-plugin-tests
- exit code: 1

Testing minister...
  x Tests failed

=== Test Summary ===
x Failed (1): minister
ERROR: Some tests failed!

# Commit is BLOCKED - fix tests first!
```

### Trigger Rules

| Trigger | Tests Run | Speed |
|---------|-----------|-------|
| Modify `plugins/minister/*.py` | Only minister tests | ~3-5s |
| Modify `plugins/minister/*.py` + `plugins/imbue/*.py` | Minister + imbue tests | ~8-12s |
| Modify `plugins/*/commands/*.md` | Tests for affected plugins | ~5-10s |
| Manual: `make test` | ALL plugin tests | ~2-3min |

### Configuration

Defined in `.pre-commit-config.yaml`:

```yaml
- id: run-plugin-tests
  name: Run Tests for Changed Plugins
  entry: ./scripts/run-plugin-tests.sh --changed
  language: system
  pass_filenames: false
  stages: [pre-commit]
  files: ^plugins/.*\.(py|md)$
```

The hook triggers on `.py` and `.md` file changes in plugins, runs automatically before every commit, blocks commits if any tests fail, and provides output showing which tests failed.

## Test Coverage

### Plugins with Test Coverage

Current plugins with automated tests:

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

For each modified plugin, the hook:

1. **First checks** for \`Makefile\` with \`test:\` target
   \`\`\`bash
   cd plugins/<plugin> && make test
   \`\`\`

2. **Falls back** to \`pyproject.toml\` with pytest
   \`\`\`bash
   cd plugins/<plugin> && uv run python -m pytest tests/
   \`\`\`

3. **Skips** plugins without test configuration

## Writing Tests

### Test Structure

\`\`\`
plugins/<plugin>/
├── src/
│   └── <plugin>/
│       └── module.py
└── tests/
    ├── unit/           # Unit tests (isolated)
    ├── integration/    # Integration tests (plugin-level)
    ├── bdd/            # BDD scenarios
    └── conftest.py     # Shared fixtures
\`\`\`

### Test Patterns

#### 1. Unit Tests

\`\`\`python
# tests/unit/test_tracker.py
import pytest
from minister.project_tracker import ProjectTracker

def test_create_initiative():
    """Test creating a new initiative."""
    tracker = ProjectTracker()
    initiative = tracker.create_initiative(
        name="Test Initiative",
        description="Test description"
    )
    assert initiative["name"] == "Test Initiative"
    assert initiative["status"] == "active"
\`\`\`

#### 2. Integration Tests

\`\`\`python
# tests/integration/test_cli.py
from click.testing import CliRunner
from minister.cli import cli

def test_cli_status_command():
    """Test the status command end-to-end."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Active Initiatives:" in result.output
\`\`\`

#### 3. BDD Tests

\`\`\`python
# tests/bdd/test_scenarios.py
import pytest

def test_scenario_create_and_complete_initiative():
    """
    Given a new project tracker
    When I create an initiative and mark it complete
    Then the initiative status should be 'completed'
    """
    # Given
    tracker = ProjectTracker()

    # When
    initiative = tracker.create_initiative("Test", "Description")
    tracker.complete_initiative(initiative["id"])

    # Then
    status = tracker.get_initiative_status(initiative["id"])
    assert status == "completed"
\`\`\`

### Test Configuration

#### pyproject.toml

\`\`\`toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-v",                    # Verbose output
    "--strict-markers",      # Strict marker enforcement
    "--cov=src",             # Coverage for src/
    "--cov-report=term",     # Terminal coverage report
    "--cov-report=html",     # HTML coverage report
]

markers = [
    "slow: marks tests as slow (deselect with '-m \\"not slow\\"')",
    "integration: marks tests as integration tests",
]
\`\`\`

#### Makefile

\`\`\`makefile
.PHONY: test test-unit test-integration test-coverage

test:
	uv run python -m pytest tests/ -v

test-unit:
	uv run python -m pytest tests/unit/ -v

test-integration:
	uv run python -m pytest tests/integration/ -v

test-coverage:
	uv run python -m pytest tests/ --cov=src --cov-report=html
\`\`\`

## Running Tests

### Pre-Commit (Automatic)

Tests run automatically on commit:

\`\`\`bash
git add plugins/minister/src/minister/tracker.py
git commit -m "feat: improve tracker"
# Tests run automatically
\`\`\`

### Manual Execution

#### Test Runner Script

\`\`\`bash
# Test only changed plugins (based on staged files)
./scripts/run-plugin-tests.sh --changed

# Test all plugins
./scripts/run-plugin-tests.sh --all

# Test specific plugins
./scripts/run-plugin-tests.sh minister imbue sanctum
\`\`\`

#### Direct pytest

\`\`\`bash
# Test a specific plugin
cd plugins/minister
uv run python -m pytest tests/ -v

# Test a specific file
uv run python -m pytest tests/unit/test_tracker.py -v

# Test a specific test
uv run python -m pytest tests/unit/test_tracker.py::test_create_initiative -v

# Run with coverage
uv run python -m pytest tests/ --cov=src --cov-report=term
\`\`\`

#### Using Make

\`\`\`bash
cd plugins/minister
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-coverage     # Run with coverage report
\`\`\`

### Performance

#### Typical Timings

- **Single plugin (minister)**: ~5-10 seconds
- **Two plugins**: ~10-20 seconds
- **All plugins**: ~2-3 minutes

#### Optimization

Hooks are optimized for developer workflow:

- **Only tests changed plugins** (not entire codebase)
- **Runs in parallel** when multiple plugins changed
- **Uses quiet mode** for less verbose output
- **Caches test dependencies** via uv

## Troubleshooting

### Common Test Failures

See [Quality Gates - Troubleshooting](./quality-gates.md#troubleshooting) for troubleshooting guide.

### When Tests Fail

1. **Review the test output** - Pre-commit shows test failures
2. **Fix the failing tests** or the code causing failures
3. **Re-run tests manually** to verify:
   \`\`\`bash
   cd plugins/<plugin>
   uv run python -m pytest tests/ -v
   \`\`\`
4. **Stage your fixes** and commit again

## Best Practices

### For Test Development

1. **Follow TDD (Test-Driven Development)**
   - Write test first → Watch it fail → Write minimal code → Refactor

2. **Use descriptive test names**
   - Good: \`test_create_initiative_with_valid_data_succeeds\`
   - Bad: \`test1\`

3. **Test one thing per test**
   - One assertion per test (where reasonable)
   - Clear failure messages

4. **Use fixtures for common setup**
   - Define in \`conftest.py\`
   - Reuse across tests

5. **Keep tests fast**
   - Mock external dependencies
   - Tag slow tests: \`@pytest.mark.slow\`

### For Plugin Maintainers

1. **Maintain high coverage** (85%+ target)
2. **Keep tests isolated** (no shared state)
3. **Document test requirements**
4. **Review test failures promptly**

### For Daily Development

1. **Run tests before committing**
2. **Fix tests incrementally**
3. **Never skip tests** (avoid \`--no-verify\`)

## CI/CD Integration

See [Quality Gates - CI/CD Integration](./quality-gates.md#cicd-integration) for details on how testing integrates with continuous integration.

## Skipping Tests (Emergency Only)

\`\`\`bash
# Skip all hooks (DANGEROUS)
git commit --no-verify -m "emergency fix"

# Skip tests only
SKIP=run-plugin-tests git commit -m "WIP: tests in progress"
\`\`\`

**⚠️ Use sparingly!** Only for true emergencies or WIP commits.

## See Also

- [Quality Gates](./quality-gates.md) - Complete quality system documentation
- [Plugin Development Guide](./plugin-development-guide.md) - Plugin development standards
- [Pre-commit configuration](../.pre-commit-config.yaml) - Hook definitions
- [Test Runner Script](../scripts/run-plugin-tests.sh) - Test execution script
