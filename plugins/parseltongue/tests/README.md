# Parseltongue Plugin Test Suite

This directory contains comprehensive tests for the parseltongue Python development suite, following TDD/BDD principles and ensuring high-quality coverage of all functionality.

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── README.md                      # Testing documentation and best practices
├── test_language_detection.py    # Language identification and parsing
├── test_pattern_matching.py      # DSL pattern recognition
├── test_code_transformation.py   # Code manipulation and generation
├── test_skill_integration.py     # Integration with skill files
├── test_token_efficiency.py      # Performance and token optimization
├── test_error_handling.py        # Edge cases and error scenarios
├── test_async_patterns.py        # Async code analysis and optimization
├── test_testing_guidance.py      # Test quality assessment and guidance
├── test_performance_optimization.py # Performance analysis and recommendations
├── test_packaging_guidance.py    # Python packaging and distribution
├── scripts/                      # Script-specific tests
│   ├── test_python_pro_agent.py    # Python generalist agent tests
│   ├── test_python_tester_agent.py  # Testing specialist agent tests
│   ├── test_python_optimizer_agent.py # Performance specialist agent tests
│   ├── test_analyze_tests.py        # Test analysis command tests
│   ├── test_run_profiler.py         # Profiling command tests
│   └── test_check_async.py           # Async validation command tests
├── fixtures/                     # Test data and utilities
│   ├── language_samples/           # Code samples in various languages
│   ├── performance_issues/         # Code with performance problems
│   ├── async_issues/              # Code with async issues
│   ├── testing_issues/            # Code with testing problems
│   └── packaging_examples/        # Sample project structures
└── language_samples/              # Multi-language code examples
    ├── python_samples/
    ├── javascript_samples/
    ├── typescript_samples/
    └── rust_samples/
```

## Testing Philosophy

### Test-Driven Development (TDD)
- **Red-Green-Refactor**: Write failing tests first, implement to pass, then refactor
- **Single Responsibility**: Each test validates one specific behavior
- **Fast Feedback**: Unit tests run in milliseconds, integration tests in seconds

### Behavior-Driven Development (BDD)
- **User-Centric**: Tests validate user behaviors and use cases
- **Given-When-Then**: Clear scenario structure in integration tests
- **Domain Language**: Tests use Python development terminology

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Individual function and method testing
- Business logic validation
- Edge case and error handling
- Pattern recognition algorithms
- Language detection logic

### Integration Tests (`@pytest.mark.integration`)
- End-to-end workflow testing
- Multi-component interaction
- Real file system operations
- Agent dispatch and coordination
- Command execution workflows

### Performance Tests (`@pytest.mark.performance`)
- Token efficiency analysis
- Processing speed validation
- Memory usage optimization
- Scalability testing
- Benchmark comparisons

### Async Tests (`@pytest.mark.asyncio`)
- Async pattern validation
- Concurrency testing
- Event loop analysis
- Performance optimization
- Error handling in async contexts

### Testing Tests (`@pytest.mark.testing`)
- Test quality assessment
- Coverage analysis
- Anti-pattern detection
- Fixture optimization
- Test structure validation

### Packaging Tests (`@pytest.mark.packaging`)
- Project structure analysis
- Dependency management
- Build system validation
- Distribution checks
- CI/CD integration

## Running Tests

### All Tests
```bash
pytest tests/ -v --cov=parseltongue
```

### By Category
```bash
# Unit tests only
pytest tests/ -m unit -v

# Integration tests only
pytest tests/ -m integration -v

# Performance tests
pytest tests/ -m performance -v

# Async-focused tests
pytest tests/ -m asyncio -v

# Testing-focused tests
pytest tests/ -m testing -v
```

### Specific Skill Tests
```bash
# Test language detection
pytest tests/test_language_detection.py -v

# Test async patterns
pytest tests/test_async_patterns.py -v

# Test performance optimization
pytest tests/test_performance_optimization.py -v
```

### Agent Tests
```bash
# Test all agents
pytest tests/scripts/ -v

