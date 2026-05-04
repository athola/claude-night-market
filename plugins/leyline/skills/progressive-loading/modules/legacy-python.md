# Legacy Python

This module covers progressive-loading for skills that work with
Python 3.8 through 3.10 codebases. The selection question is
which language-feature modules to load when the runtime predates
features like `match` statements, the `tomllib` standard library
module, exception groups, and PEP 604 union syntax.

## When This Module Applies

Load this module when:

- The target codebase pins `python_requires = ">=3.8,<3.11"`
  in `setup.cfg` or `requires-python = ">=3.8,<3.11"` in
  `pyproject.toml`.
- CI matrices target only 3.8, 3.9, or 3.10.
- The user mentions a specific legacy version constraint.

For Python 3.11+ work, load `modern-python.md` instead. The two
modules are mutually exclusive (see the mutually-exclusive
selection pattern in `selection-strategies.md`).

## Detect the Version Floor

The version floor decides which features are available. Read it
from the project metadata, not from the local interpreter.

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
        major, minor = requires[2:].split(".")[:2]
        return (int(major), int(minor.split(",")[0]))
    return None
```

For projects on Python 3.10 or earlier, replace `tomllib` with
the `tomli` backport. The legacy module should document this
substitution explicitly.

## What Legacy Python Lacks

The module loaded here documents the gaps so generated code
stays valid. The most important gaps:

| Feature | Available From | Legacy Substitute |
|---------|----------------|-------------------|
| `match` statement | 3.10 | `if`/`elif` chains |
| `int \| str` unions | 3.10 | `Union[int, str]` from `typing` |
| `tomllib` stdlib | 3.11 | `tomli` backport |
| `ExceptionGroup` | 3.11 | manual exception aggregation |
| `Self` type | 3.11 | `TypeVar` bound to the class |
| `tomli_w` integration | n/a | use `tomli-w` package |

For 3.8 specifically, `dict[str, int]` PEP 585 syntax requires
`from __future__ import annotations`. Without that import, code
fails at class definition time on 3.8.

## Concrete Example: Type Hints That Work on 3.8

The legacy module shows the patterns that work across all
supported versions.

```python
from __future__ import annotations

from typing import Optional, Union


def first_match(values: list[str], pattern: str) -> Optional[str]:
    return next((v for v in values if pattern in v), None)


def parse_int_or_str(value: Union[int, str]) -> int:
    if isinstance(value, str):
        return int(value)
    return value
```

The `from __future__ import annotations` at module top defers
annotation evaluation to runtime, letting 3.8 parse PEP 585
generic syntax without crashing.

## Concrete Example: tomli Backport

`tomllib` was added in 3.11. Legacy code uses `tomli`.

```python
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pip install tomli

with open("pyproject.toml", "rb") as fp:
    data = tomllib.load(fp)
```

Note that both modules require binary mode. `tomli` is a real
PyPI package maintained by Hugo van Kemenade.

## Pitfalls

1. **Generating `match` for 3.8 targets**: `match` statements
   are a syntax error before 3.10. Test generated code against
   the declared floor.
2. **Forgetting `from __future__ import annotations`**: Without
   it, PEP 585 generics raise `TypeError` at class definition
   time on 3.9 and earlier.
3. **Assuming `tomllib` is always available**: Stdlib `tomllib`
   exists only on 3.11+. Use the conditional import above.
4. **Type hints with `Self`**: `typing.Self` is 3.11+. For
   legacy targets, use a `TypeVar` bound to the class.
5. **Loading both legacy and modern modules**: They contradict
   each other on union syntax and stdlib modules. The
   mutually-exclusive selection pattern enforces a single
   choice.

## Cross-Reference

See `modern-python.md` for the 3.11+ counterpart, and the
parent `SKILL.md` for the mutually-exclusive selection pattern
that picks between them.
