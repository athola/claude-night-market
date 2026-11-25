"""Receiver classification for the membership-in-loop check (T2).

Collects the names a module binds to a set, dict or string, so that
``x in name`` inside a loop is reported only when ``name`` may be a list.
"""

from __future__ import annotations

import ast
from pathlib import Path

from ._classify import _annotation_is_hashed, _classify_rhs

_STRING_ITER_METHODS: frozenset[str] = frozenset({"split", "splitlines", "rsplit"})


def _classify_string_iter(value: ast.expr) -> bool:
    """True iff value is provably an iterable of string elements."""
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr in _STRING_ITER_METHODS
    ):
        return True
    if isinstance(value, (ast.SetComp, ast.ListComp, ast.GeneratorExp)):
        return _classify_rhs(value.elt) == "string"
    return False


def _iter_yields_string(
    iter_expr: ast.expr,
    string_names: set[str],
    string_iter_names: set[str],
) -> bool:
    """True if iter_expr yields elements that are provably strings.

    Covers: inline `.split()`/`.splitlines()` results; comprehensions
    whose `elt` classifies as string; iteration over a Name that was
    classified as string (iter over a string yields chars) or as
    string-iter (the loop var is each string element).
    """
    if _classify_string_iter(iter_expr):
        return True
    if isinstance(iter_expr, ast.Name):
        if iter_expr.id in string_names:
            return True
        if iter_expr.id in string_iter_names:
            return True
    return False


def _add_name(name: str, target_set: set[str]) -> bool:
    """Add `name` to `target_set` and return True if it was newly added."""
    if name in target_set:
        return False
    target_set.add(name)
    return True


def _is_non_list_value(
    value: ast.expr, names: set[str], hashed_calls: frozenset[str]
) -> bool:
    """True when ``value`` is provably a set, dict or string.

    Beyond the literal and constructor forms: a name already classified,
    a call to a function of this module annotated to return one, and a
    conditional whose arms are each one of these or ``None``.
    """
    if _classify_rhs(value) is not None:
        return True
    if isinstance(value, ast.Name):
        return value.id in names
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        return value.func.id in hashed_calls
    if isinstance(value, ast.IfExp):
        arms = (value.body, value.orelse)
        is_none = [isinstance(a, ast.Constant) and a.value is None for a in arms]
        return not all(is_none) and all(
            none or _is_non_list_value(arm, names, hashed_calls)
            for arm, none in zip(arms, is_none)
        )
    return False


def _hashed_return_functions(tree: ast.AST) -> frozenset[str]:
    """Functions in this module whose return annotation is a hashed container."""
    return frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _annotation_is_hashed(node.returns)
    )


def _add_names(new_names: list[str], target_set: set[str]) -> bool:
    """Add every name, and return True if any was new."""
    added = False
    for name in new_names:
        added = _add_name(name, target_set) or added
    return added


def _classify_assign_targets(
    value: ast.expr,
    targets: list[ast.expr],
    names: set[str],
    string_iter_names: set[str],
    hashed_calls: frozenset[str] = frozenset(),
) -> bool:
    """Classify assignment targets from their shared RHS.

    Handles both `ast.Assign` (multiple targets) and `ast.AnnAssign`
    (single target, passed as a one-element list) uniformly, and pairs
    `a, b = x, y` element by element. Returns True if any target was
    newly classified.
    """
    changed = False
    for tgt in targets:
        if (
            isinstance(tgt, ast.Tuple)
            and isinstance(value, ast.Tuple)
            and len(tgt.elts) == len(value.elts)
        ):
            for sub_target, sub_value in zip(tgt.elts, value.elts):
                if _classify_assign_targets(
                    sub_value, [sub_target], names, string_iter_names, hashed_calls
                ):
                    changed = True
    name_targets = [t.id for t in targets if isinstance(t, ast.Name)]
    if _is_non_list_value(value, names, hashed_calls):
        changed = _add_names(name_targets, names) or changed
    yields_strings = _classify_string_iter(value) or (
        isinstance(value, ast.Name) and value.id in string_iter_names
    )
    if yields_strings:
        changed = _add_names(name_targets, string_iter_names) or changed
    return changed


