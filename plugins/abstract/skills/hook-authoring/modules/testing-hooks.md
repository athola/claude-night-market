# Testing Hooks

Comprehensive testing strategies for hook development, including unit tests, integration tests, security testing, and performance validation.

## Testing Philosophy

### Core Testing Principles

1. **Test Hook Logic, Not Tools**: Test your hook's behavior, not Claude's tools
2. **Mock External Dependencies**: Isolate hook logic from I/O and network
3. **Test All Paths**: Happy path, error cases, edge cases
4. **Verify Performance**: Test timing budgets and resource usage
5. **Security Testing**: Test security controls and sanitization

## Unit Testing

### Basic Hook Tests

```python
import pytest
from my_hooks import ValidationHooks

@pytest.mark.asyncio
async def test_dangerous_command_blocked():
    """Verify dangerous commands are blocked."""
    hooks = ValidationHooks()

    with pytest.raises(ValueError, match="Dangerous command"):
        await hooks.on_pre_tool_use("Bash", {"command": "rm -rf /"})

@pytest.mark.asyncio
async def test_safe_command_allowed():
    """Verify safe commands are allowed."""
    hooks = ValidationHooks()

    result = await hooks.on_pre_tool_use("Bash", {"command": "ls -la"})
    assert result is None  # None means allow

@pytest.mark.asyncio
async def test_input_transformation():
    """Verify input transformation works."""
    hooks = TransformationHooks()

    result = await hooks.on_pre_tool_use("Read", {
        "file_path": "relative/path.txt"
    })

    assert result is not None
    assert result["file_path"].startswith("/")  # Transformed to absolute
```

### Testing Return Values

```python
import pytest
from my_hooks import MyHooks

@pytest.mark.asyncio
async def test_pre_tool_use_returns_none():
    """Test hook returns None to allow unchanged."""
    hooks = MyHooks()
    result = await hooks.on_pre_tool_use("Bash", {"command": "echo hello"})
    assert result is None

@pytest.mark.asyncio
async def test_pre_tool_use_returns_modified_input():
    """Test hook returns modified input."""
    hooks = MyHooks()
    result = await hooks.on_pre_tool_use("Read", {"file_path": "file.txt"})

    assert isinstance(result, dict)
    assert "file_path" in result

@pytest.mark.asyncio
async def test_post_tool_use_returns_modified_output():
    """Test hook returns modified output."""
    hooks = MyHooks()
    result = await hooks.on_post_tool_use(
        "Bash", {"command": "ls"}, "file1\nfile2"
    )

    assert isinstance(result, str)
    assert "file1" in result
```

### Testing Error Handling

```python
import pytest
from my_hooks import ResilientHooks

@pytest.mark.asyncio
async def test_validation_error_doesnt_block():
    """Verify validation errors don't block operations."""
    hooks = ResilientHooks()

    # Even with validation error, should return None (allow)
    result = await hooks.on_pre_tool_use("Bash", {"invalid": "input"})
    assert result is None

@pytest.mark.asyncio
async def test_logging_error_doesnt_block():
    """Verify logging errors don't block operations."""
    hooks = ResilientHooks()

    # Should not raise even if logging fails
    result = await hooks.on_post_tool_use(
        "Bash", {"command": "ls"}, "output"
    )
    assert result is None
```

## Integration Testing

### Testing with Mock Agent

```python
import pytest
from unittest.mock import AsyncMock, Mock
from my_hooks import MyHooks

@pytest.mark.asyncio
async def test_hooks_with_mock_agent():
    """Test hooks integrated with mock agent."""
    hooks = MyHooks()

    # Simulate agent tool execution flow
    tool_name = "Bash"
    tool_input = {"command": "ls -la"}
    tool_output = "file1.txt\nfile2.txt"

    # PreToolUse
    modified_input = await hooks.on_pre_tool_use(tool_name, tool_input)
    assert modified_input is None or isinstance(modified_input, dict)

    # PostToolUse
    modified_output = await hooks.on_post_tool_use(
        tool_name, tool_input, tool_output
    )
    assert modified_output is None or isinstance(modified_output, str)

    # Verify hooks were called correctly
    assert len(hooks._log_entries) > 0
```

