"""Receiver classification for the membership-in-loop check (T2).

Collects the names a module binds to a set, dict or string, so that
``x in name`` inside a loop is reported only when ``name`` may be a list.
"""

from __future__ import annotations

import ast
from pathlib import Path

from ._helpers import _decorator_name

_STRING_ITER_METHODS: frozenset[str] = frozenset({"split", "splitlines", "rsplit"})


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


# Operators a list does not support: on a list operand they raise, so a
# result that is later searched with `in` is a set (or a dict, for `|`).
_SET_ALGEBRA_OPS = (ast.BitOr, ast.BitAnd, ast.Sub, ast.BitXor)


def _classify_rhs_fallback(value: ast.expr) -> str | None:
    """Classify set algebra and an expression whose fallback names its type.

    ``loaded or {}`` and ``mapping.get(key, set())`` say what the value is
    meant to be through the empty value they fall back to.
    """
    if isinstance(value, ast.BinOp) and isinstance(value.op, _SET_ALGEBRA_OPS):
        return "set"
    if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.Or):
        return _classify_rhs(value.values[-1])
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "get"
        and len(value.args) == 2  # noqa: PLR2004 - key and default
    ):
        return _classify_rhs(value.args[1])
    return None


def _classify_rhs(value: ast.expr) -> str | None:
    """Classify an Assign RHS as 'dict', 'set', 'string', or None.

    Used to suppress T2 false positives where the membership test
    target is provably not a list. Conservative: returns None for
    anything indeterminate (Name reference, attribute access, etc.).
    """
    return (
        _classify_rhs_literal(value)
        or _classify_rhs_call(value)
        or _classify_rhs_fallback(value)
    )


# Annotation heads whose values answer `in` without a linear scan, or
# (str, bytes) by substring search. Compared after dropping a module prefix.
_HASHED_ANNOTATIONS: frozenset[str] = frozenset(
    {
        "set",
        "frozenset",
        "dict",
        "Set",
        "FrozenSet",
        "Dict",
        "AbstractSet",
        "MutableSet",
        "Mapping",
        "MutableMapping",
        "Counter",
        "defaultdict",
        "OrderedDict",
        "str",
        "bytes",
    }
)


def _constant_annotation_is_hashed(annotation: ast.Constant) -> bool:
    """``None`` is an allowed arm, and a string is a forward reference."""
    if annotation.value is None:
        return True
    if not isinstance(annotation.value, str):
        return False
    try:
        parsed = ast.parse(annotation.value, mode="eval").body
    except SyntaxError:
        return False
    return _annotation_is_hashed(parsed)


def _annotation_is_hashed(annotation: ast.expr | None) -> bool:
    """True when every non-None arm of the annotation is a hashed container."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant):
        return _constant_annotation_is_hashed(annotation)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        arms = (annotation.left, annotation.right)
        return all(_annotation_is_hashed(arm) for arm in arms) and not all(
            isinstance(arm, ast.Constant) for arm in arms
        )
    target = annotation
    if isinstance(annotation, ast.Subscript):
        if _decorator_name(annotation.value).rsplit(".", 1)[-1] == "Optional":
            return _annotation_is_hashed(annotation.slice)
        target = annotation.value
    return _decorator_name(target).rsplit(".", 1)[-1] in _HASHED_ANNOTATIONS


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
            elif isinstance(node, ast.AnnAssign):
                if (
                    _annotation_is_hashed(node.annotation)
                    and isinstance(node.target, ast.Name)
                    and _add_name(node.target.id, names)
                ):
                    changed = True
                if node.value is not None and _classify_assign_targets(
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
