# Modern Python

This module covers progressive-loading for skills targeting
Python 3.11 or later. The selection question is which
language-feature modules to load when the runtime supports
`match` statements, `tomllib` in the standard library, exception
groups, the `Self` type, and PEP 604 union syntax without
backports.

## When This Module Applies

Load this module when:

- The target codebase pins `requires-python = ">=3.11"` in
  `pyproject.toml`.
- CI matrices include 3.11, 3.12, or 3.13 only.
- The user explicitly requests modern Python features.

For Python 3.8-3.10 work, load `legacy-python.md` instead. The
two modules contradict each other on syntax and stdlib
availability, so the mutually-exclusive selection pattern in
`selection-strategies.md` enforces a single choice.

## Detect the Version Floor

Read the version constraint from the project metadata. The
local interpreter version is irrelevant if the project must
support older versions.

```python
import tomllib
from pathlib import Path

def python_floor(project_root: Path) -> tuple[int, int] | None:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    requires = data.get("project", {}).get("requires-python", "")
    if requires.startswith(">="):
        spec = requires[2:].split(",")[0]
        major, minor = spec.split(".")[:2]
        return (int(major), int(minor))
    return None
```

`tomllib` is available without backport on 3.11+, which is one
reason this module assumes the modern floor.

## Features Available on 3.11+

The module loaded here documents the features that justify the
modern floor.

| Feature | Available From | Use Case |
|---------|----------------|----------|
| `match` statement | 3.10 | Multi-way dispatch on shape |
| `int \| str` unions | 3.10 | Inline type unions |
| `tomllib` stdlib | 3.11 | Parse TOML without `tomli` |
| `ExceptionGroup` | 3.11 | Aggregate concurrent failures |
| `Self` type | 3.11 | Annotate methods returning `self` |
| `LiteralString` | 3.11 | SQL-injection-resistant types |
| Improved error locations | 3.11 | Per-character traceback markers |
| `tomllib.loads` | 3.11 | String-mode TOML parsing |

3.12 adds the `type` statement (PEP 695 type aliases) and
per-interpreter GIL support. 3.13 adds the experimental
free-threaded build.

## Concrete Example: Match on Shape

`match` statements replace verbose `isinstance` chains.

```python
from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float


def describe(value: object) -> str:
    match value:
        case Point(x=0, y=0):
            return "origin"
        case Point(x=0, y=y):
            return f"on y-axis at {y}"
        case Point(x=x, y=0):
            return f"on x-axis at {x}"
        case Point():
            return "off-axis point"
        case [first, *rest]:
            return f"sequence starting with {first!r}"
        case _:
            return "unknown"
```

Class patterns (`Point(x=0, y=0)`) require the dataclass to
declare `__match_args__`, which `@dataclass` does automatically.

## Concrete Example: Self Type

`typing.Self` removes the boilerplate of class-bound `TypeVar`s.

```python
from typing import Self


class Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, part: str) -> Self:
        self.parts.append(part)
        return self

    def build(self) -> str:
        return " ".join(self.parts)
```

Subclasses of `Builder` get the correct return type from `add`
without redeclaring it.

## Concrete Example: Exception Groups

`ExceptionGroup` aggregates multiple failures from concurrent
work without losing any of them.

```python
def collect_failures(tasks: list[callable]) -> None:
    errors: list[Exception] = []
    for task in tasks:
        try:
            task()
        except Exception as exc:
            errors.append(exc)
    if errors:
        raise ExceptionGroup("task failures", errors)
```

Callers catch with `except* ValueError as eg:` to filter by
exception type while preserving the group structure.

## Pitfalls

1. **Using `match` on 3.9 targets**: `match` is 3.10+. Skills
   generating code for older floors must load `legacy-python.md`
   and use `if`/`elif` chains instead.
2. **Assuming `tomllib` on every Python**: It is 3.11+ only.
   Verify the floor before importing.
3. **Class patterns on non-dataclass classes**: Class patterns
   need `__match_args__`. Plain classes without this attribute
   match by keyword only.
4. **`Self` without inheritance**: `Self` is meaningful for
   subclassing. For final classes, the explicit class name in
   the annotation is equally clear.
5. **Loading both legacy and modern modules**: They contradict
   each other on union syntax and stdlib modules. The
   mutually-exclusive selection pattern enforces a single choice.

## Cross-Reference

See `legacy-python.md` for the 3.8-3.10 counterpart, and the
parent `SKILL.md` for the mutually-exclusive selection pattern
that picks between them.