def _classify_function_args(
    node: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]
) -> bool:
    """Add args annotated as a set, dict, str or bytes to `names`."""
    changed = False
    for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
        if _annotation_is_hashed(arg.annotation) and _add_name(arg.arg, names):
            changed = True
    return changed


def _classify_loop_target(
    node: ast.For | ast.AsyncFor | ast.comprehension,
    names: set[str],
    string_iter_names: set[str],
) -> bool:
    """Classify a for-loop/comprehension target from its iterable.

    Shared by `ast.For`/`ast.AsyncFor` and the `for X in Y` clause of a
    SetComp/ListComp/DictComp/GeneratorExp: if Y yields strings, X is a
    string.
    """
    return (
        _iter_yields_string(node.iter, names, string_iter_names)
        and isinstance(node.target, ast.Name)
        and _add_name(node.target.id, names)
    )


def _module_level_non_list_names(module: ast.Module) -> set[str]:
    """Top-level names a module binds to a set, dict or string."""
    names: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.Assign) and _classify_rhs(node.value) is not None:
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            hashed_value = node.value is not None and _classify_rhs(node.value)
            if _annotation_is_hashed(node.annotation) or hashed_value:
                names.add(node.target.id)
    return names


def _imported_module_path(node: ast.ImportFrom, file_path: str) -> Path | None:
    """The source file an import names, when it sits beside the importer.

    ``from .models import X`` resolves through the package directory and
    ``from models import X`` through the importer's own directory, which
    is where a script run by path finds it. Anything else is not followed.
    """
    if not node.module:
        return None
    base = Path(file_path).parent
    for _ in range(max(node.level - 1, 0)):
        base = base.parent
    candidate = base.joinpath(*node.module.split(".")).with_suffix(".py")
    return candidate if candidate.is_file() else None


def _imported_non_list_names(tree: ast.AST, file_path: str) -> set[str]:
    """Names imported from a sibling module that binds them to a set or dict."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        source = _imported_module_path(node, file_path)
        if source is None:
            continue
        try:
            module = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            continue  # an unreadable sibling only costs the suppression
        hashed = _module_level_non_list_names(module)
        names.update(
            alias.asname or alias.name for alias in node.names if alias.name in hashed
        )
    return names


def _collect_non_list_names(tree: ast.AST, file_path: str | None = None) -> set[str]:
    """Pre-pass: gather Names provably bound to non-list values.

    Sources, processed iteratively to a fixed point:
    - Assignments whose RHS classifies as dict/set/string.
    - Function args annotated `str` or `bytes`.
    - For-loop / async-for loop iter vars whose `iter` expression
      yields string elements (e.g. `lines = s.split(); for line in
      lines:` adds `line`).
    - Names annotated as a set, dict or string, whatever the RHS.
    - Names imported from a sibling module that binds them at top level
      to a set, dict or string, when ``file_path`` is given.

    Scope is intentionally coarse (module-wide). False-positive cost
    dominates the rare cross-scope reassignment case.
    """
    names: set[str] = _imported_non_list_names(tree, file_path) if file_path else set()
    hashed_calls = _hashed_return_functions(tree)
    # Names whose VALUE is iterable of strings (e.g. `.split()` result).
    # Tracked separately because they ARE lists (so don't suppress T2
    # when the RHS in a Compare IS this name) but iterating over them
    # yields strings (so iter-vars get classified).
    string_iter_names: set[str] = set()

    # Iterate to a fixed point so chains pick up correctly:
    # `lines = s.split(); for line in lines: ...` -> line classified as str.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if _classify_assign_targets(
                    node.value, node.targets, names, string_iter_names, hashed_calls
                ):
                    changed = True
            elif isinstance(node, ast.AnnAssign):
                if (
                    _annotation_is_hashed(node.annotation)
                    and isinstance(node.target, ast.Name)
                    and _add_name(node.target.id, names)
                ):
                    changed = True
                if node.value is not None and _classify_assign_targets(
                    node.value, [node.target], names, string_iter_names, hashed_calls
                ):
                    changed = True
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _classify_function_args(node, names):
                    changed = True
            elif isinstance(
                node, (ast.For, ast.AsyncFor, ast.comprehension)
            ) and _classify_loop_target(node, names, string_iter_names):
                changed = True
    return names
