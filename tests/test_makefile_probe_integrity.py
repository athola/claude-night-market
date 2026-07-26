"""Guard that Makefile ``python -c`` probes reference real code and can fail.

``tests/test_gate_exit_codes.py`` covers checkers whose exit code is
discarded with ``|| true``. This guard covers the shape one level over:
a recipe that *runs Python* to prove something works.

Two defects, both found live in conjure.

The first is a snippet that imports something which does not exist::

    uv run python -c "from tools.delegation_executor import Delegator; ..."

There is no ``tools`` package in conjure. The module is
``scripts/delegation_executor.py``, and ``estimate_tokens`` is a
module-level function there, not a ``Delegator`` method. The target had
never run successfully.

The second is what kept the first invisible. The same broken snippet
appears again in ``demo-delegation``, wrapped like this::

    @uv run python -c "..." 2>/dev/null || echo "  (token estimator not available)"

stderr goes to ``/dev/null``, the ``||`` branch prints a calm sentence,
and the recipe exits 0. The demo reported "Delegation demo complete"
while step 3 had thrown ``ModuleNotFoundError``. The fallback text is
worse than silence: "(token estimator not available)" names a cause that
is false. The estimator was available; the call was wrong.

A probe used as an ``if`` condition is excluded, because there the exit
code is consumed rather than discarded::

    @if python3 -c "import memory_profiler" 2>/dev/null; then ...

That is feature detection for an optional tool, and it is correct.

Scope limit worth stating: the import check is static, so it catches a
wrong module path but not a wrong attribute on a correctly imported
object. ``Delegator().estimate_tokens(...)`` is only caught once the
probe is unmasked and actually runs.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

# ``python -c "..."`` / ``python3 -c "..."``, tolerating backslash escapes so a
# snippet containing \" is captured whole.
SNIPPET_RE = re.compile(r"""python[0-9.]*\s+-c\s+"((?:[^"\\]|\\.)*)\"""")

# Trailing ``|| echo ...`` discards the probe's verdict and substitutes prose.
SWALLOW_RE = re.compile(r"\|\|\s*(echo|true|:)\b")

# ``@if python3 -c "..."; then`` consumes the exit code instead of dropping it.
CONDITION_RE = re.compile(r"^\s*[-@]*\s*if\b")


def _plugin_makefiles() -> list[Path]:
    """Every plugin Makefile in the monorepo."""
    return sorted(PLUGINS_DIR.glob("*/Makefile"))


def _declared_dependencies(plugin: Path) -> set[str]:
    """Distribution names this plugin declares, normalized to module form.

    Covers ``dependencies``, every ``optional-dependencies`` extra, and
    every ``dependency-groups`` group, because plugins here use all three.
    """
    pyproject = plugin / "pyproject.toml"
    if not pyproject.is_file():
        return set()
    try:
        data = tomllib.loads(pyproject.read_text())
    except (OSError, tomllib.TOMLDecodeError):  # pragma: no cover - malformed
        return set()

    specs: list[str] = []
    project = data.get("project", {})
    specs += project.get("dependencies", []) or []
    for extra in (project.get("optional-dependencies", {}) or {}).values():
        specs += extra or []
    for group in (data.get("dependency-groups", {}) or {}).values():
        specs += [g for g in (group or []) if isinstance(g, str)]

    names = set()
    for spec in specs:
        # "pytest-cov>=4.1 ; python_version >= '3.10'" -> "pytest_cov"
        name = re.split(r"[<>=!~;\[\s]", spec, maxsplit=1)[0].strip()
        if name:
            names.add(name.lower().replace("-", "_"))
    return names


def _resolve_first_party(plugin: Path, dotted: str) -> Path | None:
    """Path of a dotted module inside the plugin, or None if absent."""
    parts = dotted.split(".")
    for root in (plugin, plugin / "src"):
        base = root.joinpath(*parts)
        if base.is_dir():
            return base
        module = base.with_suffix(".py")
        if module.is_file():
            return module
    return None


def _top_level_name_exists(module: Path, name: str) -> bool:
    """True if ``name`` is bound anywhere in ``module``.

    Deliberately permissive: ``ast.walk`` also sees names bound inside a
    ``try``/``except ImportError`` fallback, which is exactly how
    ``estimate_tokens`` is defined. A false negative here would be a
    broken build for working code, so the check errs toward accepting.
    """
    target = module / "__init__.py" if module.is_dir() else module
    if not target.is_file():
        return True
    try:
        tree = ast.parse(target.read_text())
    except (OSError, SyntaxError):  # pragma: no cover - unreadable module
        return True
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == name:
                return True
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if any((a.asname or a.name.split(".")[0]) == name for a in node.names):
                return True
        elif isinstance(node, ast.Assign):
            if any(
                isinstance(t, ast.Name) and t.id == name
                for t in ast.walk(node)
                if isinstance(t, ast.Name)
            ):
                return True
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return True
    return False


def _snippets(makefile: Path) -> list[tuple[int, str, str]]:
    """``(line number, raw line, python source)`` for each embedded snippet."""
    found = []
    for number, raw in enumerate(makefile.read_text().splitlines(), start=1):
        for match in SNIPPET_RE.finditer(raw):
            source = match.group(1).replace('\\"', '"').replace("$$", "$")
            found.append((number, raw, source))
    return found


def _imports(source: str) -> list[tuple[str, tuple[str, ...]]]:
    """``(dotted module, imported names)`` pairs, or [] if unparseable.

    Unparseable snippets are skipped rather than failed: a recipe may
    interpolate a Make variable into the Python source, and this guard is
    not a Make expander.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    pairs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = tuple(a.name for a in node.names if a.name != "*")
            pairs.append((node.module, names))
        elif isinstance(node, ast.Import):
            pairs += [(a.name, ()) for a in node.names]
    return pairs


