# Conjure Plugin Tests

This directory contains detailed tests for the conjure plugin, following TDD/BDD principles and the patterns established in the abstract plugin.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini              # Pytest configuration
├── README.md               # This file
├── __init__.py
├── scripts/                # Tests for script modules
│   ├── __init__.py
│   ├── test_delegation_executor.py
│   ├── test_quota_tracker.py
│   └── test_usage_logger.py
├── test_hooks.py           # Tests for hook functionality
├── test_skills.py          # Tests for skill loading/execution
├── test_integration.py     # End-to-end integration tests
└── test_edge_cases.py      # Edge cases and error handling
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing

# Run specific test categories
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m "not network" # Skip network tests

# Run specific test file
uv run pytest tests/scripts/test_delegation_executor.py
```

## Test Philosophy

### TDD/BDD Approach

- **Given/When/Then** pattern for readable test scenarios
- **Behavior verification** over implementation details
- **Test doubles** for isolated unit testing
- **Integration tests** for end-to-end workflows

### Test Categories

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test component interactions and workflows
3. **Edge Case Tests**: Test error conditions, timeouts, and failures
4. **Performance Tests**: Test token estimation and quota tracking

### Coverage Requirements

- Minimum 85% code coverage
- All business logic paths tested
- Error handling scenarios covered
- Performance-critical paths verified

## Key Fixtures

- `temp_config_dir`: Temporary configuration directory
- `sample_config_file`: Sample service configuration
- `sample_usage_log`: Sample usage log entries
- `sample_files`: Test files for various file types
- `mock_subprocess_run`: Mocked subprocess execution
- `mock_tiktoken_encoder`: Mocked token encoder

## Test Data Management

Tests use temporary directories and files that are automatically cleaned up:
- Configuration files in temp directories
- Sample code and documentation files
- Mock usage logs with realistic data
- Hook scripts with test content
