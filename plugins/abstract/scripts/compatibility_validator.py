#!/usr/bin/env python3
"""Compatibility Validator.

Validates feature parity between original plugin commands and wrapper implementations.

This script validates that wrapper implementations maintain feature parity
with original plugin commands when migrating to superpowers-based wrappers.
"""

import argparse
import ast
import logging
import os
import re
import sys
from typing import Any, Literal, TypedDict

import yaml

# Constants for magic numbers
PARITY_THRESHOLD = 0.9
FEATURE_KEYS: tuple[
    Literal["parameters", "options", "output_format", "error_handling"],
    ...,
] = ("parameters", "options", "output_format", "error_handling")


class FeatureMap(TypedDict):
    """Feature extraction result shape."""

    parameters: list[str]
    options: list[str]
    output_format: str | None
    error_handling: list[str]


class ValidationResult(TypedDict):
    """Validation result payload."""

    feature_parity: float
    original_features: FeatureMap
    wrapper_features: FeatureMap
    missing_features: list[dict[str, Any]]
    validation_passed: bool


class CompatibilityValidator:
    """Validates wrapper implementations maintain feature parity with original commands.

    This class analyzes both markdown command files and Python wrapper implementations
    to validate that wrapper scripts maintain the same functionality as the original
    plugin commands they replace.
    """

    def __init__(self) -> None:
        """Initialize the compatibility validator."""
        self.feature_weights = {
            "parameters": 0.3,
            "options": 0.2,
            "output_format": 0.3,
            "error_handling": 0.2,
        }

    @staticmethod
    def _empty_features() -> FeatureMap:
        return {
            "parameters": [],
            "options": [],
            "output_format": None,
            "error_handling": [],
        }

    def validate_wrapper(self, original: str, wrapper: str) -> ValidationResult:
        """Validate that wrapper maintains feature parity with original command.

        Args:
            original: Path to original command file (.md)
            wrapper: Path to wrapper implementation file (.py)

        Returns:
            dict: Validation results with feature parity score and missing features.

        """
        original_features = self._extract_features(original)
        wrapper_features = self._extract_features(wrapper)

        parity_score = self._calculate_parity(original_features, wrapper_features)
        missing_features = self._find_missing_features(
            original_features,
            wrapper_features,
        )

        return {
            "feature_parity": parity_score,
            "original_features": original_features,
            "wrapper_features": wrapper_features,
            "missing_features": missing_features,
            "validation_passed": parity_score >= PARITY_THRESHOLD
            and not self._has_critical_missing_features(missing_features),
        }

    def _extract_features(self, file_path: str) -> FeatureMap:
        """Extract features from command implementation file.

        Args:
            file_path: Path to file to analyze

        Returns:
            Dictionary of extracted features

        """
        features = self._empty_features()

        if not os.path.exists(file_path):
            return features

        if file_path.endswith(".md"):
            features.update(self._parse_markdown_command(file_path))
        elif file_path.endswith(".py"):
            features.update(self._parse_python_wrapper(file_path))

        return features

    def _parse_markdown_command(self, file_path: str) -> FeatureMap:
        """Parse markdown command file for features.

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary of extracted features

        """
        features = self._empty_features()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse YAML frontmatter
            self._extract_frontmatter_features(content, features)

            # Scan content for additional features
            self._extract_content_features(content, features)

        except Exception as e:
            # If parsing fails, return empty features
            logging.warning(f"Failed to parse {file_path}: {e}")

        return features

    def _extract_frontmatter_features(self, content: str, features: FeatureMap) -> None:
        """Extract features from YAML frontmatter.

        Args:
            content: File content
            features: Features dict to update

        """
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return

        frontmatter = yaml.safe_load(frontmatter_match.group(1))
        if not isinstance(frontmatter, dict):
            return

        self._extract_frontmatter_parameters(frontmatter, features)
        self._extract_frontmatter_options(frontmatter, features)
        self._extract_frontmatter_usage(frontmatter, features)
        self._extract_frontmatter_error_handling(frontmatter, features)

    def _extract_frontmatter_parameters(
        self,
        frontmatter: dict[str, Any],
        features: FeatureMap,
    ) -> None:
        """Extract parameter names from frontmatter."""
        params = frontmatter.get("parameters")
        if isinstance(params, list):
            for param in params:
                if isinstance(param, dict):
                    name = param.get("name")
                    if isinstance(name, str):
                        features["parameters"].append(name)
                elif isinstance(param, str):
                    features["parameters"].append(param)
            return
        if isinstance(params, str):
            features["parameters"].append(params)

    def _extract_frontmatter_options(
        self,
        frontmatter: dict[str, Any],
        features: FeatureMap,
    ) -> None:
        """Extract options from frontmatter."""
        options = frontmatter.get("options")
        if isinstance(options, list):
            features["options"] = [opt for opt in options if isinstance(opt, str)]
        elif isinstance(options, str):
            features["options"] = [options]

    def _extract_frontmatter_usage(
        self,
        frontmatter: dict[str, Any],
        features: FeatureMap,
    ) -> None:
        """Infer output format from usage hints."""
        usage = frontmatter.get("usage")
        if not isinstance(usage, str):
            return
        usage_lower = usage.lower()
        if "report" in usage_lower or "output" in usage_lower:
            features["output_format"] = "markdown_report"
        elif "json" in usage_lower:
            features["output_format"] = "json"

    def _extract_frontmatter_error_handling(
        self,
        frontmatter: dict[str, Any],
        features: FeatureMap,
    ) -> None:
        """Extract error handling hints from frontmatter."""
        error_handling = frontmatter.get("error_handling")
        if isinstance(error_handling, list):
            features["error_handling"] = [
                item for item in error_handling if isinstance(item, str)
            ]
        elif isinstance(error_handling, str):
            features["error_handling"] = [error_handling]

    def _extract_content_features(self, content: str, features: FeatureMap) -> None:
        """Extract features from content scanning.

        Args:
            content: File content
            features: Features dict to update

        """
        content_lower = content.lower()

        # Detect error handling patterns
        error_patterns = ["validation", "error", "exception", "fallback", "recover"]
        for pattern in error_patterns:
            if pattern in content_lower and pattern not in features["error_handling"]:
                features["error_handling"].append(pattern)

    def _parse_python_wrapper(self, file_path: str) -> FeatureMap:
        """Parse Python wrapper file for features.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary of extracted features

        """
        features = self._empty_features()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            logging.warning(f"Failed to read {file_path}: {exc}")
            return features

        try:
            # Parse AST for structural features
            self._extract_ast_features(content, features)

            # Use regex for additional pattern matching
            self._extract_regex_features(content, features)

        except Exception:
            # If parsing fails, use regex-based extraction only
            self._extract_fallback_features(content, features)

        # Remove duplicates and clean up
        features["parameters"] = sorted(set(features["parameters"]))
        features["options"] = sorted(set(features["options"]))
        features["error_handling"] = sorted(set(features["error_handling"]))

        return features

    def _extract_ast_features(self, content: str, features: FeatureMap) -> None:
        """Extract features using AST parsing.

        Args:
            content: Python source code
            features: Features dict to update

        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._extract_function_features(node, features)

    def _extract_function_features(
        self,
        node: ast.FunctionDef,
        features: FeatureMap,
    ) -> None:
        """Extract features from a function definition.

        Args:
            node: AST FunctionDef node
            features: Features dict to update

        """
        # Extract function parameters
        for arg in node.args.args:
            if arg.arg not in features["parameters"]:
                features["parameters"].append(arg.arg)

        # Look for error handling patterns
        for child in ast.walk(node):
            if isinstance(child, (ast.Try, ast.ExceptHandler)):
                if "exception" not in features["error_handling"]:
                    features["error_handling"].append("exception")
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in ["validate", "check", "verify"]:
                        if "validation" not in features["error_handling"]:
                            features["error_handling"].append("validation")

    def _extract_regex_features(self, content: str, features: FeatureMap) -> None:
        """Extract features using regex patterns.

        Args:
            content: Python source code
            features: Features dict to update

        """
        content_lower = content.lower()

        # Detect option patterns (filter common words)
        self._extract_option_patterns(content, features)

        # Detect output format
        if "json" in content_lower:
            features["output_format"] = "json"
        elif "markdown" in content_lower or "md" in content_lower:
            features["output_format"] = "markdown"

        # Detect fallback mechanisms
        if (
            "fallback" in content_lower or "backup" in content_lower
        ) and "fallback" not in features["error_handling"]:
            features["error_handling"].append("fallback")

        # Detect parameter patterns in get() calls
        get_patterns = re.findall(r'get\([\'"]([^\'"]+)[\'"]\)', content)
        features["parameters"].extend(get_patterns)

        # Detect options in string literals
        self._extract_option_literals(content, features)

    def _extract_option_patterns(self, content: str, features: FeatureMap) -> None:
        """Extract option patterns while filtering common words.

        Args:
            content: Python source code
            features: Features dict to update

        """
        excluded_words = {
            "development",
            "skill",
            "driven",
            "test",
            "superpower",
            "wrapper",
        }

        option_patterns = re.findall(r"--?(\w+)(?=\W)", content)
        filtered_options = [opt for opt in option_patterns if opt not in excluded_words]
        features["options"].extend(filtered_options)

    def _extract_option_literals(self, content: str, features: FeatureMap) -> None:
        """Extract options from string literals.

        Args:
            content: Python source code
            features: Features dict to update

        """
        option_literals = re.findall(
            r'\[(?:[\'"][a-zA-Z]+[\'"](?:,\s*[\'"][a-zA-Z]+[\'"])*)\]',
            content,
        )
        for literal in option_literals:
            # Extract individual quoted values
            options = re.findall(r'[\'"]([a-zA-Z]+)[\'"]', literal)
            features["options"].extend(options)

    def _extract_fallback_features(self, content: str, features: FeatureMap) -> None:
        """Extract features using basic regex when AST parsing fails.

        Args:
            content: Python source code
            features: Features dict to update

        """
        # Basic parameter detection
        param_patterns = re.findall(r"def.*?\((.*?)\):", content, re.DOTALL)
        for params in param_patterns:
            for param_raw in params.split(","):
                param = param_raw.strip().split("=")[0].strip()
                if param and param != "self":
                    features["parameters"].append(param)

        # Detect get() patterns for dict access
        get_patterns = re.findall(r'get\([\'"]([^\'"]+)[\'"]\)', content)
        features["parameters"].extend(get_patterns)

    def _calculate_parity(self, original: FeatureMap, wrapper: FeatureMap) -> float:
        """Calculate feature parity score between original and wrapper.

        Args:
            original: Features from original command
            wrapper: Features from wrapper implementation

        Returns:
            Parity score between 0.0 and 1.0

        """
        total_score = 0.0

        for feature in FEATURE_KEYS:
            weight = self.feature_weights[feature]
            original_value = original[feature]
            wrapper_value = wrapper[feature]

            if isinstance(original_value, list):
                # Calculate overlap for lists
                original_set = set(original_value)
                wrapper_list = wrapper_value if isinstance(wrapper_value, list) else []
                wrapper_set = set(wrapper_list)

                if not original_set and not wrapper_set:
                    feature_score = 1.0  # Both empty is perfect match
                elif not original_set:
                    feature_score = (
                        0.0  # Original empty but wrapper has features is fine
                    )
                else:
                    overlap = len(original_set & wrapper_set)
                    total = len(original_set)

                    # For parameters, be more flexible with naming
                    # (e.g., skill-path vs skill_path)
                    if feature == "parameters":
                        normalized_overlap = 0
                        for orig in original_set:
                            for wrap in wrapper_set:
                                # Normalize by removing common separators
                                orig_norm = orig.replace("-", "_").replace("_", "-")
                                wrap_norm = wrap.replace("-", "_").replace("_", "-")
                                if orig_norm == wrap_norm:
                                    normalized_overlap += 1
                                    break
                        feature_score = normalized_overlap / total if total > 0 else 1.0
                    else:
                        feature_score = overlap / total if total > 0 else 1.0
            else:
                # Simple comparison for single values
                feature_score = 1.0 if original_value == wrapper_value else 0.0

            total_score += feature_score * weight

        return round(total_score, 3)

    def _find_missing_features(
        self,
        original: FeatureMap,
        wrapper: FeatureMap,
    ) -> list[dict[str, Any]]:
        """Identify features present in original but missing from wrapper.

        Args:
            original: Features from original command
            wrapper: Features from wrapper implementation

        Returns:
            List of missing feature dictionaries with severity information

        """
        missing: list[dict[str, Any]] = []

        for feature in FEATURE_KEYS:
            original_value = original[feature]
            wrapper_value = wrapper[feature]

            if isinstance(original_value, list):
                original_set = set(original_value)
                wrapper_list = wrapper_value if isinstance(wrapper_value, list) else []
                wrapper_set = set(wrapper_list)

                if feature == "parameters":
                    # Use normalized comparison for parameters
                    missing_items = []
                    for orig in original_set:
                        found = False
                        for wrap in wrapper_set:
                            orig_norm = orig.replace("-", "_").replace("_", "-")
                            wrap_norm = wrap.replace("-", "_").replace("_", "-")
                            if orig_norm == wrap_norm:
                                found = True
                                break
                        if not found:
                            missing_items.append(orig)
                else:
                    missing_items = sorted(original_set - wrapper_set)

                for item in missing_items:
                    severity = self._determine_severity(feature, item)
                    missing.append(
                        {
                            "category": feature,
                            "name": item,
                            "severity": severity,
                            "description": f"Missing {feature}: {item}",
                        },
                    )
            elif original_value != wrapper_value:
                severity = self._determine_severity(feature, str(original_value))
                missing.append(
                    {
                        "category": feature,
                        "name": str(original_value),
                        "severity": severity,
                        "description": (
                            f"Different {feature}: expected {original_value}, "
                            f"got {wrapper_value}"
                        ),
                    },
                )

        return sorted(missing, key=lambda x: self._severity_order(x["severity"]))

    def _determine_severity(self, category: str, feature: str) -> str:
        """Determine the severity level of a missing feature.

        Args:
            category: Feature category (parameters, options, etc.)
            feature: Feature name

        Returns:
            Severity level: critical, high, medium, or low

        """
        # Critical features
        if category == "parameters" and feature in ["skill-path", "command", "input"]:
            return "critical"

        # High priority features
        if category == "parameters":
            return "high"
        if category == "options" and feature in ["verbose", "debug", "help"]:
            return "high"

        # Medium priority features
        if category == "options":
            return "medium"
        if category == "error_handling" and feature in ["validation", "exception"]:
            return "medium"

        # Low priority features
        return "low"

    def _severity_order(self, severity: str) -> int:
        """Get numeric value for severity sorting.

        Args:
            severity: Severity string

        Returns:
            Numeric severity order (lower is more severe)

        """
        severity_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return severity_map.get(severity, 3)

    def _has_critical_missing_features(
        self,
        missing_features: list[dict[str, Any]],
    ) -> bool:
        """Check if any critical features are missing.

        Args:
            missing_features: List of missing features

        Returns:
            True if critical features are missing

        """
        return any(feature["severity"] == "critical" for feature in missing_features)


def main() -> None:
    """Validate compatibility between original commands and wrapper implementations."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate feature parity between original commands and "
            "wrapper implementations"
        ),
    )
    parser.add_argument("original", help="Path to original command file (.md)")
    parser.add_argument("wrapper", help="Path to wrapper implementation file (.py)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = CompatibilityValidator()
    result = validator.validate_wrapper(args.original, args.wrapper)

    if args.verbose:
        if result["missing_features"]:
            for _feature in result["missing_features"]:
                pass
    elif not result["validation_passed"]:
        sys.exit(1)
    else:
        pass


if __name__ == "__main__":
    main()
