---
description: Python development best practices
globs: "**/*.py"
---

# Python Standards

## Type Hints

- Use `from __future__ import annotations`
- Prefer `T | None` over `Optional[T]`
- Use `TypeVar` for generics
- Add type hints to all public functions

## Code Style

- ruff for linting (fast, replaces flake8/isort/black)
- mypy for type checking
- 88 character line limit (black default)

## Testing

- pytest with fixtures
- Coverage target: 85%+
- Integration tests in `tests/integration/`
- Use `@pytest.mark.parametrize` over duplicate tests

## Package Management

- uv for dependency management
- pyproject.toml for configuration
- Lock files committed to repo

## Error Handling

- Specific exceptions over generic `Exception`
- Context managers for resources
- Structured logging over print statements