### Testing Hook Chains

```python
import pytest
from my_hooks import ValidationHooks, LoggingHooks, MetricsHooks

@pytest.mark.asyncio
async def test_multiple_hooks_execute():
    """Test multiple hooks execute in sequence."""
    validation_hooks = ValidationHooks()
    logging_hooks = LoggingHooks()
    metrics_hooks = MetricsHooks()

    tool_name = "Bash"
    tool_input = {"command": "ls"}
    tool_output = "file.txt"

    # All hooks should execute
    await validation_hooks.on_pre_tool_use(tool_name, tool_input)
    await logging_hooks.on_pre_tool_use(tool_name, tool_input)
    await metrics_hooks.on_pre_tool_use(tool_name, tool_input)

    await validation_hooks.on_post_tool_use(tool_name, tool_input, tool_output)
    await logging_hooks.on_post_tool_use(tool_name, tool_input, tool_output)
    await metrics_hooks.on_post_tool_use(tool_name, tool_input, tool_output)

    # Verify all hooks executed
    assert len(logging_hooks._log_entries) > 0
    assert metrics_hooks._tool_counts["Bash"] == 1
```

## Security Testing

### Test Secret Sanitization

```python
import pytest
from my_hooks import SecretProtectionHooks

@pytest.mark.asyncio
async def test_api_key_sanitized():
    """Verify API keys are redacted from logs."""
    hooks = SecretProtectionHooks()

    output_with_secret = 'api_key=sk_live_1234567890abcdef'

    await hooks.on_post_tool_use("Bash", {}, output_with_secret)

    # Check log doesn't contain actual key
    log_content = await hooks._get_log_content()
    assert "sk_live_1234567890abcdef" not in log_content
    assert "REDACTED" in log_content

@pytest.mark.asyncio
async def test_password_sanitized():
    """Verify passwords are redacted."""
    hooks = SecretProtectionHooks()

    output = 'password="MySecretPassword123"'

    result = await hooks.on_post_tool_use("Bash", {}, output)

    # If hook modifies output, verify sanitization
    if result:
        assert "MySecretPassword123" not in result
        assert "REDACTED" in result
```

### Test Path Traversal Prevention

```python
import pytest
from pathlib import Path
from my_hooks import PathSecurityHooks

@pytest.mark.asyncio
async def test_path_traversal_blocked():
    """Verify path traversal attempts are blocked."""
    allowed_roots = [Path.home(), Path("/tmp")]
    hooks = PathSecurityHooks(allowed_roots)

    # Test various traversal attempts
    traversal_attempts = [
        "../../etc/passwd",
        "/etc/passwd",
        str(Path.home() / ".." / ".." / "etc" / "passwd"),
    ]

    for attempt in traversal_attempts:
        with pytest.raises(ValueError, match="access denied"):
            await hooks.on_pre_tool_use("Read", {"file_path": attempt})

@pytest.mark.asyncio
async def test_allowed_path_accepted():
    """Verify allowed paths are accepted."""
    allowed_roots = [Path.home()]
    hooks = PathSecurityHooks(allowed_roots)

    safe_path = str(Path.home() / "documents" / "file.txt")

    result = await hooks.on_pre_tool_use("Read", {"file_path": safe_path})
    assert result is None  # Allowed
```

### Test Command Injection Prevention

