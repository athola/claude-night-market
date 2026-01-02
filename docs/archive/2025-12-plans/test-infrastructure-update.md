# Test Infrastructure Modernization Plan

*Last Updated: 2025-12-06*

## Executive Summary

A 2-week dedicated sprint to modernize test infrastructure across all plugins, targeting 85% code coverage, standardized testing patterns, and improved test execution efficiency.

## Current State Analysis

### Test Coverage Across Plugins

| Plugin | Current Coverage | Target | Gap |
|--------|-----------------|--------|-----|
| Abstract | 75% | 85% | +10% |
| Conservation | 60% | 85% | +25% |
| Sanctum | 70% | 85% | +15% |
| Memory Palace | 65% | 85% | +20% |
| Parseltongue | 68% | 85% | +17% |
| Pensive | 72% | 85% | +13% |
| Conjure | 55% | 85% | +30% |
| Imbue | 50% | 85% | +35% |

**Average current coverage: 64%**
**Target average coverage: 85%**

### Identified Issues

1. **Inconsistent test patterns** across plugins
2. **Duplicated test fixtures** and setup code
3. **Poor integration test coverage**
4. **Missing end-to-end tests**
5. **Inconsistent test data management**
6. **No property-based testing**
7. **Minimal performance testing**
8. **Inadequate mocking strategies**

## Sprint Plan (2 Weeks)

### Week 1: Foundation & Standardization

#### Day 1-2: Shared Test Framework

**Objective**: Create a unified testing framework for all plugins

**Tasks**:
1. Create `claude-marketplace-testing` package
2. Standardize pytest configuration
3. Create shared test fixtures
4. Setup common test utilities

**Deliverables**:
```python
# tests/framework/
├── __init__.py
├── conftest.py          # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   ├── plugin_fixtures.py
│   ├── mock_fixtures.py
│   └── data_fixtures.py
├── utils/
│   ├── __init__.py
│   ├── assertions.py    # Custom assertions
│   ├── helpers.py       # Test helpers
│   └── bdd.py          # BDD helpers
└── data/
    ├── sample_skills.md
    ├── sample_configs.yaml
    └── test_data.json
```

**Implementation**:
```python
# conftest.py - Shared pytest configuration
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """Root test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_skill_content(test_data_dir):
    """Sample skill content for testing."""
    return (test_data_dir / "sample_skills.md").read_text()

@pytest.fixture
def mock_bash():
    """Mock bash operations for testing."""
    with patch('plugins.shared.utils.bash') as mock:
        yield mock

@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Temporary plugin directory for testing."""
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    # Create basic plugin structure
    (plugin_dir / ".claude-plugin").mkdir()
    return plugin_dir
```

#### Day 3-4: Test Coverage Analysis

**Objective**: Identify gaps and create coverage improvement plans

**Tasks**:
1. Run detailed coverage reports for all plugins
2. Create coverage visualization dashboards
3. Identify untested critical paths
4. Prioritize test additions based on risk

**Tools**:
```bash
# Generate coverage reports
pytest --cov=src --cov-report=html --cov-report=term-missing

# Coverage visualization
coverage-badge.py
coverage-dashboard.html
```

#### Day 5: Mock Strategy Standardization

**Objective**: Define consistent mocking patterns

**Tasks**:
1. Create mock library for common external dependencies
2. Standardize file system mocking
3. Create API mocking utilities
4. Define when to mock vs when to use test doubles

**Implementation**:
```python
# mocks.py - Standardized mocking utilities
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

class MockFileSystem:
    """Consistent file system mocking."""

    def __init__(self):
        self.files = {}
        self.directories = set()

    def add_file(self, path: str, content: str):
        self.files[path] = content

    def exists(self, path: str) -> bool:
        return path in self.files or path in self.directories

@contextmanager
def mock_file_system(files: dict):
    """Context manager for file system mocking."""
    mock_fs = MockFileSystem()
    for path, content in files.items():
        mock_fs.add_file(path, content)

    with patch('pathlib.Path.exists', mock_fs.exists):
        yield mock_fs
```

### Week 2: Implementation & Quality Improvement

#### Day 6-7: Property-Based Testing

**Objective**: Implement property-based testing for critical functions

**Tasks**:
1. Identify functions suitable for property-based testing
2. Write Hypothesis tests for core utilities
3. Create property-based test templates
4. Add to CI pipeline

**Implementation**:
```python
# property_tests.py - Property-based testing
from hypothesis import given, strategies as st
import pytest

@given(st.lists(st.integers(), min_size=1))
def test_sort_preserves_length(data):
    """Sorting should preserve list length."""
    result = sort_function(data)
    assert len(result) == len(data)

@given(st.text(), st.text())
def test_string_concatenation_properties(s1, s2):
    """Test string concatenation properties."""
    result = f"{s1}{s2}"

    # Length property
    assert len(result) == len(s1) + len(s2)

    # Prefix property
    assert result.startswith(s1)

    # Suffix property
    assert result.endswith(s2)
```

