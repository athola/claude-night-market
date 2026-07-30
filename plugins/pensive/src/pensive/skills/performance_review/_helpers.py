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


# Common string-returning methods. Conservative list: only methods whose
# return type is unambiguously str across the stdlib (str, pathlib,
# io.IOBase). Not included: split (list), splitlines (list), partition
# (tuple), readlines (list).
_STRING_RETURNING_METHODS: frozenset[str] = frozenset(
    {
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
    }
)


def _classify_rhs_literal(value: ast.expr) -> str | None:
    """Classify literal RHS forms: dict/set/string literals and comprehensions."""
    if isinstance(value, (ast.Dict, ast.DictComp)):
        return "dict"
    if isinstance(value, (ast.Set, ast.SetComp)):
        return "set"
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return "string"
    if isinstance(value, ast.JoinedStr):
        return "string"
    return None


_CONSTRUCTOR_CLASSIFICATIONS: dict[str, str] = {
    "dict": "dict",
    "set": "set",
    "frozenset": "set",
    "str": "string",
}


def _classify_rhs_call(value: ast.expr) -> str | None:
    """Classify RHS forms that call a known constructor or string method."""
    if not isinstance(value, ast.Call):
        return None
    if isinstance(value.func, ast.Name):
        return _CONSTRUCTOR_CLASSIFICATIONS.get(value.func.id)
    if (
        isinstance(value.func, ast.Attribute)
        and value.func.attr in _STRING_RETURNING_METHODS
    ):
        return "string"
    return None


def _classify_rhs(value: ast.expr) -> str | None:
    """Classify an Assign RHS as 'dict', 'set', 'string', or None.

    Used to suppress T2 false positives where the membership test
    target is provably not a list. Conservative: returns None for
    anything indeterminate (Name reference, attribute access, etc.).
    """
    return _classify_rhs_literal(value) or _classify_rhs_call(value)


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
    """Add `name` to `target_set`; return True if it was newly added."""
    if name in target_set:
        return False
    target_set.add(name)
    return True


def _classify_assign_targets(
    value: ast.expr,
    targets: list[ast.expr],
    names: set[str],
    string_iter_names: set[str],
) -> bool:
    """Classify assignment targets from their shared RHS.

    Handles both `ast.Assign` (multiple targets) and `ast.AnnAssign`
    (single target, passed as a one-element list) uniformly. Returns
    True if any target was newly classified.
    """
    cat = _classify_rhs(value)
    yields_strings = _classify_string_iter(value)
    propagate_non_list = isinstance(value, ast.Name) and value.id in names
    propagate_string_iter = (
        isinstance(value, ast.Name) and value.id in string_iter_names
    )

    changed = False
    if cat is not None or propagate_non_list:
        for tgt in targets:
            if isinstance(tgt, ast.Name) and _add_name(tgt.id, names):
                changed = True
    if yields_strings or propagate_string_iter:
        for tgt in targets:
            if isinstance(tgt, ast.Name) and _add_name(tgt.id, string_iter_names):
                changed = True
    return changed


def _classify_function_args(
    node: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]
) -> bool:
    """Add str/bytes-annotated function args to `names`; True if changed."""
    changed = False
    for arg in node.args.args + node.args.kwonlyargs:
        if (
            isinstance(arg.annotation, ast.Name)
            and arg.annotation.id in {"str", "bytes"}
            and _add_name(arg.arg, names)
        ):
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

    # Iterate to a fixed point so chains pick up correctly:
    # `lines = s.split(); for line in lines: ...` -> line classified as str.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if _classify_assign_targets(
                    node.value, node.targets, names, string_iter_names
                ):
                    changed = True
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                if _classify_assign_targets(
                    node.value, [node.target], names, string_iter_names
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