```python
import pytest
from my_hooks import CommandSanitizationHooks

@pytest.mark.asyncio
async def test_command_injection_blocked():
    """Verify command injection attempts are blocked."""
    hooks = CommandSanitizationHooks()

    injection_attempts = [
        "ls; rm -rf /",
        "ls && cat /etc/passwd",
        "ls || echo 'hacked'",
        "ls `whoami`",
        "ls $(cat /etc/passwd)",
    ]

    for attempt in injection_attempts:
        with pytest.raises(ValueError, match="injection"):
            await hooks.on_pre_tool_use("Bash", {"command": attempt})

@pytest.mark.asyncio
async def test_safe_command_allowed():
    """Verify safe commands are allowed."""
    hooks = CommandSanitizationHooks()

    safe_commands = [
        "ls -la",
        "cat file.txt",
        "grep 'pattern' file.txt",
    ]

    for cmd in safe_commands:
        result = await hooks.on_pre_tool_use("Bash", {"command": cmd})
        assert result is None  # Allowed
```

## Performance Testing

### Test Timing Budgets

```python
import pytest
import time
from my_hooks import ValidationHooks

@pytest.mark.asyncio
async def test_validation_meets_timing_budget():
    """Verify validation completes within timing budget."""
    hooks = ValidationHooks()

    start = time.perf_counter()

    await hooks.on_pre_tool_use("Bash", {"command": "ls -la"})

    duration_ms = (time.perf_counter() - start) * 1000

    # PreToolUse should complete < 100ms
    assert duration_ms < 100, f"Validation too slow: {duration_ms:.2f}ms"

@pytest.mark.asyncio
async def test_logging_meets_timing_budget():
    """Verify logging completes within timing budget."""
    hooks = LoggingHooks()

    start = time.perf_counter()

    await hooks.on_post_tool_use("Bash", {"command": "ls"}, "output")

    duration_ms = (time.perf_counter() - start) * 1000

    # PostToolUse should complete < 500ms
    assert duration_ms < 500, f"Logging too slow: {duration_ms:.2f}ms"
```

### Test Memory Usage

```python
import pytest
import tracemalloc
from my_hooks import BoundedStateHooks

@pytest.mark.asyncio
async def test_memory_bounded():
    """Verify memory usage stays bounded."""
    hooks = BoundedStateHooks(max_history=1000)

    tracemalloc.start()

    # Execute many operations
    for i in range(10000):
        await hooks.on_post_tool_use(f"Tool{i % 10}", {}, f"output{i}")

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory should be bounded (< 10MB for this test)
    assert peak < 10 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.2f}MB"
```

### Benchmark Performance

```python
import pytest
import time
from my_hooks import MyHooks

@pytest.mark.asyncio
async def test_hook_performance_benchmark():
    """Benchmark hook performance."""
    hooks = MyHooks()

    iterations = 1000
    durations = []

    for _ in range(iterations):
        start = time.perf_counter()
        await hooks.on_pre_tool_use("Bash", {"command": "ls"})
        durations.append(time.perf_counter() - start)

    avg_duration_ms = (sum(durations) / len(durations)) * 1000
    p95_duration_ms = sorted(durations)[int(len(durations) * 0.95)] * 1000
    max_duration_ms = max(durations) * 1000

    print(f"\nPerformance Benchmark:")
    print(f"  Average: {avg_duration_ms:.2f}ms")
    print(f"  P95: {p95_duration_ms:.2f}ms")
    print(f"  Max: {max_duration_ms:.2f}ms")

    # Assert performance targets
    assert avg_duration_ms < 50, "Average too slow"
    assert p95_duration_ms < 100, "P95 too slow"
```

## Test Fixtures

### Common Test Fixtures

```python
import pytest
import tempfile
from pathlib import Path
from my_hooks import MyHooks

@pytest.fixture
def temp_log_file():
    """Create temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = Path(f.name)

    yield log_file

    # Cleanup
    if log_file.exists():
        log_file.unlink()

@pytest.fixture
def hooks_with_temp_log(temp_log_file):
    """Create hooks instance with temporary log file."""
    return MyHooks(log_file=temp_log_file)

@pytest.fixture
async def initialized_hooks():
    """Create and initialize hooks instance."""
    hooks = MyHooks()
    await hooks.initialize()

    yield hooks

    await hooks.cleanup()
```

