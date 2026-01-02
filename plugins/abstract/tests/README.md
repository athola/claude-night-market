# Test Suite for Abstract Project

This directory contains integration, performance, and unit test suites for validation and analysis scripts.

## Test Structure

```
tests/
├── unit/                              # Unit tests for individual tools
│   ├── test_skill_analyzer.py         # Tests for skill complexity analyzer
│   ├── test_module_validator.py       # Tests for modular structure validator
│   └── test_token_estimator.py        # Tests for token usage estimator
├── integration/                       # Integration tests for complete workflows
│   └── test_full_modular_workflow.py  # End-to-end workflow testing
├── performance/                       # Performance benchmarks and load tests
└── fixtures/                          # Test data and expected outputs
    ├── sample_skills/                 # Sample skill files for testing
    ├── expected_outputs/              # Expected tool outputs
    └── benchmark_data/                # Data for performance testing
```

## Running Tests

### Prerequisites

validate you have the required dependencies installed:

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Install project dependencies
cd "$(git rev-parse --show-toplevel)"  # Navigate to project root
pip install -e .
```

### Running All Tests

```bash
# Run all tests with coverage
cd "$(git rev-parse --show-toplevel)"  # Navigate to project root
python -m pytest tests/ -v --cov=skills --cov=tools

# Run tests with HTML coverage report
python -m pytest tests/ --cov=skills --cov=tools --cov-report=html

# Run tests with JUnit XML output (for CI/CD)
python -m pytest tests/ --junitxml=test-results.xml
```

### Running Specific Test Categories

```bash
# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run specific test file
python -m pytest tests/unit/test_skill_analyzer.py -v

# Run specific test
python -m pytest tests/unit/test_skill_analyzer.py::TestSkillAnalyzer::test_skill_analyzer_help -v
```

### Running Performance Tests

```bash
# Run with performance timing
python -m pytest tests/ --durations=0

# Run with memory profiling
python -m pytest tests/ --benchmark-only

# Run stress tests
python -m pytest tests/performance/ -v -k "stress"
```

## Test Categories

### Unit Tests

**test_skill_analyzer.py**
- Tests skill file analysis functionality
- Validates line count thresholds and recommendations
- Tests handling of various file formats and edge cases
- Validates command-line interface and argument parsing

**test_module_validator.py**
- Tests modular skill structure validation
- Validates hub-and-spoke patterns
- Tests dependency resolution and circular dependency detection
- Validates directory structure and module interactions

**test_token_estimator.py**
- Tests token usage estimation accuracy
- Validates different output formats (JSON, CSV, text)
- Tests handling of various content types (code, markdown, frontmatter)
- Validates dependency token counting

### Integration Tests

**test_full_modular_workflow.py**
- Tests complete workflow from monolithic to modular migration
- Validates end-to-end tool integration
- Tests progressive disclosure patterns
- Validates token efficiency improvements

## Test Fixtures and Data

### Sample Skills

The tests use dynamically generated sample skills that cover various scenarios:

- **Small skills**: Simple, focused content (50-100 tokens)
- **Large skills**: Complex, detailed content (1000+ tokens)
- **Modular structures**: Hub with multiple focused modules
- **Dependency chains**: Skills with inter-module dependencies
- **Invalid structures**: Edge cases and error conditions

### Expected Outputs

For consistency, tests use deterministic expected outputs:

- Tool analysis results
- Validation reports
- Token estimations
- Error messages

## Test Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --verbose
    --cov=skills
    --cov=tools
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests for individual components
    integration: Integration tests for workflows
    performance: Performance benchmarks and stress tests
    slow: Tests that take longer to run
    external: Tests requiring external services
```

### Environment Variables

```bash
# Test environment
export ABSTRACT_TEST_MODE=true
export ABSTRACT_TEST_DATA_DIR=/tmp/abstract_test_data
export ABSTRACT_VERBOSE_TESTS=false
```

## Coverage Requirements

### Target Coverage

- **Overall**: 85% minimum
- **Unit Tests**: 90% minimum
- **Integration Tests**: 80% minimum
- **Critical Paths**: 95% minimum

