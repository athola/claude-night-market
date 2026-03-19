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

## Imports

- All imports at the top of the file (PLC0415 enforced by ruff)
- Hook files are exempt (they use deferred imports for
  optional deps and Python 3.9 compatibility)
- Only use function-level imports for: try/except ImportError
  guards, dynamic module reloads, or circular import avoidance
  (with a comment explaining why)

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