### Mock Fixtures

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_file_system():
    """Mock file system for testing."""
    mock_fs = MagicMock()
    mock_fs.exists.return_value = True
    mock_fs.is_file.return_value = True
    mock_fs.stat.return_value.st_size = 1024
    return mock_fs

@pytest.fixture
def mock_async_logger():
    """Mock async logger for testing."""
    logger = AsyncMock()
    logger.write = AsyncMock()
    logger.flush = AsyncMock()
    return logger
```

## JSON Hook Testing

### Testing Declarative Hooks

For JSON hooks (Claude Code), test the hook scripts directly:

```bash
#!/usr/bin/env bash
# test_hooks.sh - Test JSON hook scripts

set -e

echo "Testing validation hook..."

# Set up environment
export CLAUDE_TOOL_NAME="Bash"
export CLAUDE_TOOL_INPUT='{"command": "rm -rf /"}'

# Run hook script
if ./hooks/scripts/validate.sh; then
    echo "ERROR: Dangerous command should be blocked"
    exit 1
else
    echo "[OK] Dangerous command blocked"
fi

# Test safe command
export CLAUDE_TOOL_INPUT='{"command": "ls -la"}'

if ./hooks/scripts/validate.sh; then
    echo "[OK] Safe command allowed"
else
    echo "ERROR: Safe command should be allowed"
    exit 1
fi

echo "All tests passed!"
```

### Integration Test for JSON Hooks

```python
import pytest
import subprocess
import json
from pathlib import Path

def test_json_hook_validation():
    """Test JSON hook script execution."""
    hook_script = Path("hooks/scripts/validate.sh")

    # Test dangerous command
    env = {
        "CLAUDE_TOOL_NAME": "Bash",
        "CLAUDE_TOOL_INPUT": json.dumps({"command": "rm -rf /"})
    }

    result = subprocess.run(
        [str(hook_script)],
        env=env,
        capture_output=True
    )

    # Should exit with error
    assert result.returncode != 0

    # Test safe command
    env["CLAUDE_TOOL_INPUT"] = json.dumps({"command": "ls -la"})

    result = subprocess.run(
        [str(hook_script)],
        env=env,
        capture_output=True
    )

    # Should succeed
    assert result.returncode == 0
```

## Test Coverage

### Measuring Coverage

```python
# Run tests with coverage
# pytest --cov=my_hooks --cov-report=html tests/

# Coverage targets:
# - Line coverage: > 90%
# - Branch coverage: > 80%
# - Function coverage: 100%
```

### Coverage Configuration

```ini
# .coveragerc or pyproject.toml
[tool.coverage.run]
source = ["my_hooks"]
omit = ["tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Testing Checklist

Before deploying hooks, verify:

- [ ] **Unit Tests**: All hook methods have unit tests
- [ ] **Happy Path**: Normal operations work correctly
- [ ] **Error Cases**: Errors handled gracefully
- [ ] **Edge Cases**: Boundary conditions tested
- [ ] **Security**: Secret sanitization verified
- [ ] **Performance**: Timing budgets met
- [ ] **Memory**: No memory leaks
- [ ] **Integration**: Works with real/mock agent
- [ ] **Coverage**: > 90% line coverage
- [ ] **Documentation**: Tests document expected behavior

## Continuous Testing

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running hook tests..."
pytest tests/test_hooks.py --quiet

if [ $? -ne 0 ]; then
    echo "Hook tests failed. Commit aborted."
    exit 1
fi

echo "[OK] Hook tests passed"
```

### CI/CD Pipeline

```yaml
# .github/workflows/test-hooks.yml
name: Test Hooks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ -v --cov=my_hooks --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Related Modules

- **hook-types.md**: Event types to test
- **sdk-callbacks.md**: Implementation patterns to test
- **security-patterns.md**: Security tests to include
- **performance-guidelines.md**: Performance targets to test
