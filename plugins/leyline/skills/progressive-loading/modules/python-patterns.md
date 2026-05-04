# Python Patterns

This module covers progressive-loading for skills that read,
generate, or refactor Python source code. The selection question
is which Python idiom modules to load: typing, dataclasses,
context managers, iterators, or async. Each is a distinct slice
that need not load together.

## When This Module Applies

Load this module when the task involves:

- Reading or modifying `.py` files.
- Generating new Python source code.
- Reviewing Python idioms for readability or correctness.
- Refactoring imperative code into more idiomatic forms.

For test-specific patterns, load `python-testing.md`. For
packaging concerns, load `python-packaging.md`. For version
selection between legacy and modern features, see
`legacy-python.md` or `modern-python.md`.

## Slice the Idiom Surface First

A "Python patterns" mega-module would cover everything from
list comprehensions to async context managers. The progressive
load splits by idiom family.

| Family | Module | Token Estimate |
|--------|--------|----------------|
| Type hints | `typing-patterns.md` | 500 |
| Dataclasses | `dataclass-patterns.md` | 400 |
| Context managers | `context-manager-patterns.md` | 300 |
| Iterators and generators | `iterator-patterns.md` | 400 |
| Async (`asyncio`) | `async-patterns.md` | 600 |
| Pathlib | `pathlib-patterns.md` | 200 |

Most tasks need one or two families, not all six. The hub picks
based on the imports and patterns already present in the file
under review.

## Detection by Existing Imports

A fast loader inspects the file's imports to pick the right
sub-modules.

```python
import ast
from pathlib import Path


def detect_idioms(py_path: Path) -> set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    idioms: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "asyncio":
                    idioms.add("async")
                if alias.name == "pathlib":
                    idioms.add("pathlib")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "dataclasses":
                idioms.add("dataclass")
            if node.module == "typing":
                idioms.add("typing")
            if node.module == "contextlib":
                idioms.add("context-manager")
    return idioms
```

The set drives module selection. A file importing only
`pathlib` and `dataclasses` does not need the async sub-module.

## Concrete Example: Pathlib over os.path

The pathlib sub-module documents the most common substitutions
since `os.path` operations have direct `pathlib` equivalents.

```python
from pathlib import Path

# Read a file's text
content = Path("config.toml").read_text(encoding="utf-8")

# Build a path
log_dir = Path.home() / ".local" / "share" / "myapp" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Iterate matching files
for py_file in Path("src").rglob("*.py"):
    print(py_file.relative_to("src"))

# Check existence and type
if log_dir.is_dir():
    pass
```

`Path.read_text` and `Path.write_text` accept `encoding=` and
default to the locale encoding. Always pass `encoding="utf-8"`
for portable behavior.

## Concrete Example: Dataclass with Defaults

The dataclass sub-module documents the field defaults that trip
up most authors.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Config:
    name: str
    tags: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)
    timeout_s: float = 30.0
```

`field(default_factory=list)` is required for mutable defaults.
A bare `tags: list[str] = []` triggers a `ValueError` at class
definition because `dataclass` rejects shared mutable defaults.

`frozen=True` makes instances immutable and hashable. `slots=True`
(Python 3.10+) saves memory and prevents accidental attribute
addition.

## Concrete Example: Context Manager via contextlib

For one-off context managers, `contextlib.contextmanager` is
shorter than a class.

```python
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timed(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")


with timed("step 1"):
    do_work()
```

The `try/finally` around `yield` ensures cleanup runs even when
the wrapped block raises.

## Pitfalls

1. **Mutable default arguments**: `def f(items=[]):` shares the
   list across calls. The dataclass module documents the
   `field(default_factory=...)` fix; for plain functions, use
   `items=None` and assign inside the body.
2. **String paths everywhere**: `os.path.join` produces strings
   that lose type information. Use `Path` and convert to
   string at the boundary only when an external API requires
   it.
3. **Loading async patterns for sync code**: `asyncio` patterns
   add complexity that sync code does not need. Detect
   `asyncio` imports before loading.
4. **Bare `except:`**: Catches `KeyboardInterrupt` and
   `SystemExit`. Use `except Exception:` for broad catches and
   specific exception types when possible.
5. **One mega-module**: 2000 tokens of mixed Python guidance
   forces every Python task to load all of it. Split by family.

## Cross-Reference

See `python-testing.md` for test patterns, `python-packaging.md`
for distribution, and the parent `SKILL.md` for how Python
modules plug into the hub-and-spoke pattern.
