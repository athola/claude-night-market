"""Compatibility checker skill for parseltongue."""

from __future__ import annotations

import ast
import re
from typing import Any


def _version_key(version: str) -> tuple[int, ...]:
    """Order versions numerically so "3.10" sorts above "3.8"."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        raise ValueError(
            f"invalid Python version {version!r}; expected a dotted number such as 3.9"
        ) from None


def _has_union_annotation(node: ast.AST) -> bool:
    """Return True when node annotates a name, argument or return with ``A | B``."""
    if isinstance(node, ast.AnnAssign):
        annotations = [node.annotation]
    elif isinstance(node, ast.arg):
        annotations = [node.annotation] if node.annotation else []
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
        annotations = [node.returns]
    else:
        return False
    return any(
        isinstance(part, ast.BinOp) and isinstance(part.op, ast.BitOr)
        for annotation in annotations
        for part in ast.walk(annotation)
    )


#: ``except*`` parses only on 3.11+, so older interpreters have no node for it.
_TRY_STAR: type | None = getattr(ast, "TryStar", None)


#: Module-level names added in 3.11, keyed by module.
_NAMES_3_11 = {
    "datetime": {"UTC": "datetime_utc"},
    "enum": {"StrEnum": "enum_strenum"},
    "typing": {"Self": "typing_self"},
}


def _feature_needing_3_11(
    node: ast.AST, module_aliases: dict[str, str] | None = None
) -> str | None:
    """Name the 3.11-only feature ``node`` uses, if any.

    ``module_aliases`` maps a local name to the module it is bound to, so
    ``import datetime as dt`` makes ``dt.UTC`` count.
    """
    aliases = module_aliases or {name: name for name in _NAMES_3_11}
    if _TRY_STAR is not None and isinstance(node, _TRY_STAR):
        return "except_star"
    if isinstance(node, ast.Import) and any(a.name == "tomllib" for a in node.names):
        return "tomllib"
    if isinstance(node, ast.ImportFrom):
        if node.module == "tomllib":
            return "tomllib"
        names = _NAMES_3_11.get(node.module or "", {})
        for alias in node.names:
            if alias.name in names:
                return names[alias.name]
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        module = aliases.get(node.value.id)
        if module is not None:
            return _NAMES_3_11.get(module, {}).get(node.attr)
    return None


def _module_aliases(tree: ast.Module) -> dict[str, str]:
    """Local names bound to the modules whose 3.11 names are checked."""
    aliases = {name: name for name in _NAMES_3_11}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _NAMES_3_11:
                    aliases[alias.asname or alias.name] = alias.name
    return aliases


_BUILTIN_TYPE_NAMES = frozenset(
    {
        "int",
        "str",
        "float",
        "bytes",
        "bool",
        "complex",
        "list",
        "dict",
        "set",
        "frozenset",
        "tuple",
        "type",
        "object",
    }
)


def _is_type_operand(node: ast.expr) -> bool:
    """True for ``None``, a builtin type, a generic alias, or a union of them.

    Plain names such as ``MASK`` are left out: ``3 | MASK`` is bitwise or,
    which every version runs.
    """
    if isinstance(node, ast.Constant):
        return node.value is None
    if isinstance(node, ast.Name):
        return node.id in _BUILTIN_TYPE_NAMES
    if isinstance(node, ast.Subscript):
        return isinstance(node.value, ast.Name) and node.value.id in _BUILTIN_TYPE_NAMES
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _is_type_operand(node.left) or _is_type_operand(node.right)
    return False


def _annotation_node_ids(tree: ast.Module) -> set[int]:
    """Ids of every node inside an annotation, which the future import defers."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.AnnAssign, ast.arg)):
            annotations = [node.annotation]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations = [node.returns]
        else:
            continue
        for annotation in annotations:
            if annotation is not None:
                ids.update(id(part) for part in ast.walk(annotation))
    return ids


def _is_runtime_union(node: ast.AST, annotation_ids: set[int]) -> bool:
    """``A | B`` evaluated at runtime, which needs 3.10 even with the future import."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"isinstance", "issubclass"} and node.args[1:]:
            classinfo = node.args[1]
            return isinstance(classinfo, ast.BinOp) and isinstance(
                classinfo.op, ast.BitOr
            )
        return False
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.BitOr)
        and id(node) not in annotation_ids
        and _is_type_operand(node)
    )


def _feature_needing_3_10_or_3_12(node: ast.AST) -> tuple[str, str] | None:
    """Name a 3.10 call form or a 3.12 PEP 695 form ``node`` uses, if any."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "zip"
        and any(kw.arg == "strict" for kw in node.keywords)
    ):
        return "zip_strict", "3.10"
    type_alias = getattr(ast, "TypeAlias", None)
    if type_alias is not None and isinstance(node, type_alias):
        return "type_statement", "3.12"
    if getattr(node, "type_params", None):
        return "type_parameter_syntax", "3.12"
    return None


# ast.Match exists from Python 3.10. On 3.9 a match statement does not
# parse, so that code reaches the regex reading instead.
_MATCH_NODE: type[ast.AST] | None = getattr(ast, "Match", None)


def _report_once(
    features_found: list[dict[str, str]],
    issues: list[dict[str, str]],
    feature: str,
    min_version: str,
    *,
    status: str | None = None,
) -> None:
    """Record a feature and its issue, once per feature."""
    if any(f["feature"] == feature for f in features_found):
        return
    features_found.append({"feature": feature, "min_version": min_version})
    issues.append(
        {
            "feature": feature,
            "status": status or f"requires_{min_version}+",
            "min_version": min_version,
        }
    )