#### Day 8-9: Integration Testing Framework

**Objective**: Build detailed integration test suite

**Tasks**:
1. Create integration test templates
2. Setup test environment orchestration
3. Implement end-to-end test scenarios
4. Add performance regression tests

**Implementation**:
```python
# integration_tests.py - Integration testing framework
import pytest
from testcontainers.compose import DockerCompose

@pytest.fixture(scope="class")
def test_environment():
    """Orchestrated test environment."""
    with DockerCompose("tests/docker") as compose:
        # Wait for services to be ready
        compose.wait_for("http://test-service:8080/health")
        yield compose

class TestPluginIntegration:
    """Integration tests for plugin functionality."""

    def test_full_workflow(self, test_environment):
        """Test complete plugin workflow."""
        # Setup
        client = test_environment.get_service("test-service")

        # Execute
        response = client.post("/process", json={"data": "test"})

        # Verify
        assert response.status_code == 200
        assert response.json()["success"] is True
```

#### Day 10: Performance Testing

**Objective**: Add performance testing framework

**Tasks**:
1. Create performance benchmark utilities
2. Implement load testing scenarios
3. Add memory usage validation
4. Setup performance regression detection

**Implementation**:
```python
# performance_tests.py - Performance testing
import time
import psutil
import pytest
from functools import wraps

def measure_performance(max_time_ms: int = 1000, max_memory_mb: int = 100):
    """Decorator for performance testing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Measure initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024

            # Measure execution time
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Measure memory usage
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory

            # Assert performance constraints
            assert execution_time < max_time_ms, f"Too slow: {execution_time}ms"
            assert memory_used < max_memory_mb, f"Too much memory: {memory_used}MB"

            return result
        return wrapper
    return decorator

@measure_performance(max_time_ms=500, max_memory_mb=50)
def test_function_performance():
    """Test function performance constraints."""
    # Function to test
    pass
```

## Test Quality Standards

### 1. Coverage Requirements

```python
# Minimum coverage requirements
COVERAGE_REQUIREMENTS = {
    "overall": 85,        # Overall coverage
    "critical_paths": 95, # Critical code paths
    "unit": 90,          # Unit test coverage
    "integration": 80,    # Integration test coverage
}
```

### 2. Test Categories

```python
# Test categorization for pytest markers
TEST_MARKERS = {
    "unit": "Unit tests - fast, isolated tests",
    "integration": "Integration tests - test component interactions",
    "e2e": "End-to-end tests - full workflow testing",
    "performance": "Performance tests - timing and resource usage",
    "slow": "Slow tests - marked for separate execution",
    "security": "Security tests - vulnerability and validation",
}
```

### 3. Test Naming Conventions

```python
# Consistent test naming patterns
class TestClassName:
    """Test class using descriptive name."""

    def test_method_should_do_something_when_condition(self):
        """GIVEN context
        WHEN action
        THEN result
        """
        pass

    def test_property_should_hold_for_valid_input(self):
        """Property-based test naming."""
        pass
```

### 4. Test Data Management

```python
# Test data organization
test_data/
├── fixtures/          # Test fixtures
│   ├── skills/       # Skill file fixtures
│   ├── configs/      # Configuration fixtures
│   └── outputs/      # Expected output fixtures
├── generators/       # Test data generators
└── schemas/         # Test data schemas
```

## CI/CD Integration

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Infrastructure

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install -e "plugins/claude-marketplace-testing"

    - name: Run unit tests
      run: |
        pytest -m "not slow and not integration" \
               --cov=src \
               --cov-fail-under=85

    - name: Run integration tests
      run: |
        pytest -m "integration" \
               --cov=src \
               --cov-append

    - name: Run performance tests
      run: |
        pytest -m "performance"

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### 2. Test Execution Pipeline

```python
# test_runner.py - Centralized test execution
import pytest
import sys
from pathlib import Path

class TestRunner:
    """Centralized test execution with reporting."""

    def run_unit_tests(self, plugin_dir: Path) -> bool:
        """Run unit tests for a plugin."""
        args = [
            str(plugin_dir / "tests"),
            "-m", "not slow and not integration",
            "--cov=src",
            "--cov-fail-under=85",
            "--tb=short"
        ]
        return pytest.main(args) == 0

    def run_integration_tests(self, plugin_dir: Path) -> bool:
        """Run integration tests for a plugin."""
        args = [
            str(plugin_dir / "tests"),
            "-m", "integration",
            "--cov=src",
            "--cov-append"
        ]
        return pytest.main(args) == 0

    def run_performance_tests(self, plugin_dir: Path) -> bool:
        """Run performance tests for a plugin."""
        args = [
            str(plugin_dir / "tests"),
            "-m", "performance",
            "--tb=short"
        ]
        return pytest.main(args) == 0
```

