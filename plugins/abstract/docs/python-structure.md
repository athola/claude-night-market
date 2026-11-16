# Python Project Structure

The abstract plugin keeps its shared Python code in a standard `src/`
layout, installed with `uv`. The module reference, installation steps and
a complete usage example are in
[`src/abstract/README.md`](../src/abstract/README.md). This page records
why the layout is what it is.

## Why the src/ Layout

The `src/` layout is the Python packaging convention (PEP 517/518):

1. **No accidental imports**: an uninstalled package cannot be imported
   from the project root during development.
2. **Tests run against the installed package**, not the source tree.
3. **Tooling expects it**: uv, pip, hatch and mypy find the package
   without `PYTHONPATH` changes.
4. **Clean namespace**: package modules stay out of the project root.

Scripts import shared code as `from abstract.config import ...`, and
`py.typed` (PEP 561) gives mypy the package's type hints.

## References

- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - Build Dependencies](https://peps.python.org/pep-0518/)
- [PEP 561 - Type Hints](https://peps.python.org/pep-0561/)
- [Python Packaging Guide - src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
