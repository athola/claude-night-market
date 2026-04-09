# Quality Validation Module

## Overview

detailed test quality assurance through static analysis, dynamic validation, metrics tracking, and structured peer review.

## Validation Categories

### 1. Static Analysis
Validate test code without execution (details below).

### 2. Dynamic Validation
Execute tests to verify they actually work (details below).

### 3. Metrics Validation
Track quantitative quality measures (details below).

### 4. Peer Review Checklist
Structured validation for human review.

#### Quality Gates Checklist
```python
QUALITY_GATES = {
    "structure": [
        "Test follows BDD pattern with Given/When/Then",
        "Test has descriptive name explaining behavior",
        "Test is independent and isolated",
        "Test uses appropriate fixtures or setup",
    ],
    "assertions": [
        "Assertions are specific and meaningful",
        "Error messages are descriptive",
        "Both positive and negative cases tested",
        "Edge cases are covered",
    ],
    "maintenance": [
        "Test is readable and understandable",
        "Test data is clearly defined",
        "External dependencies are mocked",
        "Test documentation is adequate",
    ],
    "performance": [
        "Test runs quickly (< 1 second)",
        "No unnecessary I/O operations",
        "Memory usage is reasonable",
        "Tests are parallelizable",
    ],
}
```

## Validation Workflow

```python
def run_validation_pipeline(test_path, source_path=None):
    """Run complete validation pipeline."""

    report = ValidationReport()

    # Phase 1: Static Analysis
    static_issues = validate_static_quality(test_path)
    report.add_section("Static Analysis", static_issues)

    # Phase 2: Dynamic Validation
    execution_results = validate_test_execution(test_path)
    report.add_section("Dynamic Validation", execution_results)

    # Phase 3: Mutation Testing (if source provided)
    if source_path:
        mutation_score = run_mutation_tests(test_path, source_path)
        report.add_section("Mutation Testing", {"score": mutation_score})

    # Phase 4: Metrics Validation
    coverage_violations = validate_coverage_metrics(execution_results["coverage"])
    report.add_section("Coverage Metrics", coverage_violations)

    # Phase 5: Complexity Analysis
    complexity = calculate_test_complexity(test_path)
    report.add_section("Complexity Metrics", complexity)

    return report
```

## Quality Standards

### Minimum Requirements
- **Coverage**: 85% line, 80% branch, 90% function
- **Mutation Score**: 80% or higher
- **Test Speed**: < 1 second per test
- **Independence**: No test dependencies
- **BDD Compliance**: All tests follow BDD patterns

### Excellence Criteria
- **Coverage**: 95% line, 90% branch, 100% function
- **Mutation Score**: 90% or higher
- **Test Speed**: < 0.5 seconds per test
- **Documentation**: detailed behavior description
- **Maintainability**: Clear, readable, well-structured

### Failure Modes
Tests failing validation should:
1. Generate detailed issue reports
2. Suggest specific improvements
3. Provide examples of fixes
4. Block merging until resolved

---

### Static Analysis

Validate test code without execution using pattern matching
and AST analysis.

#### Code Quality Checks

```python
def validate_static_quality(test_file):
    """Perform static quality validation."""

    issues = []

    # Check test naming
    if not test_has_descriptive_name(test_file):
        issues.append("Test name should describe behavior")

    # Check BDD structure
    if not has_bdd_structure(test_file):
        issues.append("Test should follow BDD pattern")

    # Check assertion quality
    if has_vague_assertions(test_file):
        issues.append("Use specific, meaningful assertions")

    # Check test independence
    if tests_have_dependencies(test_file):
        issues.append("Tests should be independent")

    return issues
```

#### Pattern Validation