## Test Data Management

### 1. Fixtures Strategy

```python
# fixtures/plugin_fixtures.py - Plugin-specific fixtures
import pytest
from pathlib import Path

@pytest.fixture
def valid_skill_file():
    """Valid skill file fixture."""
    return """---
name: test-skill
description: A test skill
category: testing
tools: [bash]
---

# Test Skill Content

This is a test skill for unit testing.
"""

@pytest.fixture
def invalid_skill_file():
    """Invalid skill file fixture."""
    return """---
name: ""
description: ""
---

Invalid content without proper frontmatter.
"""

@pytest.fixture
def plugin_config():
    """Standard plugin configuration fixture."""
    return {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "commands": [],
        "skills": [],
        "agents": []
    }
```

### 2. Test Data Generators

```python
# generators/data_generators.py - Test data generation
from faker import Faker
import random

fake = Faker()

class SkillDataGenerator:
    """Generate test skill data."""

    @staticmethod
    def valid_skill():
        return {
            "name": fake.words()[0].lower(),
            "description": fake.sentence(),
            "category": random.choice(["testing", "utility", "analysis"]),
            "tools": random.sample(["bash", "read", "write"], k=random.randint(1, 3))
        }

    @staticmethod
    def skill_content():
        skill = SkillDataGenerator.valid_skill()
        frontmatter = "\n".join([f"{k}: {v}" for k, v in skill.items()])
        return f"""---
{frontmatter}
---

# {skill['name'].title()}

{fake.paragraph()}
"""
```

## Success Metrics

### Coverage Targets

| Metric | Current | Target | Success Criteria |
|--------|---------|--------|------------------|
| Overall Coverage | 64% | 85% | ≥85% across all plugins |
| Critical Path Coverage | 70% | 95% | ≥95% for critical functions |
| Integration Coverage | 40% | 80% | ≥80% for integration points |
| Property-Based Tests | 5% | 30% | ≥30% of functions have property tests |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Execution Time | <5min per plugin | Automated timing |
| Flaky Test Rate | <1% | CI failure analysis |
| Test Maintenance Overhead | <10% of dev time | Developer surveys |
| Bug Detection Rate | >90% of new bugs | Bug tracking analysis |

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Suite Runtime | <30min total | CI timing |
| Memory Usage | <2GB peak | Resource monitoring |
| Parallel Execution | 4x speedup | Before/after comparison |
| Test Failure Rate | <5% per run | CI statistics |

## Implementation Timeline

### Pre-Sprint (Week 0)
- [ ] Review current test infrastructure
- [ ] Identify high-priority plugins
- [ ] Setup development environment
- [ ] Create test modernization backlog

### Sprint Week 1
- [ ] Create shared test framework
- [ ] Implement standard pytest configuration
- [ ] Create shared fixtures and utilities
- [ ] Analyze coverage gaps
- [ ] Define mock strategy

### Sprint Week 2
- [ ] Implement property-based testing
- [ ] Create integration test framework
- [ ] Add performance testing
- [ ] Update CI/CD pipelines
- [ ] Document new practices

### Post-Sprint (Week 3-4)
- [ ] Roll out to all plugins
- [ ] Monitor coverage improvements
- [ ] Gather developer feedback
- [ ] Refine based on experience

## Risk Mitigation

### Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Developer resistance | Medium | High | Early involvement, training, quick wins |
| Test suite slowdown | High | Medium | Parallel execution, selective runs |
| Coverage gaming | Medium | Medium | Quality reviews, complexity analysis |
| Tooling complexity | High | Low | Simplified setup, good documentation |
| Legacy compatibility | Medium | High | Gradual migration, backward compatibility |

### Rollback Strategy

```python
# Feature flags for gradual rollout
USE_NEW_TEST_FRAMEWORK = os.getenv("USE_NEW_TEST_FRAMEWORK", "false").lower() == "true"

def run_tests_with_fallback():
    """Run tests with fallback to old framework."""
    try:
        if USE_NEW_TEST_FRAMEWORK:
            return run_new_tests()
        else:
            return run_legacy_tests()
    except Exception as e:
        logger.error(f"New test framework failed: {e}")
        return run_legacy_tests()
```

## Conclusion

This test infrastructure modernization plan will:

1. **Standardize testing practices** across all plugins
2. **Improve code coverage** from 64% to 85%
3. **Reduce test maintenance overhead** through shared utilities
4. **Enable better CI/CD integration** with consistent patterns
5. **Improve developer productivity** through better tooling

The 2-week sprint focuses on high-impact improvements while maintaining compatibility with existing workflows. The phased approach validates quick wins while building toward detailed test quality improvements.