# Test specific agent
pytest tests/scripts/test_python_pro_agent.py -v
```

## Test Data and Fixtures

### Language Samples
- **Python**: Modern Python 3.12+ with type hints, async/await
- **JavaScript**: ES6+ with async/await, classes, modules
- **TypeScript**: Type-safe JavaScript with interfaces and generics
- **Rust**: Safe systems programming with ownership and lifetimes

### Code Issue Categories
- **Performance Issues**: O(n²) algorithms, memory leaks, blocking I/O
- **Async Issues**: Missing await, sequential processing, error handling
- **Testing Issues**: No fixtures, testing implementation details, missing assertions
- **Packaging Issues**: Poor structure, missing metadata, dependency problems

### Pattern Examples
- **TDD Patterns**: AAA structure, fixture usage, parameterized tests
- **Performance Patterns**: Optimization techniques, caching strategies
- **Async Patterns**: Concurrency patterns, error handling, resource management
- **Testing Patterns**: Test structure, mocking strategies, coverage optimization

## Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 85% line coverage
- **Unit Tests**: 90% coverage of business logic
- **Integration Tests**: 80% coverage of workflows
- **Critical Paths**: 95% coverage

### Quality Gates
- All tests must pass
- No new test regressions
- Coverage must not decrease
- Performance tests within thresholds

## Test Best Practices

### Writing Tests
1. **Descriptive Names**: Test names should describe the behavior being tested
2. **AAA Pattern**: Arrange-Act-Assert structure
3. **Test Constants**: Use meaningful constants, not magic numbers
4. **Isolation**: Tests should not depend on each other
5. **Cleanup**: Proper setup and teardown

### Example Test Structure
```python
def test_detects_python_class_definition(sample_python_code):
    """Given Python code with class, when skill analyzes, then detects class structure."""
    # Arrange
    skill = LanguageDetectionSkill()
    code = sample_python_code

    # Act
    result = skill.detect_language_features(code)

    # Assert
    assert "class" in result["structures"]
    assert result["structures"]["class"] >= 1
    assert "UserService" in result["classes"]
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_optimizes_sequential_async_calls():
    """Given sequential async calls, when skill optimizes, then suggests concurrent execution."""
    # Arrange
    async_code = await load_async_sample("sequential_calls.py")
    skill = AsyncOptimizationSkill()

    # Act
    suggestions = await skill.analyze_and_suggest(async_code)

    # Assert
    assert any("asyncio.gather" in suggestion for suggestion in suggestions)
    assert any("concurrent" in suggestion for suggestion in suggestions)
```

## Mocking Guidelines

### When to Mock
- External dependencies (HTTP APIs, databases)
- File system operations (when testing logic, not I/O)
- Agent responses (for unit testing workflow logic)
- Time operations (for consistent test timing)

### When Not to Mock
- File system operations in integration tests
- Real code parsing and transformation
- Language detection logic
- Pattern matching algorithms

## Performance Testing

### Metrics to Track
- **Token Usage**: Ensure parseltongue itself is token-efficient
- **Processing Speed**: Code analysis should be fast
- **Memory Usage**: Should handle large codebases efficiently
- **Scalability**: Performance with increasing code complexity

### Benchmarking
```bash
# Run performance benchmarks
pytest tests/test_token_efficiency.py --benchmark-only

# Compare with previous runs
pytest tests/test_performance_optimization.py --benchmark-compare
```

## Continuous Integration

### GitHub Actions Workflow
- Run all tests on every push and PR
- Generate coverage reports
- Fail build on coverage decrease
- Performance regression detection
- Multi-Python version testing

### Local Development
```bash
# Quick feedback during development
pytest tests/ -x -v --lf

# Full test suite before commit
make test  # Runs: format, lint, test, coverage
```

## Test Debugging

### Common Issues
1. **Flaky Tests**: Tests that sometimes fail
   - Use deterministic test data
   - Avoid timing dependencies
   - Mock external services

2. **Slow Tests**: Tests taking too long
   - Mock expensive operations
   - Use fixtures for setup
   - Parallelize where possible

3. **Coverage Gaps**: Missing test coverage
   - Use `--cov-report=html` for detailed reports
   - Focus on uncovered branches
   - Add edge case tests

### Debugging Commands
```bash
# Run with debugger
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l

# Stop on first failure
pytest tests/ -x

# Run only failed tests
pytest tests/ --lf
```

## Contributing Tests

When adding new functionality:
1. Write tests first (TDD)
2. Ensure coverage meets standards
3. Add integration tests for workflows
4. Document test scenarios
5. Update this README if needed

## Test Metrics

We track the following metrics:
- Code coverage percentage
- Test execution time
- Number of tests per category
- Agent dispatch accuracy
- Pattern recognition success rate
- Token efficiency improvements
- Performance optimization effectiveness

These metrics help maintain test quality and identify areas for improvement in the parseltongue plugin.
