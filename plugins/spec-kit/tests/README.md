# Spec-Kit Test Suite

Comprehensive test suite for the spec-kit plugin following TDD/BDD principles with excellent coverage of unit and integration tests.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── pytest.ini              # Pytest configuration
├── requirements.txt         # Test dependencies
├── Makefile                # Test automation commands
├── README.md               # This file
├── __init__.py
├── test_orchestrator.py    # Tests for speckit-orchestrator skill
├── test_spec_writing.py    # Tests for spec-writing skill
├── test_task_planning.py   # Tests for task-planning skill
├── test_commands.py        # Tests for speckit commands
├── test_agents.py          # Tests for speckit agents
├── test_integration.py     # Integration tests for workflows
└── test_frontmatter.py     # Tests for frontmatter validation
```

## Testing Philosophy

### TDD/BDD Principles
- **Test-Driven Development**: Tests are written before or alongside implementation
- **Behavior-Driven Development**: Tests focus on user behavior and business outcomes
- **Given-When-Then Pattern**: Clear test structure with context, action, and expectations
- **Descriptive Test Names**: Test names clearly indicate what is being tested

### Test Coverage Areas

#### Unit Tests
- **Individual Skills**: Testing each skill in isolation
- **Core Business Logic**: Validation rules, data transformations, calculations
- **Error Handling**: Edge cases, invalid inputs, failure scenarios
- **Dependencies**: Mock external dependencies for isolated testing

#### Integration Tests
- **Workflow End-to-End**: Complete speckit workflows from specification to implementation
- **Cross-Command Data Flow**: Data consistency between different commands
- **Artifact Consistency**: Validation that generated artifacts are consistent
- **Error Recovery**: Testing recovery from partial failures

#### Validation Tests
- **Frontmatter Validation**: Ensuring all skill files have valid frontmatter
- **Structure Validation**: Directory structure and file naming conventions
- **Content Quality**: Checking for required sections and proper formatting

## Running Tests

### Prerequisites
```bash
# Install test dependencies
make install

# Or manually
pip install -r requirements.txt
```

### Test Commands

```bash
# Run all tests
make test
# or
pytest

# Run unit tests only
make test-unit
# or
pytest -m "not integration"

# Run integration tests only
make test-integration
# or
pytest -m integration

# Run tests with coverage report
make test-coverage
# or
pytest --cov=../skills --cov=../commands --cov=../agents --cov-report=html

# Run tests in parallel
make test-parallel
# or
pytest -n auto

# Run tests with verbose output
make test-verbose
# or
pytest -v

# Run specific test file
make test-file FILE=test_spec_writing.py

# Run tests matching pattern
make test-match PATTERN=test_spec_creation
```

### Test Categories

#### Markers
Tests are marked with categories:
- `unit`: Unit tests for individual components
- `integration`: Integration tests for workflows
- `slow`: Tests that take longer to run
- `network`: Tests requiring network access

#### Running by Category
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Fixtures

### Core Fixtures

- `sample_spec_content`: Valid specification content for testing
- `sample_task_list`: Sample task breakdown for testing
- `temp_speckit_project`: Temporary speckit-enabled project structure
- `temp_skill_files`: Temporary skill files for testing
- `mock_git_repo`: Mock git repository with branches
- `sample_feature_description`: Natural language feature description
- `mock_agent_responses`: Mock responses from agents

### Usage Example
```python
def test_spec_creation(self, sample_feature_description):
    """Test creating specification from natural language."""
    # Use the fixture
    feature_desc = sample_feature_description

    # Test logic
    assert "user authentication" in feature_desc.lower()
```

## Writing New Tests

### Test Structure
```python
class TestNewFeature:
    """Test cases for new feature."""

    def test_descriptive_name(self, fixture1, fixture2):
        """Given context, when action, then expected result."""
        # Arrange (Given)
        setup_data = fixture1

        # Act (When)
        result = function_under_test(setup_data)

        # Assert (Then)
        assert result.success is True
        assert "expected" in result.message
```

### Best Practices

1. **Descriptive Names**: Test names should clearly indicate what is being tested
2. **AAA Pattern**: Arrange, Act, Assert structure
3. **One Assertion Per Test**: Focus on testing one behavior
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include tests for error conditions and edge cases
6. **Use Fixtures**: Reuse common test data and setup
7. **Independent Tests**: Tests should not depend on each other

## Coverage

### Target Coverage
- **Unit Tests**: 90%+ line coverage
- **Integration Tests**: 80%+ workflow coverage
- **Overall**: 85%+ combined coverage

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=../skills --cov=../commands --cov=../agents --cov-report=html

# View coverage in terminal
pytest --cov=../skills --cov=../commands --cov=../agents --cov-report=term-missing
```

### Coverage Exclusions
- Test files themselves
- Example/demonstration code
- Debug/development utilities
- Generated files

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Spec-Kit
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd plugins/spec-kit/tests
          make install
      - name: Run tests
        run: |
          cd plugins/spec-kit/tests
          make test-coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Running Tests with Debugger
```bash
# Run with pdb on failure
pytest --pdb

# Run specific test with pdb
pytest --pdb -k test_specific_name

# Use breakpoints in tests
import pdb; pdb.set_trace()
```

### Test Output
```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x
```

## Contributing

### Adding Tests
1. Write tests following the existing patterns
2. Use appropriate fixtures and markers
3. Ensure test coverage targets are met
4. Update documentation if needed

### Test Review Checklist
- [ ] Test name is descriptive
- [ ] Test follows AAA pattern
- [ ] Appropriate fixtures are used
- [ ] Test is independent
- [ ] Edge cases are covered
- [ ] Assertions are specific
- [ ] No external dependencies in unit tests

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure PYTHONPATH includes plugin directory
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

**Fixture Not Found**
```bash
# Check fixtures are defined in conftest.py
pytest --fixtures
```

**Coverage Not Working**
```bash
# Install coverage tools
pip install pytest-cov coverage
```

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review existing test patterns in the test suite
- Use `pytest --help` for available options
- Check plugin-specific requirements in plugin.json