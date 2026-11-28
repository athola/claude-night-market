"""Expression classification for the membership-in-loop check (T2).

Decides from an expression or an annotation alone whether a value is a
set, dict or string. Name tracking across a module is in ``_receivers``.
"""

from __future__ import annotations

import ast

from ._helpers import _decorator_name

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
