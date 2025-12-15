# Conservation Plugin Test Suite

This comprehensive test suite validates the conservation plugin's resource optimization, performance monitoring, and token conservation capabilities following TDD/BDD principles.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── README.md                            # This documentation
├── unit/                                # Unit tests for individual components
│   ├── scripts/                         # Core validation logic tests
│   │   └── test_*.py
│   ├── skills/                          # Skill-specific unit tests
│   │   ├── test_context_optimization.py # MECW principles and context management
│   │   ├── test_token_conservation.py   # Token optimization and quota tracking
│   │   ├── test_performance_monitoring.py # Resource usage monitoring
│   │   ├── test_mcp_code_execution.py   # MCP pattern optimization
│   │   └── test_optimizing_large_skills.py # Large skill optimization
│   ├── commands/                        # Command-specific tests
│   │   ├── test_optimize_context.py     # /optimize-context command
│   │   └── test_analyze_growth.py       # /analyze-growth command
│   └── agents/                          # Agent-specific tests
│       └── test_context_optimizer.py    # Autonomous context optimization
├── integration/                         # Workflow integration tests
│   ├── test_conservation_workflow_integration.py  # End-to-end conservation workflows
│   ├── test_token_optimization_integration.py     # Token conservation integration
│   └── test_performance_monitoring_integration.py # Performance monitoring workflows
├── performance/                         # Performance benchmarks
│   ├── test_conservation_performance.py # Conservation optimization performance
│   └── test_scalability_tests.py       # Large-scale resource management
└── fixtures/                            # Test data and samples
    ├── sample_skills/                   # Sample skill files
    ├── token_logs/                      # Token usage logs
    ├── performance_data/                # Performance metrics
    └── expected_outputs/                # Expected test results
```

## Running Tests

### Prerequisites
- Python 3.8+
- uv package manager
- Plugin dependencies installed

### Basic Test Execution
```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=scripts --cov-report=html

# Run specific test categories
uv run pytest tests/unit/ -v          # Unit tests only
uv run pytest tests/integration/ -v    # Integration tests only
uv run pytest tests/performance/ -v    # Performance tests only

# Run tests with markers
uv run pytest tests/ -m "unit" -v      # Unit tests only
uv run pytest tests/ -m "integration" -v # Integration tests only
uv run pytest tests/ -m "performance" -v # Performance tests only
```

### Make Commands
```bash
make test           # Run all tests with coverage
make test-unit      # Run unit tests
make test-integration # Run integration tests
make test-performance # Run performance tests
make test-verbose   # Run tests with verbose output
make coverage       # Generate coverage report
```

## Test Categories

### Unit Tests
- **Core Logic**: Conservation validator and analysis scripts
- **Skills**: Individual skill business logic validation
- **Commands**: Command parsing and execution logic
- **Agents**: Agent workflow and decision-making tests

### Integration Tests
- **Workflow Orchestration**: End-to-end conservation workflows
- **Token Optimization**: Complete token conservation pipelines
- **Performance Monitoring**: Resource tracking and alerting

### Performance Tests
- **Scalability**: Large-scale resource management
- **Efficiency**: Optimization algorithm performance
- **Resource Usage**: Memory and CPU consumption validation

## Key Testing Patterns

### TDD/BDD Structure
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

### Conservation-Specific Testing

#### MECW (Maximum Effective Context Window) Testing
- Context utilization analysis
- Threshold compliance validation
- Optimization recommendation testing

#### Token Conservation Testing
- Quota tracking and validation
- Usage pattern analysis
- Efficiency measurement

#### Performance Monitoring Testing
- Resource usage tracking
- Alert system validation
- Report generation accuracy

## Test Fixtures

### Core Fixtures
- `conservation_plugin_root`: Plugin root directory
- `sample_skill_content`: Valid skill file content
- `sample_plugin_json`: Plugin configuration
- `mock_todo_write`: TodoWrite tool mock
- `mock_claude_tools`: Claude Code tools mock

### Specialized Fixtures
- `mock_performance_monitor`: Performance monitoring mock
- `mock_mecw_analyzer`: MECW analysis mock
- `mock_token_quota_tracker`: Token quota tracking mock
- `sample_context_analysis`: Context analysis results
- `sample_performance_metrics`: Performance metrics data

## Quality Gates

### Coverage Requirements
- **Unit Tests**: 95% line coverage minimum
- **Integration Tests**: 100% workflow path coverage
- **Branch Coverage**: 90% minimum
- **Critical Business Logic**: 100% coverage required

### Performance Requirements
- Test execution time < 5 minutes total
- Memory usage < 1GB during test execution
- No memory leaks in long-running tests

## Test Data Management

### Sample Skills
- Realistic conservation skill examples
- Various complexity levels and configurations
- Edge cases and error conditions

### Performance Data
- Synthetic performance metrics
- Resource usage patterns
- Scaling test datasets

### Token Logs
- Realistic token usage patterns
- Quota exceedance scenarios
- Efficiency measurement data

## Continuous Integration

### Pre-commit Hooks
- Test execution on commit
- Coverage validation
- Performance regression detection

### CI/CD Pipeline
- Automated test execution
- Coverage reporting
- Performance benchmarking
- Quality gate enforcement

## Development Workflow

### Adding New Tests
1. Follow TDD/BDD patterns
2. Use appropriate fixtures
3. Include comprehensive scenarios
4. Add performance considerations
5. Update documentation

### Test Maintenance
- Regular review and updates
- Performance baseline adjustments
- Fixture maintenance
- Coverage monitoring

## Troubleshooting

### Common Issues
- Missing dependencies: Run `uv sync --group dev`
- Permission errors: Check script permissions
- Memory issues: Increase test timeout
- Performance failures: Check system resources

### Debug Tips
- Use `pytest -s` for live output
- Check test logs in `tests/.pytest_cache/`
- Monitor system resources during performance tests
- Validate test data integrity

## Contributing

When adding tests:
1. Follow established patterns
2. Maintain BDD structure
3. Include edge cases
4. Update fixtures if needed
5. Document new test categories

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [TDD/BDD Best Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [Conservation Plugin Documentation](../README.md)
