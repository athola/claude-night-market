# Imbue Plugin Testing Mocking Standards

This document outlines the standardized mocking patterns adopted across the imbue plugin test suite.

## Motivation

Prior to standardization, the test suite exhibited several inconsistencies:
- Mixed use of `Mock()`, `MagicMock()`, and `mocker` fixture
- Duplicate mock setup code across test files
- Inconsistent mock return values for the same dependencies
- Missing `spec=` parameters reducing type safety
- Varying patterns for `side_effect` usage

## Standardized Patterns

### 1. Use MagicMock Over Mock

**Rationale**: `MagicMock` provides enhanced functionality including support for magic methods and better attribute access.

```python
from unittest.mock import MagicMock

# Good
mock_tool = MagicMock(name="Read")

# Avoid
mock_tool = Mock()  # Less functionality
```

### 2. Prefer pytest-mock's mocker Fixture

**Rationale**: The `mocker` fixture provides better test isolation and automatic cleanup.

```python
# Good - using mocker fixture
def test_something(mocker):
    mock_bash = mocker.patch.object(some_obj, 'bash', return_value="output")
    # Test code...
    mock_bash.assert_called_once()

# Acceptable for simple cases - using conftest fixtures
def test_something_else(mock_claude_tools):
    mock_claude_tools["Bash"].return_value = "output"
    # Test code...
```

### 3. Use spec= for Type Safety

**Rationale**: Adding `spec=` prevents accidental attribute access and provides better IDE support.

```python
# Good
mock_validator = MagicMock(
    spec=["plugin_root", "scan_review_workflows", "validate_review_workflows"]
)

# Acceptable when spec is not practical
mock_tool = MagicMock(name="Read")
```

### 4. Standardized Fixtures in conftest.py

#### mock_claude_tools
Pre-configured dictionary of all Claude Code tools with sensible defaults.

```python
def test_workflow(mock_claude_tools):
    # All tools are already set up with defaults
    mock_claude_tools["Bash"].side_effect = ["output1", "output2"]
    # ... test code
```

#### mock_skill_factory
Factory for creating custom skill execution mocks that track calls.

```python
def test_skills(mock_skill_factory):
    skill_mock = mock_skill_factory()
    result = skill_mock(skill_name="review-core", context={})
    assert len(skill_mock.calls) == 1
```

#### mock_bash_factory
Factory for Bash mocks with command-response mappings.

```python
def test_git_commands(mock_bash_factory):
    bash_mock = mock_bash_factory({
        "pwd": "/test/project",
        "git status": "On branch main"
    })
    assert bash_mock("pwd") == "/test/project"
```

### 5. Consistent side_effect Usage

Use `side_effect=` for sequential returns or exceptions.

```python
# Good - sequential return values
mock_claude_tools["Bash"].side_effect = [
    "first output",
    "second output",
    "third output",
]

# Good - mixed returns and exceptions
mock_claude_tools["Read"].side_effect = [
    "File content",
    PermissionError("Permission denied"),
    "Another file",
]
```

### 6. Call Verification Patterns

Standardized assertion patterns for mock verification.

```python
# Single call verification
mock.assert_called_once_with(expected_arg)

# Multiple calls in order
from unittest.mock import call
mock.assert_has_calls([
    call("first"),
    call("second"),
])

# Call counting
assert mock.call_count == 3

# Check calls without strict ordering
assert call("some_arg") in mock.call_args_list
```

## Migration Guide

### Before: Inconsistent Mocking
```python
from unittest.mock import Mock, patch

def test_old_style():
    # Inconsistent patterns
    mock = Mock()
    mock.return_value = "value"

    with patch('module.function') as mock_func:
        # Test code
        pass
```

### After: Standardized Mocking
```python
from unittest.mock import MagicMock

def test_new_style(mock_claude_tools):
    # Use fixtures when possible
    mock_claude_tools["Bash"].return_value = "output"

    # Or use mocker for more control
def test_with_mocker(mocker):
    mock_func = mocker.patch('module.function', return_value="value")
    mock_func.assert_called_once()
```

## Common Patterns

### Pattern 1: Mocking Tool Sequences

```python
def test_sequential_tool_calls(mock_claude_tools):
    """Test multiple tool calls with different outputs."""
    mock_claude_tools["Bash"].side_effect = [
        "/test/project",           # pwd
        "feature/auth",            # git branch
        "On branch feature/auth", # git status
    ]

    # Execute test logic
    # Verify calls if needed
    assert mock_claude_tools["Bash"].call_count == 3
```

### Pattern 2: Mocking Skill Workflows

```python
def test_skill_orchestration(mock_claude_tools):
    """Test skill execution workflow."""
    executed_skills = []

    def track_skill(skill_name, context):
        executed_skills.append(skill_name)
        return f"{skill_name} completed"

    mock_claude_tools["Skill"] = MagicMock(
        name="Skill",
        side_effect=track_skill
    )

    # Test workflow
    assert "review-core" in executed_skills
```

### Pattern 3: Mocking with Errors

```python
def test_error_handling(mock_claude_tools):
    """Test graceful error handling."""
    mock_claude_tools["Read"].side_effect = [
        "Success",
        PermissionError("Permission denied"),
        "Success again",
    ]

    # Test should handle the exception gracefully
```

## Anti-Patterns to Avoid

### Don't: Create Mocks Without Names
```python
# Hard to debug
mock = MagicMock()
```

### Do: Always Name Your Mocks
```python
# Easy to identify in error messages
mock = MagicMock(name="BashTool")
```

### Don't: Use Direct Assignment for Sequential Values
```python
# Doesn't work as expected
mock.return_value = "first"
mock.return_value = "second"  # Overwrites first
```

### Do: Use side_effect for Sequences
```python
mock.side_effect = ["first", "second", "third"]
```

### Don't: Duplicate Mock Setup Across Tests
```python
# Every test creates the same mock
def test_one():
    mock_tools = {"Read": Mock(), "Bash": Mock()}

def test_two():
    mock_tools = {"Read": Mock(), "Bash": Mock()}  # Duplicate
```

### Do: Use Fixtures for Common Mocks
```python
def test_one(mock_claude_tools):
    # Use shared fixture

def test_two(mock_claude_tools):
    # Same fixture, isolated state
```

## Testing Checklist

When writing or reviewing tests, verify:

- [ ] Using `MagicMock` instead of `Mock` where appropriate
- [ ] All mocks have meaningful `name=` parameters
- [ ] Using `mocker` fixture or conftest fixtures instead of `@patch`
- [ ] `spec=` parameter added where practical
- [ ] Using `side_effect=` for sequential returns or exceptions
- [ ] Proper call assertions (`assert_called_with`, `assert_has_calls`)
- [ ] No duplicate mock setup code
- [ ] Mock documentation clearly states purpose

## Examples

See the following test files for standardized patterns:
- `tests/unit/agents/test_review_analyst.py`
- `tests/unit/commands/test_review_command.py`
- `tests/unit/skills/test_evidence_logging.py`

## Resources

- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [MagicMock vs Mock](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock)
