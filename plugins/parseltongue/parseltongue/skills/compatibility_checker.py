"""Compatibility checker skill for parseltongue."""

from __future__ import annotations

import ast
import re
from typing import Any


class CompatibilityChecker:
    """Check code compatibility across Python versions using AST analysis."""

    FEATURE_VERSIONS: dict[str, str] = {
        "match_statement": "3.10",
        "union_type_syntax": "3.10",
        "dataclass_slots": "3.10",
        "walrus_operator": "3.8",
        "fstrings": "3.6",
        "async_await": "3.5",
        "type_hints": "3.5",
        "from __future__ import annotations": "3.7",
    }

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

        # Check for from __future__ import annotations (3.7+)
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

        # Check for match statements (3.10+)
        if re.search(r"^\s*match\s+\w+.*:\s*$", code, re.MULTILINE):
            if re.search(r"^\s*case\s+", code, re.MULTILINE):
                features_found.append(
                    {"feature": "match_statement", "min_version": "3.10"}
                )
                issues.append(
                    {
                        "feature": "match_statement",
                        "status": "requires_3.10+",
                        "min_version": "3.10",
                    }
                )

        # Check for union type syntax X | Y (3.10+)
        if re.search(r":\s*\w+\s*\|\s*\w+", code) or re.search(
            r"->\s*\w+\s*\|\s*\w+", code
        ):
            features_found.append(
                {"feature": "union_type_syntax", "min_version": "3.10"}
            )
            issues.append(
                {
                    "feature": "union_type_syntax",
                    "status": "requires_3.10+",
                    "min_version": "3.10",
                }
            )

        # Check for dataclass slots=True (3.10+)
        if re.search(r"@dataclass\(.*slots\s*=\s*True", code):
            features_found.append({"feature": "dataclass_slots", "min_version": "3.10"})
            issues.append(
                {
                    "feature": "dataclass_slots",
                    "status": "requires_3.10+",
                    "min_version": "3.10",
                }
            )

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "minimum_version": min_version,
                "features": features_found,
                "issues": issues,
                "recommendations": recommendations,
                "compatible_versions": target_versions,
                "error": "Could not fully parse code",
            }

        for node in ast.walk(tree):
            # Walrus operator := (3.8+)
            if isinstance(node, ast.NamedExpr):
                features_found.append(
                    {"feature": "walrus_operator", "min_version": "3.8"}
                )

            # f-strings (3.6+)
            if isinstance(node, ast.JoinedStr):
                features_found.append({"feature": "fstrings", "min_version": "3.6"})

            # async/await (3.5+)
            if isinstance(
                node,
                (
                    ast.AsyncFunctionDef,
                    ast.Await,
                    ast.AsyncFor,
                    ast.AsyncWith,
                ),
            ):
                features_found.append({"feature": "async_await", "min_version": "3.5"})

            # Type hints (3.5+)
            if isinstance(node, ast.FunctionDef) and node.returns is not None:
                features_found.append({"feature": "type_hints", "min_version": "3.5"})
            if isinstance(node, ast.AnnAssign):
                features_found.append({"feature": "type_hints", "min_version": "3.5"})

        # Deduplicate features
        seen: set[str] = set()
        unique_features: list[dict[str, str]] = []
        for f in features_found:
            key = f["feature"]
            if key not in seen:
                seen.add(key)
                unique_features.append(f)

        if unique_features:
            min_version = max(f["min_version"] for f in unique_features)

        compatible = [v for v in target_versions if v >= min_version]

        # Generate recommendations
        if min_version >= "3.10":
            recommendations.append(
                "Code uses 3.10+ features. Consider using "
                "'from __future__ import annotations' for "
                "backward compatibility of type hints."
            )
        if not unique_features:
            recommendations.append(
                "No version-specific features detected. Code is broadly compatible."
            )

        # Group features by version
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
