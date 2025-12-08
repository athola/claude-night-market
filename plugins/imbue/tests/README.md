# Imbue Plugin Test Suite

This directory contains comprehensive tests for the imbue plugin, following TDD/BDD principles and mirroring the testing patterns from the abstract plugin.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and test configuration
├── README.md                            # This file - test documentation
├── unit/                                # Unit tests for individual components
│   ├── test_imbue_validator.py          # Core validation logic tests
│   ├── skills/                          # Skill-specific unit tests
│   │   ├── test_review_core.py          # Review workflow scaffolding
│   │   ├── test_evidence_logging.py     # Evidence capture patterns
│   │   ├── test_diff_analysis.py        # Change categorization
│   │   ├── test_catchup.py              # Git repository catchup
│   │   └── test_structured_output.py    # Deliverable formatting
│   ├── commands/                        # Command-specific tests
│   │   ├── test_review_command.py       # /review command
│   │   └── test_catchup_command.py      # /catchup command
│   └── agents/                          # Agent-specific tests
│       └── test_review_analyst.py       # Autonomous review agent
├── integration/                         # Workflow integration tests
│   ├── test_review_workflow_integration.py  # End-to-end review process
│   ├── test_evidence_chain_integration.py  # Evidence logging continuity
│   └── test_command_skill_integration.py   # Command-skill orchestration
├── fixtures/                            # Test data and mocks
│   ├── sample_skills/                   # Skill file samples
│   ├── git_repositories/                # Mock git repos
│   ├── evidence_logs/                   # Sample evidence data
│   └── expected_outputs/                # Expected test results
└── performance/                         # Performance benchmarks
    ├── test_validator_performance.py    # Validation tool performance
    └── test_workflow_scalability.py     # Large review handling
```

## Running Tests

### Prerequisites

Make sure you have the development dependencies installed:

```bash
cd plugins/imbue
uv sync
```

### Quick Test Run

Run all tests with basic output:

```bash
make test
# or
uv run pytest tests/ -v
```

### Running Specific Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/ -v -m unit

# Integration tests only
uv run pytest tests/integration/ -v -m integration

# Performance tests only
uv run pytest tests/performance/ -v -m performance

# BDD-style tests only
uv run pytest tests/ -v -m bdd
```

### Running with Coverage

```bash
# Generate coverage report
uv run pytest tests/ --cov=scripts --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=scripts --cov-report=html

# Full coverage with all reporting formats
uv run pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html --cov-report=xml
```

### Running Specific Test Files

```bash
# Test specific validator
uv run pytest tests/unit/test_imbue_validator.py -v

# Test specific skill
uv run pytest tests/unit/skills/test_review_core.py -v

# Test specific integration
uv run pytest tests/integration/test_review_workflow_integration.py -v
```

## Test Philosophy

### Test-Driven Development (TDD)

We follow the TDD cycle:

1. **Red**: Write a failing test that defines the desired behavior
2. **Green**: Write the minimal code to make the test pass
3. **Refactor**: Clean up the implementation while maintaining test coverage

### Behavior-Driven Development (BDD)

Tests are written in a BDD style that describes behavior:

```python
class TestFeatureName:
    """
    Feature: [Clear feature description]

    As a [stakeholder]
    I want [feature capability]
    So that [benefit/value]
    """

    def test_scenario_with_clear_outcome(self):
        """
        Scenario: [Clear scenario description]
        Given [initial context]
        When [action occurs]
        Then [expected outcome]
        """
```

### Test Categories

#### Unit Tests
- Test individual functions, classes, and methods in isolation
- Mock external dependencies
- Fast execution and focused scope
- Located in `tests/unit/`

#### Integration Tests
- Test interaction between components
- Verify workflow orchestration
- Test real file system and git operations
- Located in `tests/integration/`

#### Performance Tests
- Benchmark performance with large datasets
- Test memory usage and execution time
- Verify scalability constraints
- Located in `tests/performance/`

## Fixtures and Mocks

### Shared Fixtures

The `conftest.py` file provides comprehensive fixtures:

- `imbue_plugin_root` - Plugin root directory
- `sample_skill_content` - Valid skill file content
- `sample_plugin_json` - Valid plugin configuration
- `mock_git_repository` - Temporary git repository
- `sample_evidence_log` - Structured evidence data
- `mock_todo_write` - Mocked TodoWrite tool
- `mock_claude_tools` - Mocked Claude Code tools

### Mocking Strategy

#### External Dependencies
- **Git operations**: Controlled mock outputs for various git states
- **File system**: Use pytest's `tmp_path` for isolated environments
- **Claude Code API**: Mock all tool interactions
- **Network resources**: Mock web citations and external URLs

#### Test Data Management
- **Sample skills**: Structured markdown with valid frontmatter
- **Git repositories**: Controlled commit history and file states
- **Evidence logs**: Structured JSON with citation references
- **Expected outputs**: Deterministic results for validation

## Coverage Requirements