def _unresolved_imports(makefile: Path) -> list[str]:
    """Imports in this Makefile's snippets that point at nothing real."""
    plugin = makefile.parent
    declared = _declared_dependencies(plugin)
    problems = []
    for number, raw, source in _snippets(makefile):
        # ``@if python3 -c "import memory_profiler"; then`` is asking whether
        # an undeclared optional tool is installed. "It resolves to nothing"
        # is the answer the recipe is written to handle, not a defect.
        if CONDITION_RE.match(raw):
            continue
        for dotted, names in _imports(source):
            root = dotted.split(".")[0]
            if root in sys.stdlib_module_names or root in declared:
                continue
            module = _resolve_first_party(plugin, dotted)
            if module is None:
                problems.append(
                    f"  {makefile.name}:{number}: '{dotted}' is neither a "
                    f"declared dependency nor a module in {plugin.name}/"
                )
                continue
            problems += [
                f"  {makefile.name}:{number}: '{dotted}' has no '{name}'"
                for name in names
                if not _top_level_name_exists(module, name)
            ]
    return problems


def _swallowed_probes(makefile: Path) -> list[str]:
    """Snippets whose failure is converted into reassuring prose."""
    problems = []
    for number, raw, source in _snippets(makefile):
        line = raw.rstrip()
        if CONDITION_RE.match(line) or not SWALLOW_RE.search(line):
            continue
        if not _imports(source):
            continue
        problems.append(f"  {makefile.name}:{number}: {source[:70]}")
    return problems


def test_discovery_finds_snippets() -> None:
    """An empty parametrize list would make the gates below vacuously green."""
    total = sum(len(_snippets(m)) for m in _plugin_makefiles())
    assert len(_plugin_makefiles()) > 1
    assert total > 5, f"expected embedded python -c snippets, found {total}"


@pytest.mark.parametrize("makefile", _plugin_makefiles(), ids=lambda p: p.parent.name)
def test_makefile_snippets_import_real_modules(makefile: Path) -> None:
    """A ``python -c`` snippet must import modules and names that exist."""
    problems = _unresolved_imports(makefile)
    assert not problems, (
        f"{makefile.parent.name} runs a python snippet that imports something "
        f"nonexistent:\n" + "\n".join(problems) + "\n"
        "The recipe cannot ever have succeeded. Point it at the real module, "
        "or delete it."
    )


@pytest.mark.parametrize("makefile", _plugin_makefiles(), ids=lambda p: p.parent.name)
def test_import_probes_are_not_swallowed(makefile: Path) -> None:
    """A probe that imports something must let a failed import be seen."""
    problems = _swallowed_probes(makefile)
    assert not problems, (
        f"{makefile.parent.name} runs an import probe and then discards its "
        f"verdict:\n" + "\n".join(problems) + "\n"
        "A failed import prints a calm fallback message and the recipe exits "
        "0, so a broken probe is indistinguishable from a working one. Let "
        "the probe fail, or use it as an 'if' condition where the exit code "
        "is actually consumed."
    )
