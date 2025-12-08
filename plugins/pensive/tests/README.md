# Pensive Plugin Test Suite

This directory contains comprehensive tests for the pensive code review plugin, following TDD/BDD principles and ensuring high-quality coverage of all functionality.

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_*.py                      # Root-level integration tests
├── skills/                        # Skill-specific tests
│   ├── test_unified_review.py
│   ├── test_api_review.py
│   ├── test_architecture_review.py
│   ├── test_bug_review.py
│   ├── test_rust_review.py
│   ├── test_test_review.py
│   ├── test_math_review.py
│   └── test_makefile_review.py
├── agents/                        # Agent integration tests
│   ├── test_code_reviewer.py
│   ├── test_architecture_reviewer.py
│   └── test_rust_auditor.py
├── scripts/                       # Command entry point tests
│   ├── test_review.py
│   ├── test_api_review_cmd.py
│   ├── test_architecture_review_cmd.py
│   └── test_rust_review_cmd.py
└── fixtures/                      # Test data and utilities
    ├── sample_repos/
    ├── sample_findings.py
    └── test_helpers.py
```

## Testing Philosophy

### Test-Driven Development (TDD)
- **Red-Green-Refactor**: Write failing tests first, implement to pass, then refactor
- **Single Responsibility**: Each test validates one specific behavior
- **Fast Feedback**: Unit tests run in milliseconds, integration tests in seconds

### Behavior-Driven Development (BDD)
- **User-Centric**: Tests validate user behaviors and use cases
- **Given-When-Then**: Clear scenario structure in integration tests
- **Domain Language**: Tests use terminology familiar to developers

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Individual function and method testing
- Business logic validation
- Edge case and error handling
- Performance of specific algorithms

### Integration Tests (`@pytest.mark.integration`)
- End-to-end workflow testing
- Multi-component interaction
- Real filesystem operations
- Agent dispatch and coordination

### Security Tests (`@pytest.mark.security`)
- Vulnerability detection
- Input validation
- Authentication/authorization
- Data sanitization

### Architecture Tests (`@pytest.mark.architecture`)
- Design pattern compliance
- ADR adherence
- System design validation
- Coupling and cohesion analysis

## Running Tests

### All Tests
```bash
pytest tests/ -v --cov=pensive
```

### By Category
```bash
# Unit tests only
pytest tests/ -m unit -v

# Integration tests only
pytest tests/ -m integration -v

# Security-focused tests
pytest tests/ -m security -v

# Architecture tests
pytest tests/ -m architecture -v
```

### Specific Skill Tests
```bash
# Test unified review skill
pytest tests/skills/test_unified_review.py -v

# Test API review skill
pytest tests/skills/test_api_review.py -v

# Test all review skills
pytest tests/skills/ -v
```

### Performance Testing
```bash
# Run with performance profiling
pytest tests/ --profile

# Memory usage tracking
pytest tests/ --memprof
```

## Test Data and Fixtures

### Sample Repositories
- `sample_repos/simple_js/`: Basic JavaScript project
- `sample_repos/rust_project/`: Rust application with Cargo.toml
- `sample_repos/multi_lang/`: Polyglot repository
- `sample_repos/with_issues/`: Repository containing known issues

### Mock Objects
- `MockTodoWrite`: Simulate progress tracking
- `MockSkillContext`: Provide skill execution context
- `MockAgentResponse`: Simulate agent responses
- `SampleFindings`: Representative code review findings

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
1. **Descriptive Names**: Test names should describe the behavior
2. **AAA Pattern**: Arrange-Act-Assert structure
3. **Test Constants**: Use meaningful constants, not magic numbers
4. **Isolation**: Tests should not depend on each other
5. **Cleanup**: Proper setup and teardown

### Example Test Structure
```python
def test_skill_detects_rust_code_correctly(temp_repository):
    """Given a repository with Rust code, when skill analyzes, then detects Rust."""
    # Arrange
    skill = RustReviewSkill()
    context = create_skill_context(temp_repository)

    # Act
    result = skill.detect_languages(context)

    # Assert
    assert "rust" in result
    assert result["rust"]["files"] > 0
```

### Mocking Guidelines
- Mock external dependencies (API calls, file system)
- Use real temporary files for file operations
- Mock at boundaries, not implementation details
- Verify interactions, not just state

## Continuous Integration

### GitHub Actions Workflow
- Run all tests on every push
- Generate coverage reports
- Fail build on coverage decrease
- Performance regression detection

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
- Test failure rate
- Performance benchmarks

These metrics help maintain test quality and identify areas for improvement.