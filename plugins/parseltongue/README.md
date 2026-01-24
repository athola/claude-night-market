# Parseltongue

Python development skills for Claude Code, focusing on testing, performance profiling, async patterns, and packaging.

## Overview

Parseltongue provides specialized patterns for modern Python development. It includes guides for `pytest` and TDD workflows, performance profiling for CPU and memory hotspots, and `asyncio` patterns for concurrent programming. The plugin also supports modern packaging through `pyproject.toml` and `uv`.

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

## Quick Start and Integration

Parseltongue integrates with the standard Python ecosystem, including package managers like `uv`, `pip`, and `poetry`, and linting tools such as `ruff` and `mypy`. It provides implementation patterns for major frameworks like FastAPI and Django, as well as data-heavy libraries like `pandas` and `SQLAlchemy`.

Effective testing in Parseltongue uses `pytest` fixtures and TDD cycles to ensure coverage and reliability. Performance optimization relies on profiling hotspots and using techniques like `lru_cache` for expensive computations. For concurrent tasks, `asyncio` patterns help manage parallel I/O operations without the overhead of threads.

## Structure

```
parseltongue/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   ├── python-pro.md        # General Python assistant
│   ├── python-tester.md     # Testing assistant
│   ├── python-optimizer.md  # Performance assistant
│   └── python-linter.md     # Linting enforcement agent
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
