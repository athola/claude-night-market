# Imbue Plugin Mocking Quick Reference

> Fast reference for standardized mocking patterns

## Quick Start

### Use Existing Fixtures

```python
def test_something(mock_claude_tools):
    """Use pre-configured mock tools."""
    mock_claude_tools["Bash"].return_value = "output"
    # Your test code...
```

### Create Custom Mocks

```python
from unittest.mock import MagicMock

def test_custom():
    """Create a custom mock when needed."""
    mock_obj = MagicMock(name="MyObject", spec=["method1", "method2"])
    mock_obj.method1.return_value = "value"
```

## Available Fixtures

| Fixture | Purpose | Example |
|---------|---------|---------|
| `mock_claude_tools` | All Claude tools pre-configured | `mock_claude_tools["Read"].return_value = "..."` |
| `mock_skill_factory` | Create skill execution mocks | `skill_mock = mock_skill_factory()` |
| `mock_bash_factory` | Bash with command mappings | `bash = mock_bash_factory({"pwd": "/test"})` |
| `mock_todo_write` | TodoWrite tool mock | `mock_todo_write.assert_called()` |

## Common Patterns

### Sequential Returns

```python
# Returns different values on each call
mock_claude_tools["Bash"].side_effect = [
    "/test/project",     # First call
    "feature/auth",      # Second call
    "On branch main",    # Third call
]
```

### Mixed Returns and Exceptions

```python
mock_claude_tools["Read"].side_effect = [
    "Success",
    PermissionError("Denied"),
    "Success again",
]
```

### Track Skill Calls

```python
def test_skills(mock_skill_factory):
    skill_mock = mock_skill_factory()
    result = skill_mock(skill_name="review-core", context={})

    # Check what was called
    assert len(skill_mock.calls) == 1
    assert skill_mock.calls[0]["skill"] == "review-core"
```

### Command-Response Mapping

```python
def test_git(mock_bash_factory):
    bash = mock_bash_factory({
        "pwd": "/test/project",
        "git status": "On branch main",
        "git diff": "diff content",
    })

    assert bash("pwd") == "/test/project"
    assert "pwd" in bash.calls
```

## Assertion Patterns

```python
# Single call
mock.assert_called_once()
mock.assert_called_once_with("expected_arg")

# Multiple calls in order
from unittest.mock import call
mock.assert_has_calls([
    call("first"),
    call("second"),
])

# Call counting
assert mock.call_count == 3

# Check specific call
assert call("arg") in mock.call_args_list
```

## Best Practices

**DO**
- Use `MagicMock` with `name=` parameter
- Use fixtures from conftest.py
- Use `side_effect=` for sequences
- Add `spec=` when practical
- Document custom mocks

**DON'T**
- Use `Mock()` without a name
- Create duplicate mock setups
- Use direct assignment for sequential values
- Forget to verify calls
- Mix mocking patterns

## Examples

### Example 1: Basic Tool Mock

```python
def test_file_reading(mock_claude_tools):
    """Test reading files with mocked Read tool."""
    mock_claude_tools["Read"].return_value = "file content"

    # Your code that uses Read
    result = some_function_that_reads()

    assert "file content" in result
    mock_claude_tools["Read"].assert_called_once()
```

### Example 2: Workflow Testing

```python
def test_workflow(mock_claude_tools):
    """Test multi-step workflow."""
    # Setup
    executed_steps = []

    def track_skill(skill_name, context):
        executed_steps.append(skill_name)
        return f"{skill_name} done"

    mock_claude_tools["Skill"] = MagicMock(
        name="Skill",
        side_effect=track_skill
    )

    # Execute workflow
    run_workflow()

    # Verify
    assert executed_steps == [
        "review-core",
        "evidence-logging",
        "structured-output"
    ]
```

### Example 3: Error Handling

```python
def test_error_handling(mock_claude_tools):
    """Test graceful error handling."""
    mock_claude_tools["Read"].side_effect = [
        "Success",
        PermissionError("Denied"),
        "Success",
    ]

    # Should handle error gracefully
    result = resilient_function()

    assert result["errors"] == 1
    assert result["successes"] == 2
```

## Troubleshooting

### Mock Not Called?
```python
# Check call count
print(f"Called {mock.call_count} times")

# See all calls
print(mock.call_args_list)
```

### Wrong Return Value?
```python
# Check what was configured
print(f"Return value: {mock.return_value}")
print(f"Side effect: {mock.side_effect}")
```

### Attribute Error?
```python
# Add spec to prevent invalid access
mock = MagicMock(
    name="MyMock",
    spec=["valid_method1", "valid_method2"]
)
```

## More Information

- Full Standards: `tests/MOCKING_STANDARDS.md`
- Summary: `tests/STANDARDIZATION_SUMMARY.md`
- Examples: `tests/unit/agents/test_review_analyst.py`

## Quick Commands

```bash
# Run tests
uv run pytest tests/ --no-cov

# Run specific file
uv run pytest tests/unit/agents/test_review_analyst.py -v

# Show fixtures
uv run pytest --fixtures tests/
```

---

**Last Updated**: 2025-12-12
