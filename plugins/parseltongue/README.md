# Parseltongue

Python development skills for Claude Code, focusing on testing, performance profiling, async patterns, and packaging.

## Overview

Parseltongue implements specialized patterns for Python development. It includes structured guides for `pytest` and TDD workflows, profiling methods for identifying CPU and memory hotspots, and `asyncio` patterns for concurrent I/O. The plugin also provides templates for `pyproject.toml` configuration and `uv` dependency management.

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **python-testing** | Pytest patterns, fixtures, mocking, and TDD cycles. |
| **python-performance** | CPU/memory profiling and local benchmarking. |
| **python-async** | asyncio concurrency and async/await patterns. |
| **python-packaging** | pyproject.toml standards and uv integration. |

### Commands

| Command | Description |
|---------|-------------|
| `/analyze-tests` | Reports on test suite coverage and fixture usage. |
| `/run-profiler` | Runs cProfile/memory_profiler on target scripts. |
| `/check-async` | Scans for blocking calls in async functions. |

## Integration

Parseltongue works with standard Python tools:
- **Package Managers**: Native support for `uv`, `pip`, and `poetry`.
- **Quality Tools**: Integration with `ruff` for linting and `mypy` for type checking.
- **Frameworks**: Patterns for FastAPI, Django, and SQLAlchemy applications.

Testing follows a Red-Green-Refactor cycle using `pytest` fixtures. Performance optimization focuses on identifying bottlenecks via line-profiling before applying caches or algorithmic improvements. Async patterns prioritize non-blocking I/O to manage high-concurrency workloads without thread overhead.

## Structure

```
parseltongue/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── python-pro.md        # Python 3.12+ specialist
│   ├── python-tester.md     # Pytest and TDD specialist
│   ├── python-optimizer.md  # Performance tuning
│   └── python-linter.md     # Linting enforcement
├── commands/
│   ├── analyze-tests.md
│   ├── run-profiler.md
│   └── check-async.md
├── skills/
│   ├── python-testing/
│   ├── python-performance/
│   ├── python-async/
│   └── python-packaging/
└── README.md
```

## Requirements

- Python 3.12 or later (supported back to 3.9).
- `uv` recommended for dependency isolation.

## License

MIT
