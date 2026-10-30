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

        self._check_regex_features(code, features_found, issues)

        try:
            tree = ast.parse(code)
        except SyntaxError:
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
            issues.append(
                {
                    "feature": "from __future__ import annotations",
                    "status": "compatible",
                    "min_version": "3.7",
                }
            )
            features_found.append(
                {
                    "feature": "from __future__ import annotations",
                    "min_version": "3.7",
                }
            )

        if re.search(r"^\s*match\s+\w+.*:\s*$", code, re.MULTILINE) and re.search(
            r"^\s*case\s+", code, re.MULTILINE
        ):
            features_found.append({"feature": "match_statement", "min_version": "3.10"})
            issues.append(
                {
                    "feature": "match_statement",
                    "status": "requires_3.10+",
                    "min_version": "3.10",
                }
            )

        if re.search(r"@dataclass\(.*slots\s*=\s*True", code):
            features_found.append({"feature": "dataclass_slots", "min_version": "3.10"})
            issues.append(
                {
                    "feature": "dataclass_slots",
                    "status": "requires_3.10+",
                    "min_version": "3.10",
                }
            )

    def _check_ast_features(
        self,
        tree: ast.Module,
        features_found: list[dict[str, str]],
        issues: list[dict[str, str]],
    ) -> None:
        """Check for version-specific features by walking the AST."""
        union_reported = False
        for node in ast.walk(tree):
            if _has_union_annotation(node):
                features_found.append(
                    {"feature": "union_type_syntax", "min_version": "3.10"}
                )
                if not union_reported:
                    union_reported = True
                    issues.append(
                        {
                            "feature": "union_type_syntax",
                            "status": "requires_3.10+",
                            "min_version": "3.10",
                        }
                    )
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