### Coverage Reports

```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=skills --cov=tools --cov-report=html

# Generate JSON coverage report
python -m pytest tests/ --cov=skills --cov=tools --cov-report=json

# View coverage in terminal
python -m pytest tests/ --cov=skills --cov=tools --cov-report=term-missing
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest pytest-cov pytest-mock

      - name: Run unit tests
        run: python -m pytest tests/unit/ -v --cov=skills --cov=tools

      - name: Run integration tests
        run: python -m pytest tests/integration/ -v

      - name: Generate coverage report
        run: python -m pytest tests/ --cov=skills --cov=tools --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Best Practices

### Writing Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern** (Arrange, Act, Assert)
3. **Test one behavior per test** for clarity and maintainability
4. **Use fixtures** for common test setup and teardown
5. **Mock external dependencies** to isolate the code under test

### Test Organization

1. **Group related tests** in classes
2. **Use markers** to categorize tests (unit, integration, performance)
3. **Create detailed fixtures** for complex scenarios
4. **Separate concerns** between unit and integration tests

### Error Testing

1. **Test error conditions** and edge cases
2. **Validate error messages** are helpful and informative
3. **Test graceful failure** scenarios
4. **Verify cleanup** happens correctly

## Performance Testing

### Benchmarks

The test suite includes performance benchmarks for:

- **Tool execution time**: Should complete within reasonable time limits
- **Memory usage**: Should not have memory leaks
- **Token estimation accuracy**: Should be within acceptable error margins
- **Large file handling**: Should scale linearly with input size

### Load Testing

```bash
# Run stress tests
python -m pytest tests/performance/ -k "stress" -v

# Run scalability tests
python -m pytest tests/performance/ -k "scalability" -v

# Run with timing for all tests
python -m pytest tests/ --durations=10
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure the project is installed in development mode
2. **Permission errors**: Check that tools have execute permissions
3. **Path resolution**: Verify tool paths are correct for your environment
4. **Timeout errors**: Increase timeout values for slow tests

### Debugging Tests

```bash
# Run with debugging output
python -m pytest tests/unit/test_skill_analyzer.py -v -s

# Stop on first failure
python -m pytest tests/ -x

# Run with Python debugger
python -m pytest tests/ --pdb

# Run specific failing test with maximum verbosity
python -m pytest tests/unit/test_skill_analyzer.py::TestSkillAnalyzer::test_skill_analyzer_help -vv -s
```

## Contributing to Tests

### Adding New Tests

1. **Follow naming conventions**: `test_[functionality].py`
2. **Use appropriate fixtures** for common setup
3. **Add detailed coverage** for new functionality
4. **Include edge cases** and error conditions
5. **Document test scenarios** in docstrings

### Test Review Checklist

- [ ] Test name clearly describes what is being tested
- [ ] Test follows AAA pattern
- [ ] Test isolates the functionality under test
- [ ] Test includes both positive and negative cases
- [ ] Test uses appropriate fixtures
- [ ] Test has meaningful assertions
- [ ] Test contributes to coverage requirements
- [ ] Test is maintainable and well-documented

## Test Data Management

### Temporary Files

Tests use Python's `tempfile` module for creating temporary files and directories:

```python
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write(content)
    temp_path = f.name

try:
    # Use temp_path in tests
    pass
finally:
    # Cleanup
    os.unlink(temp_path)
```

### Test Fixtures

Fixtures provide consistent test data and setup:

```python
@pytest.fixture
def sample_skill_file(self):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)
```

## Maintenance

### Regular Tasks

1. **Update tests** when tools are modified
2. **Add new tests** for new functionality
3. **Review coverage** and address gaps
4. **Update expected outputs** when behavior changes
5. **Performance monitoring** and optimization

### Test Updates

When modifying existing functionality:

1. **Run related tests** to validate no regressions
2. **Update test expectations** if behavior changes intentionally
3. **Add new tests** for modified functionality
4. **Verify coverage** remains acceptable
5. **Update documentation** for test changes
