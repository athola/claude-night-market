"""Cargo dependency, build configuration, and panic analysis for Rust review."""

from __future__ import annotations

import re
from typing import Any

from ..rust_review_data import (
    INDEX_ACCESS_RE,
    PANIC_CALL_RE,
    TARGET_SECTION_RE,
    UNWRAP_CALL_RE,
)

__all__ = ["CargoBuildMixin"]

_CARGO_DEP_LINE_RE = re.compile(r'(\w+)\s*=\s*"([^"]+)"')
_FEATURE_LINE_RE = re.compile(r"(\w+)\s*=\s*\[(.*)\]")
_OPENSSL_OLD_RE = re.compile(r'openssl.*"0\.')


def _iter_toml_sections(
    lines: list[str],
) -> list[tuple[str, str]]:
    """Yield (line, section_name) pairs from TOML content.

    Tracks which [section] each line belongs to, skipping
    section headers themselves.
    """
    results: list[tuple[str, str]] = []
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if "[dependencies]" in line:
                current_section = "dependencies"
            elif "[features]" in line:
                current_section = "features"
            else:
                current_section = ""
            continue
        if current_section and "=" in line and not stripped.startswith("#"):
            results.append((line, current_section))
    return results


class CargoBuildMixin:
    """Mixin providing Cargo.toml, build configuration, and panic analysis."""

    def analyze_panic_propagation(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze error handling and panic usage.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with panic_points, unwrap_usage, and index_panics
        """
        content = context.get_file_content(file_path)
        panic_points = []
        unwrap_usage = []
        index_panics = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            # Detect explicit panic! calls
            if PANIC_CALL_RE.search(line):
                panic_points.append(
                    {
                        "line": i + 1,
                        "type": "explicit_panic",
                        "description": "Explicit panic! call",
                    }
                )

            # Detect unwrap() usage
            if UNWRAP_CALL_RE.search(line):
                unwrap_usage.append(
                    {
                        "line": i + 1,
                        "type": "unwrap",
                        "description": "Using unwrap() - can panic if None/Err",
                    }
                )
                panic_points.append(
                    {
                        "line": i + 1,
                        "type": "unwrap_panic",
                        "description": "unwrap() can cause panic",
                    }
                )

            # Detect array/vector indexing that can panic
            if INDEX_ACCESS_RE.search(line) and "get(" not in line:
                index_panics.append(
                    {
                        "line": i + 1,
                        "type": "index_access",
                        "description": (
                            "Direct index access can panic if out of bounds"
                        ),
                    }
                )

        return {
            "panic_points": panic_points,
            "unwrap_usage": unwrap_usage,
            "index_panics": index_panics,
        }

    @staticmethod
    def _check_dependency_line(
        line: str,
        dependencies: list[dict[str, str]],
        version_issues: list[dict[str, str]],
        security_concerns: list[dict[str, str]],
    ) -> None:
        """Process a single dependency line from [dependencies]."""
        deps = _CARGO_DEP_LINE_RE.match(line.strip())
        if deps:
            name, version = deps.groups()
            dependencies.append({"name": name, "version": version})
            if not any(c in version for c in ["^", "~", ">", "<", "*"]):
                version_issues.append(
                    {
                        "dependency": name,
                        "issue": "Exact version - consider version ranges",
                    }
                )
        if "tokio" in line and 'features = ["full"]' in line:
            version_issues.append(
                {
                    "dependency": "tokio",
                    "issue": "'full' features - consider selecting only needed",
                }
            )
        if _OPENSSL_OLD_RE.search(line):
            security_concerns.append(
                {
                    "dependency": "openssl",
                    "issue": "Older version - check security issues",
                }
            )

    @staticmethod
    def _check_feature_line(
        line: str,
        feature_analysis: list[dict[str, str]],
    ) -> None:
        """Process a single feature line from [features]."""
        feature_match = _FEATURE_LINE_RE.match(line.strip())
        if feature_match:
            name, features = feature_match.groups()
            if not features.strip():
                feature_analysis.append(
                    {"feature": name, "issue": "Empty feature definition"}
                )

    def analyze_dependencies(
        self,
        context: Any,
    ) -> dict[str, Any]:
        """Analyze Cargo.toml dependencies.

        Args:
            context: Skill context with file access

        Returns:
            Dictionary with dependency analysis
        """
        try:
            content = context.get_file_content("Cargo.toml")
        except Exception:
            return {
                "dependencies": [],
                "version_issues": [],
                "security_concerns": [],
                "feature_analysis": [],
            }

        dependencies: list[dict[str, str]] = []
        version_issues: list[dict[str, str]] = []
        security_concerns: list[dict[str, str]] = []
        feature_analysis: list[dict[str, str]] = []

        lines = self._get_lines(content)

        for line, section in _iter_toml_sections(lines):
            if section == "dependencies":
                self._check_dependency_line(
                    line, dependencies, version_issues, security_concerns
                )
            elif section == "features":
                self._check_feature_line(line, feature_analysis)

        return {
            "dependencies": dependencies,
            "version_issues": version_issues,
            "security_concerns": security_concerns,
            "feature_analysis": feature_analysis,
        }

    def analyze_build_configuration(
        self,
        context: Any,
    ) -> dict[str, Any]:
        """Analyze build configuration for optimization opportunities.

        Args:
            context: Skill context with file access

        Returns:
            Dictionary with build configuration analysis
        """
        optimization_level = "default"
        target_specific = []
        dependency_optimization = []
        recommendations = []

        try:
            cargo_content = context.get_file_content("Cargo.toml")
            if "[profile.release]" in cargo_content:
                optimization_level = "release"
            if "opt-level" in cargo_content:
                optimization_level = "custom"

            if 'features = ["derive"]' in cargo_content:
                dependency_optimization.append(
                    {
                        "type": "feature_selection",
                        "description": ("Using selective features for dependencies"),
                    }
                )
        except (FileNotFoundError, OSError):
            pass

        try:
            config_content = context.get_file_content(".cargo/config.toml")
            if "[target." in config_content:
                target_match = TARGET_SECTION_RE.search(config_content)
                if target_match:
                    target_specific.append(
                        {
                            "target": target_match.group(1),
                            "configured": True,
                        }
                    )

            if "linker" in config_content:
                target_specific.append(
                    {
                        "type": "custom_linker",
                        "description": "Custom linker configured",
                    }
                )
        except (FileNotFoundError, OSError):
            pass

        if optimization_level == "default":
            recommendations.append(
                "Consider adding [profile.release] optimization settings"
            )

        if not target_specific:
            recommendations.append(
                "Consider target-specific optimizations in .cargo/config.toml"
            )

        if not dependency_optimization:
            recommendations.append(
                "Review dependency features to reduce compilation time"
            )

        return {
            "optimization_level": optimization_level,
            "target_specific": target_specific,
            "dependency_optimization": dependency_optimization,
            "recommendations": recommendations,
        }