### Minimum Coverage Standards
- **Unit Tests**: 95% line coverage minimum
- **Integration Tests**: 100% workflow path coverage
- **Branch Coverage**: 90% minimum
- **Critical Business Logic**: 100% coverage required

### Coverage Reports

Coverage reports are generated in multiple formats:

1. **Terminal**: Summary with missing lines
2. **HTML**: Detailed interactive report (`htmlcov/index.html`)
3. **XML**: For CI/CD integration

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.performance   # Performance tests
@pytest.mark.slow          # Slow-running tests
@pytest.mark.bdd           # BDD-style tests
```

## Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """
    Feature: [Feature description]

    As a [stakeholder]
    I want [capability]
    So that [benefit]
    """

    @pytest.mark.unit
    def test_new_functionality_works(self, sample_fixture):
        """
        Scenario: [Scenario description]
        Given [context]
        When [action]
        Then [outcome]
        """
        # Arrange
        # Act
        # Assert
        pass
```

### Best Practices

1. **Descriptive Test Names**: Test names should clearly describe what's being tested
2. **AAA Pattern**: Structure tests with Arrange-Act-Assert
3. **Single Assertion**: Prefer one assertion per test when possible
4. **Test Independence**: Tests should not depend on each other
5. **Mock External Dependencies**: Use mocks for external services
6. **Use Fixtures**: Reuse fixtures for common test data
7. **Error Scenarios**: Test both success and failure cases
8. **Edge Cases**: Test boundary conditions and special cases

### Common Test Patterns

#### Testing with Mocks

```python
def test_function_with_external_dependency(self, mock_claude_tools):
    """Test function that uses Claude Code tools."""
    # Arrange
    mock_claude_tools['Read'].return_value = "expected content"

    # Act
    result = function_under_test()

    # Assert
    assert result == "expected result"
    mock_claude_tools['Read'].assert_called_once_with("expected_file")
```

#### Testing Git Operations

```python
def test_git_analysis(self, mock_git_repository):
    """Test git analysis functionality."""
    # Arrange - mock_git_repository provides a real git repo
    repo_path = mock_git_repository

    # Act
    result = analyze_git_repository(str(repo_path))

    # Assert
    assert result['status'] == 'clean'
    assert result['branch'] == 'main'
```

#### Testing Evidence Logging

```python
def test_evidence_capturing(self, sample_evidence_log):
    """Test evidence logging functionality."""
    # Arrange
    evidence_logger = EvidenceLogger()

    # Act
    evidence_logger.log_command("git status", "On branch main")

    # Assert
    assert len(evidence_logger.evidence) == 1
    assert evidence_logger.evidence[0]['command'] == "git status"
```

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Stop at first failure
uv run pytest tests/ -x -v

# Run with Python debugger
uv run pytest tests/ --pdb

# Run with verbose output and long traces
uv run pytest tests/ -v -s --tb=long
```

### Common Issues

1. **Import Errors**: Ensure `scripts/` directory is in Python path
2. **Fixture Not Found**: Check that fixtures are imported from `conftest.py`
3. **Mock Not Applied**: Use proper patch decorators and context managers
4. **Git Repository Issues**: Use `mock_git_repository` fixture for isolated git repos
5. **File Permission Issues**: Use `tmp_path` fixture for temporary files

## Continuous Integration

### GitHub Actions

Tests are configured to run on GitHub Actions with:

- Python 3.12 environment
- Dependency installation with `uv`
- Full test suite execution
- Coverage reporting
- Quality gates

### Quality Gates

Tests must pass:

- All tests execute without failures
- Coverage requirements met
- No linting errors
- Performance benchmarks within limits

## Performance Testing

### Benchmark Categories

1. **Validation Performance**: Large plugin validation
2. **Git Repository Analysis**: Large repository processing
3. **Evidence Log Management**: Large evidence dataset handling
4. **Memory Usage**: Memory consumption during operations

### Running Performance Tests

```bash
# Run all performance tests
uv run pytest tests/performance/ -v -m performance

# Run with timing information
uv run pytest tests/performance/ -v --durations=10
```

## Contributing

When adding new functionality:

1. **Write Tests First**: Follow TDD principles
2. **Use BDD Style**: Write descriptive test scenarios
3. **Cover All Cases**: Test success, failure, and edge cases
4. **Update Documentation**: Update this README if adding new test patterns
5. **Maintain Coverage**: Ensure coverage standards are met

## Troubleshooting

### Common Test Failures

1. **Missing Fixtures**: Import fixtures from `conftest.py`
2. **Mock Configuration**: Verify mock return values and call expectations
3. **File System Issues**: Use `tmp_path` for temporary files
4. **Git Repository State**: Use `mock_git_repository` for controlled git state

### Getting Help

- Check existing test patterns in similar test files
- Review abstract plugin tests for reference implementations
- Consult pytest documentation for advanced features
- Use `--pdb` flag to debug test failures interactively