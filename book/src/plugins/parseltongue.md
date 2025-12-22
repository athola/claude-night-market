# parseltongue

Modern Python development suite for testing, performance, async patterns, and packaging.

## Overview

Parseltongue brings Python 3.12+ best practices to your workflow. It covers the full development lifecycle: testing with pytest, performance optimization, async patterns, and modern packaging with uv.

## Installation

```bash
/plugin install parseltongue@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `python-testing` | Pytest and TDD workflows | Writing and running tests |
| `python-performance` | Profiling and optimization | Debugging slow code |
| `python-async` | Async programming patterns | Implementing asyncio |
| `python-packaging` | Modern packaging with uv | Managing pyproject.toml |

## Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Report on test suite health |
| `/run-profiler` | Profile code execution |
| `/check-async` | Validate async patterns |

## Agents

| Agent | Description |
|-------|-------------|
| `python-pro` | Master Python 3.12+ with modern features |
| `python-tester` | Expert testing for pytest, TDD, mocking |
| `python-optimizer` | Expert performance optimization |

## Usage Examples

### Test Analysis

```bash
/analyze-tests

# Reports:
# - Coverage metrics
# - Test distribution
# - Slow tests
# - Missing coverage areas
# - Anti-patterns detected
```

### Profiling

```bash
/run-profiler src/heavy_function.py

# Outputs:
# - CPU time breakdown
# - Memory usage
# - Hot paths
# - Optimization suggestions
```

### Async Validation

```bash
/check-async src/async_module.py

# Checks:
# - Proper await usage
# - Event loop handling
# - Async context managers
# - Concurrency patterns
```

### Skill Invocation

```bash
Skill(parseltongue:python-testing)

# Provides:
# - Pytest configuration patterns
# - TDD workflow guidance
# - Mocking strategies
# - Fixture patterns
```

## Python 3.12+ Features

Parseltongue emphasizes modern Python:

### Type Hints

```python
# Modern syntax (3.10+)
def process(data: list[str] | None) -> dict[str, int]:
    ...
```

### Pattern Matching

```python
# Structural pattern matching (3.10+)
match response:
    case {"status": "ok", "data": data}:
        return data
    case {"status": "error", "message": msg}:
        raise ValueError(msg)
```

### Exception Groups

```python
# Exception groups (3.11+)
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task1())
        tg.create_task(task2())
except* ValueError as eg:
    for exc in eg.exceptions:
        handle(exc)
```

## Testing Patterns

### TDD Workflow

```bash
Skill(parseltongue:python-testing)

# RED-GREEN-REFACTOR:
# 1. Write failing test
# 2. Implement minimal code
# 3. Refactor with tests green
```

### Fixture Patterns

```python
# Recommended patterns
@pytest.fixture
def db_session(tmp_path):
    """Session-scoped database fixture."""
    db = Database(tmp_path / "test.db")
    yield db
    db.close()

@pytest.fixture
def user(db_session):
    """User fixture depending on db."""
    return db_session.create_user("test")
```

### Mocking Strategies

```python
# Strategic mocking
def test_api_call(mocker):
    mock_response = mocker.patch("requests.get")
    mock_response.return_value.json.return_value = {"status": "ok"}

    result = fetch_data()

    assert result["status"] == "ok"
```

## Performance Optimization

### Profiling Tools

```python
# cProfile integration
python -m cProfile -s cumtime script.py

# Memory profiling
from memory_profiler import profile

@profile
def memory_heavy():
    ...
```

### Optimization Patterns

- **Generators over lists**: Save memory
- **Local variables**: Faster lookup
- **Built-in functions**: C-optimized
- **Lazy evaluation**: Defer computation

## Async Patterns

### Recommended Structure

```python
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results

if __name__ == "__main__":
    asyncio.run(main())
```

### Anti-Patterns to Avoid

- Blocking calls in async functions
- Creating event loops inside coroutines
- Ignoring exceptions in fire-and-forget tasks

## Packaging with uv

### pyproject.toml

```toml
[project]
name = "my-package"
version = "1.0.0"
dependencies = ["requests>=2.28"]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.uv]
index-url = "https://pypi.org/simple"
```

### Commands

```bash
# Install with uv
uv pip install -e ".[dev]"

# Lock dependencies
uv pip compile pyproject.toml -o requirements.lock

# Sync environment
uv pip sync requirements.lock
```

## Superpowers Integration

| Skill | Enhancement |
|-------|-------------|
| `python-testing` | Uses `test-driven-development` for TDD cycles |
| `python-testing` | Uses `testing-anti-patterns` for detection |

## Related Plugins

- **leyline**: Provides pytest-config patterns
- **sanctum**: Test updates integrate with test-updates skill