def _is_slots_dataclass(decorator: ast.expr) -> bool:
    """``@dataclass(slots=True)`` or ``@dataclasses.dataclass(slots=True)``."""
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
    return name == "dataclass" and any(
        kw.arg == "slots"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in decorator.keywords
    )


class CompatibilityChecker:
    """Check code compatibility across Python versions using AST analysis."""

    def check_compatibility(
        self,
        code: str,
        target_versions: list[str] | None = None,
    ) -> dict[str, Any]:
        if target_versions is None or len(target_versions) == 0:
            target_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]

        features_found: list[dict[str, str]] = []
        issues: list[dict[str, str]] = []
        recommendations: list[str] = []
        min_version = "3.0"

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Text patterns are the only reading of code that does not
            # parse. On parsed code they would also match docstrings and
            # comments, so there the tree is read instead.
            self._check_regex_features(code, features_found, issues)
            # Only the regex features are known. Without any, the code is
            # broken on every interpreter we can check, so claim none.
            if features_found:
                min_version = max(
                    (f["min_version"] for f in features_found), key=_version_key
                )
            return {
                "minimum_version": min_version,
                "features": features_found,
                "issues": issues,
                "recommendations": recommendations,
                "compatible_versions": (
                    [
                        v
                        for v in target_versions
                        if _version_key(v) >= _version_key(min_version)
                    ]
                    if features_found
                    else []
                ),
                "error": "Could not fully parse code",
            }

        self._check_ast_features(tree, features_found, issues)

        unique_features = self._deduplicate_features(features_found)

        if unique_features:
            min_version = max(
                (f["min_version"] for f in unique_features), key=_version_key
            )

        compatible = [
            v for v in target_versions if _version_key(v) >= _version_key(min_version)
        ]
        recommendations = self._generate_recommendations(min_version, unique_features)

        features_by_version: dict[str, list[str]] = {}
        for f in unique_features:
            ver = f["min_version"]
            features_by_version.setdefault(ver, []).append(f["feature"])

        return {
            "minimum_version": min_version,
            "features": unique_features,
            "features_by_version": features_by_version,
            "issues": issues,
            "recommendations": recommendations,
            "compatible_versions": compatible,
        }

    def _check_regex_features(
        self,
        code: str,
        features_found: list[dict[str, str]],
        issues: list[dict[str, str]],
    ) -> None:
        """Check for version-specific features using regex patterns."""
        if re.search(r"from\s+__future__\s+import\s+annotations", code):
            _report_once(
                features_found,
                issues,
                "from __future__ import annotations",
                "3.7",
                status="compatible",
            )

        if re.search(r"^\s*match\s+\w+.*:\s*$", code, re.MULTILINE) and re.search(
            r"^\s*case\s+", code, re.MULTILINE
        ):
            _report_once(features_found, issues, "match_statement", "3.10")

        if re.search(r"@dataclass\(.*slots\s*=\s*True", code):
            _report_once(features_found, issues, "dataclass_slots", "3.10")

    def _check_ast_features(
        self,
        tree: ast.Module,
        features_found: list[dict[str, str]],
        issues: list[dict[str, str]],
    ) -> None:
        """Check for version-specific features by walking the AST."""
        # With postponed evaluation an annotation is a string at runtime, so
        # `int | None` in one runs on any version that has the future import.
        postponed = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body
        )
        if postponed:
            _report_once(
                features_found,
                issues,
                "from __future__ import annotations",
                "3.7",
                status="compatible",
            )
        module_aliases = _module_aliases(tree)
        annotation_ids = _annotation_node_ids(tree)
        for node in ast.walk(tree):
            if _is_runtime_union(node, annotation_ids):
                _report_once(features_found, issues, "union_type_syntax", "3.10")
            other = _feature_needing_3_10_or_3_12(node)
            if other:
                _report_once(features_found, issues, other[0], other[1])
            if _MATCH_NODE is not None and isinstance(node, _MATCH_NODE):
                _report_once(features_found, issues, "match_statement", "3.10")
            elif isinstance(node, ast.ClassDef) and any(
                _is_slots_dataclass(d) for d in node.decorator_list
            ):
                _report_once(features_found, issues, "dataclass_slots", "3.10")
            feature_311 = _feature_needing_3_11(node, module_aliases)
            if feature_311:
                _report_once(features_found, issues, feature_311, "3.11")
            if not postponed and _has_union_annotation(node):
                _report_once(features_found, issues, "union_type_syntax", "3.10")
            if isinstance(node, ast.NamedExpr):
                features_found.append(
                    {"feature": "walrus_operator", "min_version": "3.8"}
                )
            elif isinstance(node, ast.JoinedStr):
                features_found.append({"feature": "fstrings", "min_version": "3.6"})
            elif isinstance(
                node,
                (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor, ast.AsyncWith),
            ):
                features_found.append({"feature": "async_await", "min_version": "3.5"})
            elif isinstance(node, ast.AnnAssign) or (
                isinstance(node, ast.FunctionDef) and node.returns is not None
            ):
                features_found.append({"feature": "type_hints", "min_version": "3.5"})

    @staticmethod
    def _deduplicate_features(
        features_found: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Remove duplicate features, keeping first occurrence."""
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for f in features_found:
            key = f["feature"]
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    @staticmethod
    def _generate_recommendations(
        min_version: str,
        unique_features: list[dict[str, str]],
    ) -> list[str]:
        """Generate compatibility recommendations."""
        recommendations: list[str] = []
        if _version_key(min_version) >= _version_key("3.10"):
            recommendations.append(
                "Code uses 3.10+ features. Consider using "
                "'from __future__ import annotations' for "
                "backward compatibility of type hints."
            )
        if not unique_features:
            recommendations.append(
                "No version-specific features detected. Code is broadly compatible."
            )
        return recommendations