```python
BDD_PATTERNS = {
    "given_pattern": r"GIVEN\s+.+",
    "when_pattern": r"WHEN\s+.+",
    "then_pattern": r"THEN\s+.+",
    "and_pattern": r"AND\s+.+",
}

def validate_bdd_patterns(test_content):
    """Validate BDD pattern usage."""
    missing_patterns = []

    for pattern_name, pattern_regex in BDD_PATTERNS.items():
        if not re.search(pattern_regex, test_content, re.IGNORECASE):
            missing_patterns.append(pattern_name)

    return missing_patterns
```

#### Validation Categories

- **Naming**: Descriptive, behavior-focused test names
- **Structure**: Proper BDD patterns and organization
- **Assertions**: Specific, meaningful checks
- **Independence**: No test dependencies
- **Documentation**: Clear docstrings and comments

---

### Dynamic Validation

Executes tests to verify they actually work and measure their
quality.

#### Test Execution Validation

```python
def validate_test_execution(test_path):
    """Validate test executes correctly."""

    results = {
        "passes": False,
        "failures": [],
        "errors": [],
        "warnings": [],
        "coverage": 0,
    }

    # Run tests in isolated environment
    test_result = pytest.main([
        test_path,
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=json",
    ])

    # Analyze results
    if test_result == 0:
        results["passes"] = True
    else:
        # Parse failures and errors
        results["failures"] = parse_test_failures()
        results["errors"] = parse_test_errors()

    # Load coverage data
    results["coverage"] = load_coverage_data()

    return results
```

#### Mutation Testing

```python
def run_mutation_tests(test_path, source_path):
    """Run mutation testing to verify test quality."""

    mutations = generate_mutations(source_path)
    killed_mutants = 0
    total_mutants = len(mutations)

    for mutation in mutations:
        # Apply mutation
        apply_mutation(source_path, mutation)

        # Run tests
        if pytest.main([test_path, "-q"]) != 0:
            killed_mutants += 1  # Test caught the mutation

        # Restore original code
        restore_original(source_path)

    mutation_score = killed_mutants / total_mutants
    return mutation_score
```

#### Performance Testing

- **Execution time**: Tests should run quickly (< 1 second)
- **Memory usage**: No memory leaks or excessive consumption
- **Parallel execution**: Tests should run independently
- **Resource cleanup**: Proper teardown after each test

---

### Quality Metrics

Tracks quantitative quality measures for test suites.

#### Coverage Metrics

```python
def validate_coverage_metrics(coverage_data):
    """Validate test coverage meets standards."""

    metrics = {
        "line_coverage": coverage_data["lines_covered"] / coverage_data["lines_valid"],
        "branch_coverage": coverage_data["branches_covered"] / coverage_data["branches_valid"],
        "function_coverage": coverage_data["functions_covered"] / coverage_data["functions_valid"],
    }

    standards = {
        "line_coverage": 0.85,  # 85% minimum
        "branch_coverage": 0.80,  # 80% minimum
        "function_coverage": 0.90,  # 90% minimum
    }

    violations = []
    for metric, value in metrics.items():
        if value < standards[metric]:
            violations.append(f"{metric}: {value:.1%} < {standards[metric]:.1%}")

    return violations
```

#### Test Complexity Metrics

```python
def calculate_test_complexity(test_file):
    """Calculate cyclomatic complexity of tests."""

    complexity_metrics = {
        "average_assertions_per_test": 0,
        "test_length_violations": 0,
        "setup_complexity": 0,
        "mock_count": 0,
    }

    # Analyze each test
    for test in extract_tests(test_file):
        assertions = count_assertions(test)
        if assertions > 5:
            complexity_metrics["test_length_violations"] += 1

        complexity_metrics["average_assertions_per_test"] += assertions
        complexity_metrics["mock_count"] += count_mocks(test)

    complexity_metrics["average_assertions_per_test"] /= len(extract_tests(test_file))

    return complexity_metrics
```

#### Quality Score Calculation

Combine multiple metrics into an overall score:
- Static analysis (20%)
- Dynamic validation (30%)
- Coverage metrics (20%)
- Mutation testing (20%)
- Complexity (10%)
