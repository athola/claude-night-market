# Parseltongue

Python development skills for Claude Code. Covers testing, performance profiling, async patterns, and packaging.

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
| **python-testing** | Comprehensive pytest patterns, fixtures, mocking, TDD workflows |
| **python-performance** | CPU/memory profiling, optimization patterns, benchmarking |
| **python-async** | asyncio, concurrent programming, async/await patterns |
| **python-packaging** | Modern pyproject.toml, uv, PyPI publishing |

### Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Analyze test suites for quality and coverage |
| `/run-profiler` | Profile Python code for performance bottlenecks |
| `/check-async` | Validate async code patterns and detect issues |

### Agents

| Agent | Description |
|-------|-------------|
| **python-pro** | Expert Python development with modern 3.12+ features |
| **python-tester** | Specialized testing agent for pytest and TDD |
| **python-optimizer** | Performance profiling and optimization expert |

## Quick Start

### Testing
```python
# Use the testing skill for pytest patterns
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
# Use the performance skill for profiling
# Skill: python-performance

from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_computation(n):
    return sum(i**2 for i in range(n))
```

### Async Programming
```python
# Use the async skill for concurrent patterns
# Skill: python-async

import asyncio

async def fetch_all(urls):
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### Modern Packaging
```toml
# Use the packaging skill for pyproject.toml
# Skill: python-packaging

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
dependencies = ["requests>=2.0.0"]
```

## Ecosystem Integration

All skills integrate with the modern Python ecosystem:

- **Package Manager**: uv (preferred), pip, poetry
- **Linting**: ruff, mypy, pyright
- **Testing**: pytest, pytest-asyncio, hypothesis, pytest-cov
- **Frameworks**: FastAPI, Django, Flask
- **Data**: pandas, SQLAlchemy, pydantic

## Structure

```
parseltongue/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── python-pro.md        # General Python expert
│   ├── python-tester.md     # Testing specialist
│   └── python-optimizer.md  # Performance specialist
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

- Python 3.9+ (3.12+ recommended)
- Claude Code with plugin support
- Optional: uv for package management

## License

MIT
