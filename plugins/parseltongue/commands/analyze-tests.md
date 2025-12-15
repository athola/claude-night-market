# Analyze Tests Command

## Usage

Analyzes Python test suites for quality, coverage, and improvement opportunities.

### Basic Usage
```
/analyze-tests
```
Analyzes tests in the current directory.

### Specific Path
```
/analyze-tests tests/unit/
```
Analyzes tests in a specific directory.

## What It Does

1. **Discovers Tests**: Finds all test files matching `test_*.py` or `*_test.py`
2. **Coverage Analysis**: Reports test coverage metrics
3. **Quality Assessment**: Evaluates test structure, naming, and patterns
4. **Improvement Suggestions**: Provides specific recommendations
5. **Gap Identification**: Identifies untested code paths

## Analysis Categories

- **Structure**: Test organization, fixture usage, conftest patterns
- **Coverage**: Line coverage, branch coverage, missing lines
- **Quality**: Test naming, assertions, independence
- **Patterns**: AAA pattern adherence, parameterization usage
- **Performance**: Test execution time, slow test identification

## Output Format

For each test module:
- Test count and coverage percentage
- Pattern compliance score
- Specific improvement recommendations
- Critical issues requiring attention

## Examples

```bash
# Analyze all tests with coverage
/analyze-tests --coverage

# Focus on quality patterns
/analyze-tests --quality-only

# Generate detailed report
/analyze-tests --report detailed
```

## Integration

Uses the `python-testing` skill's analysis tools:
- `test-analyzer`: Quality and pattern analysis
- `coverage-reporter`: Coverage metrics and gaps
- `test-runner`: Execution and timing analysis

This command helps maintain high-quality test suites that follow pytest best practices.
