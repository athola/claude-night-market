# Python Testing

This module covers progressive-loading for skills that read,
generate, or refactor Python tests. The selection question is
which testing-tool modules to load: pytest fixtures, mocking,
async tests, parameterization, coverage, or property-based
testing.

## When This Module Applies

Load this module when the task involves:

- Reading or writing files matching `test_*.py` or `*_test.py`.
- Generating new tests for existing functions.
- Reviewing test quality, coverage, or fixture design.
- Setting up `pyproject.toml` test configuration.

For runtime Python patterns, load `python-patterns.md`. For
packaging concerns including test extras, load
`python-packaging.md`. This module focuses on the test layer.

## Slice the Testing Surface First

Testing modules split by concern. Loading every concern at once
adds 3000+ tokens to a routine test edit.

| Concern | Module | Token Estimate |
|---------|--------|----------------|
| pytest basics | `pytest-basics.md` | 400 |
| Fixtures and scope | `fixture-patterns.md` | 500 |
| Mocking | `mock-patterns.md` | 500 |
| Async tests | `async-test-patterns.md` | 400 |
| Parameterization | `parametrize-patterns.md` | 300 |
| Coverage | `coverage-patterns.md` | 400 |
| Property-based | `hypothesis-patterns.md` | 600 |

The hub picks based on the test file content and the project's
declared test dependencies (`pytest-asyncio`, `pytest-mock`,
`hypothesis`).

## Detect Installed Test Plugins

The plugin set drives module selection. A project without
`pytest-asyncio` cannot use async fixtures even if the source
code is async.

```python
import tomllib
from pathlib import Path


def test_extras(project_root: Path) -> set[str]:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return set()
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    deps = project.get("dependencies", []) + project.get(
        "optional-dependencies", {}
    ).get("dev", []) + project.get("optional-dependencies", {}).get(
        "test", []
    )
    return {dep.split(">=")[0].split("==")[0].strip() for dep in deps}
```

Search the result for `pytest-asyncio`, `pytest-mock`,
`hypothesis`, and friends. Load the matching sub-modules only.

## Concrete Example: Fixture with Scope

The fixture sub-module documents scope choices.

```python
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def shared_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Database path shared across the whole test session."""
    return tmp_path_factory.mktemp("db") / "test.sqlite"


@pytest.fixture
def fresh_db_path(tmp_path: Path) -> Path:
    """Fresh database path per test."""
    return tmp_path / "test.sqlite"
```

`tmp_path` is function-scoped; `tmp_path_factory` is session-
scoped. Mixing scopes causes subtle failures: a session-scoped
fixture cannot depend on a function-scoped one.

## Concrete Example: Parametrize

The parametrize sub-module documents the table-driven pattern.

```python
import pytest


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0", 0),
        ("42", 42),
        ("-1", -1),
        ("0xff", 255),
    ],
    ids=["zero", "positive", "negative", "hex"],
)
def test_parse_int(value: str, expected: int) -> None:
    assert parse_int(value) == expected
```

The `ids` argument controls test names in pytest output. Without
it, pytest generates names from the values, which can produce
unreadable names for complex inputs.

## Concrete Example: Async Test

The async sub-module documents the marker convention.

```python
import asyncio
import pytest


@pytest.mark.asyncio
async def test_concurrent_fetches() -> None:
    results = await asyncio.gather(
        fetch("a"),
        fetch("b"),
    )
    assert len(results) == 2
```

`pytest-asyncio` provides the `asyncio` marker. The default
mode is `strict`, which requires the marker on every async
test. Set `asyncio_mode = "auto"` in `pyproject.toml` to mark
all async functions automatically.

## Concrete Example: pyproject Test Config

The test-config sub-module documents the pytest section.

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "-ra",
]
testpaths = ["tests"]
asyncio_mode = "auto"
```

`--strict-markers` makes typo'd `@pytest.mark.foo` a hard error.
`--strict-config` does the same for unknown options. `-ra`
shows reasons for skipped, expected-fail, and error tests.

## Pitfalls

1. **Loading hypothesis without the dependency**: Generated
   property-based tests fail at import time if `hypothesis` is
   not in the project. Detect dependencies before generating.
2. **Mixing fixture scopes**: A session-scoped fixture cannot
   request a function-scoped one. The fixture module documents
   the scope hierarchy.
3. **Using `unittest.mock` blindly**: `unittest.mock.patch`
   requires the import path of the function as it is used, not
   where it is defined. Mistakes here produce mocks that never
   fire.
4. **Skipping `--strict-markers`**: A typo in
   `@pytest.mark.skipif` becomes a silent no-op without strict
   markers. Always enable.
5. **Async tests without the right marker**: Without
   `pytest-asyncio` and the marker (or `asyncio_mode =
   "auto"`), async test functions are collected but never
   awaited, so they always pass.

## Cross-Reference

See `python-patterns.md` for runtime idioms, `python-packaging.md`
for distribution, and the parent `SKILL.md` for how testing
modules plug into the hub-and-spoke pattern.
