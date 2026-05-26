"""Helper functions and constants for performance_review.

Module-level utilities used by _PerfVisitor. Split out so
_visitor.py can import them without a circular dependency.
"""

from __future__ import annotations

import ast

_MEMOIZATION_DECORATORS: frozenset[str] = frozenset(
    {
        "lru_cache",
        "cache",
        "functools.lru_cache",
        "functools.cache",
        "memoize",
    }
)

_REDUCER_FUNCTIONS: frozenset[str] = frozenset(
    {"sum", "max", "min", "any", "all", "sorted", "set", "frozenset"}
)

_STRING_ITER_METHODS: frozenset[str] = frozenset({"split", "splitlines", "rsplit"})


def _decorator_name(decorator: ast.expr) -> str:
    """Return a string form of a decorator expression for matching."""
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        parts: list[str] = []
        node: ast.expr = decorator
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return ""


def _is_memoized(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function carries a known memoization decorator."""
    for dec in func.decorator_list:
        name = _decorator_name(dec)
        if name in _MEMOIZATION_DECORATORS:
            return True
    return False


def _has_self_call(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if the function body contains a Call to its own name."""
    target = func.name
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            callee = node.func
            if isinstance(callee, ast.Name) and callee.id == target:
                return True
    return False


def _iter_name(for_node: ast.For) -> str | None:
    """Return the iterable's Name id when `for x in <Name>:`, else None."""
    if isinstance(for_node.iter, ast.Name):
        return for_node.iter.id
    return None


def _classify_rhs(value: ast.expr) -> str | None:
    """Classify an Assign RHS as 'dict', 'set', 'string', or None.

    Used to suppress T2 false positives where the membership test
    target is provably not a list. Conservative: returns None for
    anything indeterminate (Name reference, attribute access, etc.).
    """
    if isinstance(value, (ast.Dict, ast.DictComp)):
        return "dict"
    if isinstance(value, (ast.Set, ast.SetComp)):
        return "set"
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return "string"
    if isinstance(value, ast.JoinedStr):
        return "string"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        if value.func.id == "dict":
            return "dict"
        if value.func.id in {"set", "frozenset"}:
            return "set"
        if value.func.id == "str":
            return "string"
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        # Common string-returning methods. Conservative list: only
        # methods whose return type is unambiguously str across the
        # stdlib (str, pathlib, io.IOBase). Not included: split (list),
        # splitlines (list), partition (tuple), readlines (list).
        if value.func.attr in {
            "lower",
            "upper",
            "strip",
            "lstrip",
            "rstrip",
            "title",
            "casefold",
            "swapcase",
            "capitalize",
            "replace",
            "format",
            "join",
            "encode",
            "decode",
            "read",
            "readline",
            "read_text",
        }:
            return "string"
    return None


def _classify_string_iter(value: ast.expr) -> bool:
    """True iff value is provably an iterable of string elements."""
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        if value.func.attr in _STRING_ITER_METHODS:
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


def _collect_non_list_names(tree: ast.AST) -> set[str]:
    """Pre-pass: gather Names provably bound to non-list values.

    Sources, processed iteratively to a fixed point:
    - Assignments whose RHS classifies as dict/set/string.
    - Function args annotated `str` or `bytes`.
    - For-loop / async-for loop iter vars whose `iter` expression
      yields string elements (e.g. `lines = s.split(); for line in
      lines:` adds `line`).

    Scope is intentionally coarse (module-wide). False-positive cost
    dominates the rare cross-scope reassignment case.
    """
    names: set[str] = set()
    # Names whose VALUE is iterable of strings (e.g. `.split()` result).
    # Tracked separately because they ARE lists (so don't suppress T2
    # when the RHS in a Compare IS this name) but iterating over them
    # yields strings (so iter-vars get classified).
    string_iter_names: set[str] = set()

    def _add(name: str) -> bool:
        if name in names:
            return False
        names.add(name)
        return True

    def _add_iter(name: str) -> bool:
        if name in string_iter_names:
            return False
        string_iter_names.add(name)
        return True

    # Iterate to a fixed point so chains pick up correctly:
    # `lines = s.split(); for line in lines: ...` -> line classified as str.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                cat = _classify_rhs(node.value)
                yields_strings = _classify_string_iter(node.value)
                propagate_non_list = (
                    isinstance(node.value, ast.Name) and node.value.id in names
                )
                propagate_string_iter = (
                    isinstance(node.value, ast.Name)
                    and node.value.id in string_iter_names
                )
                if cat is not None or propagate_non_list:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and _add(tgt.id):
                            changed = True
                if yields_strings or propagate_string_iter:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and _add_iter(tgt.id):
                            changed = True
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                cat = _classify_rhs(node.value)
                yields_strings = _classify_string_iter(node.value)
                propagate_non_list = (
                    isinstance(node.value, ast.Name) and node.value.id in names
                )
                propagate_string_iter = (
                    isinstance(node.value, ast.Name)
                    and node.value.id in string_iter_names
                )
                if cat is not None or propagate_non_list:
                    if isinstance(node.target, ast.Name) and _add(node.target.id):
                        changed = True
                if yields_strings or propagate_string_iter:
                    if isinstance(node.target, ast.Name) and _add_iter(node.target.id):
                        changed = True
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args + node.args.kwonlyargs:
                    if (
                        isinstance(arg.annotation, ast.Name)
                        and arg.annotation.id in {"str", "bytes"}
                        and _add(arg.arg)
                    ):
                        changed = True
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                if (
                    _iter_yields_string(node.iter, names, string_iter_names)
                    and isinstance(node.target, ast.Name)
                    and _add(node.target.id)
                ):
                    changed = True
            elif isinstance(node, ast.comprehension):
                # `for X in Y` clause inside a SetComp/ListComp/DictComp/
                # GeneratorExp. Same iter-var classification as a regular
                # For: if Y yields strings, X is a string.
                if (
                    _iter_yields_string(node.iter, names, string_iter_names)
                    and isinstance(node.target, ast.Name)
                    and _add(node.target.id)
                ):
                    changed = True
    return names
