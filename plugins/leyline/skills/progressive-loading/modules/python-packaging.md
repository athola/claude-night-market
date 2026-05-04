# Python Packaging

This module covers progressive-loading for skills that work with
Python package authoring and distribution: `pyproject.toml`
authoring, build backend selection, entry points, dependency
declaration, lockfile management, and PyPI publishing.

## When This Module Applies

Load this module when the task touches:

- A `pyproject.toml`, `setup.py`, or `setup.cfg` file.
- Tool configuration tables: `[tool.uv]`, `[tool.hatch]`,
  `[tool.poetry]`, `[tool.ruff]`, `[tool.pytest.ini_options]`.
- Console scripts or entry points (`[project.scripts]`).
- A `uv.lock`, `poetry.lock`, or `requirements*.txt` file.
- A PyPI publishing task or release pipeline.

For runtime Python idioms, load `python-patterns.md`. For tests,
load `python-testing.md`. This module focuses on the packaging
boundary.

## Detect the Build Backend First

The build backend in `pyproject.toml` decides which tool
sub-module to load. Different backends have different config
shapes.

```python
import tomllib
from pathlib import Path


def detect_backend(project_root: Path) -> str:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return "none"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    backend = data.get("build-system", {}).get("build-backend", "")
    if "hatchling" in backend:
        return "hatch"
    if "poetry" in backend:
        return "poetry"
    if "setuptools" in backend:
        return "setuptools"
    if "flit" in backend:
        return "flit"
    if "pdm" in backend:
        return "pdm"
    return "unknown"
```

The result drives which detail module loads next: hatch projects
need `[tool.hatch.build.targets.wheel]` guidance, poetry projects
need `[tool.poetry.dependencies]` guidance, and so on.

## Loading Map

| Backend | Detail Module | Token Estimate |
|---------|---------------|----------------|
| Hatch | `hatch-config.md` | 400 |
| Poetry | `poetry-config.md` | 500 |
| Setuptools | `setuptools-config.md` | 500 |
| PDM | `pdm-config.md` | 400 |
| Flit | `flit-config.md` | 300 |

The shared metadata module covers `[project]` table fields
common across PEP 621-compliant backends. Keep it always loaded
because every modern project uses it.

## Concrete Example: Minimal pyproject.toml

The shared module documents the PEP 621 metadata that works
across backends.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "0.1.0"
description = "Short one-line description"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.4.0",
]

[project.scripts]
myapp = "myapp.cli:main"
```

The `[project.scripts]` table generates console scripts at
install time. The `myapp` command will invoke `myapp.cli.main`.

## Lockfile Strategy

Lockfile choice depends on the resolver. The lockfile sub-module
documents each.

| Tool | Lockfile | Generation Command |
|------|----------|--------------------|
| uv | `uv.lock` | `uv lock` |
| poetry | `poetry.lock` | `poetry lock` |
| pdm | `pdm.lock` | `pdm lock` |
| pip-tools | `requirements.txt` | `pip-compile requirements.in` |

`uv` is fast enough to be a drop-in resolver for pip-based
projects. The uv sub-module documents `uv pip compile` as a
pip-tools-compatible command.

## Publishing

For PyPI publishing, the publish sub-module documents the
two-stage workflow: build, then upload.

```bash
# Build artifacts (works with any PEP 517 backend)
python -m build

# Upload via twine (or backend-native command)
twine upload dist/*
twine upload --repository testpypi dist/*  # test first
```

`python -m build` is the official PyPA build front-end and works
with hatch, poetry, setuptools, flit, and pdm backends.

## Pitfalls

1. **Editing `setup.py` when `pyproject.toml` exists**: Modern
   projects declare metadata in `pyproject.toml`. Editing both
   is a source of drift.
2. **Loading the wrong backend module**: A Hatch project does
   not have `[tool.poetry]` tables. Detect the backend first.
3. **Skipping the version floor**: `requires-python` controls
   which features the package can use. Generated code that
   targets newer features than the floor breaks installs.
4. **Hand-editing lockfiles**: Lockfiles are generated. Edits
   break the resolver. Re-run the lock command instead.
5. **Uploading to PyPI without testing**: Always upload to
   TestPyPI first to verify the package installs cleanly before
   publishing the real version.

## Cross-Reference

See `python-patterns.md` for runtime idioms, `python-testing.md`
for test setup, and the parent `SKILL.md` for how packaging
modules plug into the hub-and-spoke pattern.
