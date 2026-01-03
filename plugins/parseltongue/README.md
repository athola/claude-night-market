# Parseltongue

Python development skills for Claude Code. Supports testing, performance profiling, async patterns, and packaging.

## Installation

Add to your Claude Code plugins:
```bash
claude plugins install parseltongue
```

Or reference directly from the marketplace:
```json
{
  "plugins": ["parseltongue@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **python-testing** | Pytest patterns, fixtures, mocking, and TDD workflows. |
| **python-performance** | CPU and memory profiling, optimization, and benchmarking. |
| **python-async** | asyncio, concurrent programming, and async/await patterns. |
| **python-packaging** | Modern pyproject.toml, uv, and PyPI publishing. |

### Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Analyze test suites for quality and coverage. |
| `/run-profiler` | Profile Python code for performance bottlenecks. |
| `/check-async` | Validate async code patterns and detect issues. |

### Agents

| Agent | Description |
|-------|-------------|
| **python-pro** | Python development assistant for modern features. |
| **python-tester** | Testing assistant for pytest and TDD. |
| **python-optimizer** | Performance profiling and optimization assistant. |

## Quick Start

### Testing
```python
# Skill: python-testing

import pytest

@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.close()

def test_user_creation(db_session):
    user = User.create("test@example.com")
    assert user.is_valid()
```

### Performance Optimization
```python
# Skill: python-performance

from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_computation(n):
    return sum(i**2 for i in range(n))
```

### Async Programming
```python
# Skill: python-async

import asyncio

async def fetch_all(urls):
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### Modern Packaging
```toml
# Skill: python-packaging

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
dependencies = ["requests>=2.0.0"]
```

## Integration

Parseltongue integrates with these tools:

- **Package Managers**: uv, pip, poetry.
- **Linting**: ruff, mypy, pyright.
- **Testing**: pytest, pytest-asyncio, hypothesis, pytest-cov.
- **Frameworks**: FastAPI, Django, Flask.
- **Data**: pandas, SQLAlchemy, pydantic.

## Structure

```
parseltongue/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── python-pro.md        # General Python assistant
│   ├── python-tester.md     # Testing assistant
│   └── python-optimizer.md  # Performance assistant
├── commands/
│   ├── analyze-tests.md     # Test analysis command
│   ├── run-profiler.md      # Profiler command
│   └── check-async.md       # Async checker command
├── skills/
│   ├── python-testing/      # Testing patterns
│   │   └── SKILL.md
│   ├── python-performance/  # Performance optimization
│   │   └── SKILL.md
│   ├── python-async/        # Async programming
│   │   └── SKILL.md
│   └── python-packaging/    # Modern packaging
│       └── SKILL.md
└── README.md
```

## Requirements

- Python 3.9+ (3.12+ recommended).
- Claude Code with plugin support.
- Optional: uv for package management.

## License

MIT
