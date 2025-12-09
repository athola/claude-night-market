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
from typing import Any

import yaml

# Constants for magic numbers
PARITY_THRESHOLD = 0.9


class CompatibilityValidator:
    """Validates wrapper implementations maintain feature parity with original commands.

    This class analyzes both markdown command files and Python wrapper implementations
    to ensure that wrapper scripts maintain the same functionality as the original
    plugin commands they replace.
    """

    def __init__(self):
        self.feature_weights = {
            "parameters": 0.3,
            "options": 0.2,
            "output_format": 0.3,
            "error_handling": 0.2,
        }

    def validate_wrapper(self, original: str, wrapper: str) -> dict:
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
            original_features, wrapper_features
        )

        result = {
            "feature_parity": parity_score,
            "original_features": original_features,
            "wrapper_features": wrapper_features,
            "missing_features": missing_features,
            "validation_passed": parity_score >= PARITY_THRESHOLD
            and not self._has_critical_missing_features(missing_features),
        }

        return result

    def _extract_features(self, file_path: str) -> dict[str, Any]:
        """Extract features from command implementation file.

        Args:
            file_path: Path to file to analyze

        Returns:
            Dictionary of extracted features

        """
        features = {
            "parameters": [],
            "options": [],
            "output_format": None,
            "error_handling": [],
        }

        if not os.path.exists(file_path):
            return features

        if file_path.endswith(".md"):
            features.update(self._parse_markdown_command(file_path))
        elif file_path.endswith(".py"):
            features.update(self._parse_python_wrapper(file_path))

        return features

    def _parse_markdown_command(self, file_path: str) -> dict:
        """Parse markdown command file for features.

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary of extracted features

        """
        features = {
            "parameters": [],
            "options": [],
            "output_format": None,
            "error_handling": [],
        }

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

    def _extract_frontmatter_features(self, content: str, features: dict) -> None:
        """Extract features from YAML frontmatter.

        Args:
            content: File content
            features: Features dict to update

        """
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return

        frontmatter = yaml.safe_load(frontmatter_match.group(1))
        if not frontmatter:
            return

        # Extract parameters - handle both string and dict formats
        if "parameters" in frontmatter:
            params = frontmatter["parameters"]
            if isinstance(params, list):
                for param in params:
                    if isinstance(param, dict) and "name" in param:
                        features["parameters"].append(param["name"])
                    elif isinstance(param, str):
                        features["parameters"].append(param)

        # Extract options
        if "options" in frontmatter:
            features["options"] = frontmatter["options"]

        # Extract usage to infer output format
        if "usage" in frontmatter:
            usage = frontmatter["usage"]
            usage_lower = usage.lower()
            if "report" in usage_lower or "output" in usage_lower:
                features["output_format"] = "markdown_report"
            elif "json" in usage_lower:
                features["output_format"] = "json"

        # Look for error handling indicators
        if "error_handling" in frontmatter:
            features["error_handling"] = frontmatter["error_handling"]

    def _extract_content_features(self, content: str, features: dict) -> None:
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

    def _parse_python_wrapper(self, file_path: str) -> dict:
        """Parse Python wrapper file for features.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary of extracted features

        """
        features = {
            "parameters": [],
            "options": [],
            "output_format": None,
            "error_handling": [],
        }

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST for structural features
            self._extract_ast_features(content, features)

            # Use regex for additional pattern matching
            self._extract_regex_features(content, features)

        except Exception:
            # If parsing fails, use regex-based extraction only
            self._extract_fallback_features(content, features)

        # Remove duplicates and clean up
        features["parameters"] = list(set(features["parameters"]))
        features["options"] = list(set(features["options"]))
        features["error_handling"] = list(set(features["error_handling"]))

        return features

    def _extract_ast_features(self, content: str, features: dict) -> None:
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

    def _extract_function_features(self, node: ast.FunctionDef, features: dict) -> None:
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

    def _extract_regex_features(self, content: str, features: dict) -> None:
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

    def _extract_option_patterns(self, content: str, features: dict) -> None:
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

    def _extract_option_literals(self, content: str, features: dict) -> None:
        """Extract options from string literals.

        Args:
            content: Python source code
            features: Features dict to update

        """
        option_literals = re.findall(
            r'\[([\'"]([a-zA-Z]+)[\'"](?:,\s*[\'"][a-zA-Z]+[\'"])*?)\]', content
        )
        for literal in option_literals:
            # Extract individual quoted values
            options = re.findall(r'[\'"]([a-zA-Z]+)[\'"]', literal)
            features["options"].extend(options)

    def _extract_fallback_features(self, content: str, features: dict) -> None:
        """Extract features using basic regex when AST parsing fails.

        Args:
            content: Python source code
            features: Features dict to update

        """
        content.lower()

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

    def _calculate_parity(self, original: dict, wrapper: dict) -> float:
        """Calculate feature parity score between original and wrapper.

        Args:
            original: Features from original command
            wrapper: Features from wrapper implementation

        Returns:
            Parity score between 0.0 and 1.0

        """
        total_score = 0.0

        for feature, weight in self.feature_weights.items():
            original_value = original.get(feature, [])
            wrapper_value = wrapper.get(feature, [])

            if isinstance(original_value, list):
                # Calculate overlap for lists
                original_set = set(original_value)
                wrapper_set = set(wrapper_value)

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

    def _find_missing_features(self, original: dict, wrapper: dict) -> list[dict]:
        """Identify features present in original but missing from wrapper.

        Args:
            original: Features from original command
            wrapper: Features from wrapper implementation

        Returns:
            List of missing feature dictionaries with severity information

        """
        missing = []

        for feature, original_value in original.items():
            wrapper_value = wrapper.get(feature, [])

            if isinstance(original_value, list):
                original_set = set(original_value)
                wrapper_set = set(wrapper_value)

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
                    missing_items = original_set - wrapper_set

                for item in missing_items:
                    severity = self._determine_severity(feature, item)
                    missing.append(
                        {
                            "category": feature,
                            "name": item,
                            "severity": severity,
                            "description": f"Missing {feature}: {item}",
                        }
                    )
            elif original_value != wrapper_value:
                severity = self._determine_severity(feature, original_value)
                missing.append(
                    {
                        "category": feature,
                        "name": str(original_value),
                        "severity": severity,
                        "description": (
                            f"Different {feature}: expected {original_value}, "
                            f"got {wrapper_value}"
                        ),
                    }
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

    def _has_critical_missing_features(self, missing_features: list[dict]) -> bool:
        """Check if any critical features are missing.

        Args:
            missing_features: List of missing features

        Returns:
            True if critical features are missing

        """
        return any(feature["severity"] == "critical" for feature in missing_features)


def main():
    """Main entry point for compatibility validation"""
    parser = argparse.ArgumentParser(
        description=(
            "Validate feature parity between original commands and "
            "wrapper implementations"
        )
    )
    parser.add_argument("original", help="Path to original command file (.md)")
    parser.add_argument("wrapper", help="Path to wrapper implementation file (.py)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = CompatibilityValidator()
    result = validator.validate_wrapper(args.original, args.wrapper)

    if args.verbose:
        print("\nValidation Results:")
        print(f"Feature Parity Score: {result['feature_parity']:.1%}")
        print(f"Validation Passed: {result['validation_passed']}")

        if result["missing_features"]:
            print(f"\nMissing Features ({len(result['missing_features'])}):")
            for feature in result["missing_features"]:
                print(f"  - [{feature['severity'].upper()}] {feature['description']}")
    else:
        print(f"Feature Parity: {result['feature_parity']:.1%}")
        if not result["validation_passed"]:
            print("Validation FAILED")
            sys.exit(1)
        else:
            print("Validation PASSED")


if __name__ == "__main__":
    main()
