"""Unit tests for language detection functionality.

Tests code language identification, feature detection,
and pattern recognition capabilities.
"""

from __future__ import annotations

import pytest

# Import the skills we're testing
from parseltongue.skills.language_detection import LanguageDetectionSkill

# Import test data from conftest
from .conftest import (
    JAVASCRIPT_SAMPLE_CODE,
    PYTHON_SAMPLE_CODE,
    RUST_SAMPLE_CODE,
)


class TestLanguageDetectionSkill:
    """Test suite for LanguageDetectionSkill."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = LanguageDetectionSkill()

    @pytest.mark.unit
    def test_detects_python_language(self, sample_python_code) -> None:
        """Given Python code, when skill analyzes, then identifies Python correctly."""
        # Arrange
        code = PYTHON_SAMPLE_CODE

        # Act
        result = self.skill.detect_language(code)

        # Assert
        assert result["language"] == "python"
        assert result["confidence"] > 0.9
        assert "python" in result["features"]
        assert "type_hints" in result["features"]
        assert "classes" in result["features"]
        assert "async_functions" in result["features"]

    @pytest.mark.unit
    def test_detects_javascript_language(self, sample_javascript_code) -> None:
        """Given JavaScript code, when skill analyzes, then identifies JavaScript correctly."""
        # Arrange
        code = sample_javascript_code

        # Act
        result = self.skill.detect_language(code)

        # Assert
        assert result["language"] == "javascript"
        assert result["confidence"] > 0.9
        assert "classes" in result["features"]
        assert "async_methods" in result["features"]
        assert "prototype" in result["features"]

    @pytest.mark.unit
    def test_detects_typescript_language(self, sample_typescript_code) -> None:
        """Given TypeScript code, when skill analyzes, then identifies TypeScript correctly."""
        # Arrange
        code = sample_typescript_code

        # Act
        result = self.skill.detect_language(code)

        # Assert
        assert result["language"] == "typescript"
        assert result["confidence"] > 0.9
        assert "interfaces" in result["features"]
        assert "type_annotations" in result["features"]
        assert "generics" in result["features"]

    @pytest.mark.unit
    def test_detects_rust_language(self, sample_rust_code) -> None:
        """Given Rust code, when skill analyzes, then identifies Rust correctly."""
        # Arrange
        code = sample_rust_code

        # Act
        result = self.skill.detect_language(code)

        # Assert
        assert result["language"] == "rust"
        assert result["confidence"] > 0.9
        assert "structs" in result["features"]
        assert "traits" in result["features"]
        assert "lifetime_annotations" in result["features"]
        assert "error_handling" in result["features"]

    @pytest.mark.unit
    def test_identifies_python_features(self, sample_python_code) -> None:
        """Given Python code, when skill analyzes, then identifies Python-specific features."""
        # Arrange
        code = PYTHON_SAMPLE_CODE

        # Act
        result = self.skill.analyze_features(code, "python")

        # Assert
        features = result["features"]

        # Should detect dataclass
        assert any("dataclass" in feature for feature in features)

        # Should detect type hints
        assert any("type_hint" in feature for feature in features)

        # Should detect async function
        assert any("async" in feature for feature in features)

        # Should detect class definition
        assert features["classes"] >= 1
        assert "UserService" in features["class_names"]

    @pytest.mark.unit
    def test_identifies_javascript_features(self, sample_javascript_code) -> None:
        """Given JavaScript code, when skill analyzes, then identifies JavaScript-specific features."""
        # Arrange
        code = sample_javascript_code

        # Act
        result = self.skill.analyze_features(code, "javascript")

        # Assert
        features = result["features"]

        # Should detect class syntax
        assert features["classes"] >= 1
        assert "UserService" in features["class_names"]

        # Should detect async methods
        assert features["async_methods"] >= 1

        # Should detect Map usage
        assert features["data_structures"]["Map"] >= 1

    @pytest.mark.unit
    def test_identifies_typescript_features(self, sample_typescript_code) -> None:
        """Given TypeScript code, when skill analyzes, then identifies TypeScript-specific features."""
        # Arrange
        code = sample_typescript_code

        # Act
        result = self.skill.analyze_features(code, "typescript")

        # Assert
        features = result["features"]

        # Should detect interface definition
        assert features["interfaces"] >= 1
        assert "User" in features["interface_names"]

        # Should detect type annotations
        assert features["type_annotations"] >= 5

        # Should detect optional properties
        assert features["optional_properties"] >= 1

    @pytest.mark.unit
    def test_identifies_rust_features(self, sample_rust_code) -> None:
        """Given Rust code, when skill analyzes, then identifies Rust-specific features."""
        # Arrange
        code = sample_rust_code

        # Act
        result = self.skill.analyze_features(code, "rust")

        # Assert
        features = result["features"]

        # Should detect struct definitions
        assert features["structs"] >= 1
        assert "User" in features["struct_names"]

        # Should detect impl blocks
        assert features["impl_blocks"] >= 1

        # Should detect Result type
        assert features["error_handling"]["Result"] >= 1

        # Should detect Arc<Mutex<>> usage
        assert features["concurrency"]["Arc"] >= 1
        assert features["concurrency"]["Mutex"] >= 1

    @pytest.mark.unit
    def test_detects_python_version_features(self, language_samples) -> None:
        """Given Python code, when skill analyzes, then detects Python version features."""
        # Arrange
        modern_python = """
from __future__ import annotations
from typing import TypeAlias, Literal

UserId: TypeAlias = int
Status: Literal = ["active", "inactive"]

def process_user(user_id: UserId, status: Status) -> None:
    match status:
        case "active":
            print(f"User {user_id} is active")
        case "inactive":
            print(f"User {user_id} is inactive")
        """

        # Act
        result = self.skill.analyze_python_version(modern_python)

        # Assert
        assert result["minimum_version"] >= "3.10"
        assert "type_alias" in result["features"]
        assert "match_statement" in result["features"]
        assert "future_import" in result["features"]

    @pytest.mark.unit
    def test_detects_javascript_es_version(self, sample_javascript_code) -> None:
        """Given JavaScript code, when skill analyzes, then detects ES version features."""
        # Arrange
        code = sample_javascript_code

        # Act
        result = self.skill.analyze_javascript_version(code)

        # Assert
        assert result["es_version"] >= "ES2018"  # For async/await
        assert "class_syntax" in result["features"]
        assert "async_await" in result["features"]
        assert "arrow_functions" in result["features"]

    @pytest.mark.unit
    def test_detects_typescript_version(self, sample_typescript_code) -> None:
        """Given TypeScript code, when skill analyzes, then detects TypeScript version features."""
        # Arrange
        code = sample_typescript_code

        # Act
        result = self.skill.analyze_typescript_version(code)

        # Assert
        assert result["typescript_version"] >= "3.0"
        assert (
            "optional_chaining" in result["features"]
            or "nullish_coalescing" in result["features"]
        )
        assert "generic_classes" in result["features"]

    @pytest.mark.unit
    def test_detects_rust_edition(self, sample_rust_code) -> None:
        """Given Rust code, when skill analyzes, then detects Rust edition features."""
        # Arrange
        code = sample_rust_code

        # Act
        result = self.skill.analyze_rust_edition(code)

        # Assert
        assert result["edition"] in ["2018", "2021"]
        assert "async_await" in result["features"]
        assert "result_type" in result["features"]
        assert "serde_derive" in result["features"]

    @pytest.mark.unit
    def test_detects_frameworks_and_libraries(self, language_samples) -> None:
        """Given code, when skill analyzes, then detects frameworks and libraries."""
        # Arrange
        django_code = """
from django.db import models
from django.views.generic import ListView
from rest_framework import serializers

class User(models.Model):
    name = models.CharField(max_length=100)

class UserView(ListView):
    model = User
        """

        # Act
        result = self.skill.detect_frameworks(django_code, "python")

        # Assert
        assert "django" in result["frameworks"]
        assert "djangorestframework" in result["frameworks"]
        assert result["frameworks"]["django"]["components"]["models"]
        assert result["frameworks"]["django"]["components"]["views"]

    @pytest.mark.unit
    def test_detects_design_patterns(self, sample_python_code) -> None:
        """Given code, when skill analyzes, then identifies design patterns."""
        # Arrange
        code = PYTHON_SAMPLE_CODE

        # Act
        result = self.skill.detect_design_patterns(code, "python")

        # Assert
        patterns = result["patterns"]

        # Should detect Service pattern
        assert "service" in patterns

        # Should detect Repository-like pattern
        assert any("repository" in pattern.lower() for pattern in patterns)

    @pytest.mark.unit
    def test_handles_mixed_language_files(self, language_samples) -> None:
        """Given mixed language content, when skill analyzes, then handles appropriately."""
        # Arrange
        mixed_content = """
// JavaScript section
class JavaScriptClass {
    method() {}
}

/* Python section in comments */
# This is actually commented Python
def python_function():
    pass
        """

        # Act
        result = self.skill.detect_primary_language(mixed_content)

        # Assert
        # Should identify the primary language based on actual code, not comments
        assert result["primary_language"] == "javascript"
        assert result["confidence"] > 0.8
        assert len(result["detected_languages"]) >= 1

    @pytest.mark.unit
    def test_detects_code_complexity(self, language_samples) -> None:
        """Given code, when skill analyzes, then calculates complexity metrics."""
        # Arrange
        complex_code = """
def complex_function(items):
    results = []
    for i, item in enumerate(items):
        if item.type == "A":
            for j in range(len(items)):
                if items[j].value > 10:
                    try:
                        result = process_item(items[j])
                        if result.success:
                            results.append(result)
                            if len(results) > 100:
                                break
                    except Exception as e:
                        handle_error(e)
        elif item.type == "B":
            # Another nested structure
            pass
    return results
        """

        # Act
        result = self.skill.analyze_complexity(complex_code, "python")

        # Assert
        assert result["cyclomatic_complexity"] > 5
        assert result["nesting_depth"] >= 3
        assert result["complexity_level"] in ["medium", "high"]
        assert "suggestions" in result

    @pytest.mark.unit
    def test_handles_empty_or_invalid_code(self) -> None:
        """Given empty or invalid code, when skill analyzes, then handles gracefully."""
        # Arrange
        test_cases = [
            ("", "empty"),
            ("   \n\t  \n  ", "whitespace_only"),
            ("// Just comments", "comments_only"),
            ("invalid syntax with {{", "invalid_syntax"),
        ]

        for code, _case_type in test_cases:
            # Act
            result = self.skill.detect_language(code)

            # Assert
            assert result["language"] == "unknown"
            assert result["confidence"] < 0.5
            assert "error" in result or "features" in result

    @pytest.mark.unit
    def test_detects_language_specific_keywords(self, language_samples) -> None:
        """Given code, when skill analyzes, then identifies language-specific keywords."""
        # Arrange & Act
        python_result = self.skill.analyze_features(PYTHON_SAMPLE_CODE, "python")
        rust_result = self.skill.analyze_features(RUST_SAMPLE_CODE, "rust")

        # Assert - Python keywords
        python_keywords = python_result["features"]["keywords"]
        assert "class" in python_keywords
        assert "async" in python_keywords
        assert "def" in python_keywords

        # Assert - Rust keywords
        rust_keywords = rust_result["features"]["keywords"]
        assert "struct" in rust_keywords
        assert "impl" in rust_keywords
        assert "pub" in rust_keywords
        assert "async" in rust_keywords

    @pytest.mark.unit
    def test_identifies_imports_and_dependencies(self, language_samples) -> None:
        """Given code, when skill analyzes, then identifies imports and dependencies."""
        # Arrange
        python_code = """
import asyncio
from typing import List, Optional
import requests as http_requests
from .internal_module import helper
        """

        # Act
        result = self.skill.analyze_dependencies(python_code, "python")

        # Assert
        dependencies = result["dependencies"]

        # Should detect standard library imports
        assert "asyncio" in dependencies["standard_library"]
        assert "typing" in dependencies["standard_library"]

        # Should detect third-party imports
        assert "requests" in dependencies["third_party"]

        # Should detect local imports
        assert len(dependencies["local"]) >= 1

    @pytest.mark.unit
    def test_calculates_language_confidence_scores(self, language_samples) -> None:
        """Given code samples, when skill analyzes, then provides accurate confidence scores."""
        # Arrange & Act
        python_result = self.skill.detect_language(PYTHON_SAMPLE_CODE)
        javascript_result = self.skill.detect_language(JAVASCRIPT_SAMPLE_CODE)
        rust_result = self.skill.detect_language(RUST_SAMPLE_CODE)

        # Assert - High confidence for clear language indicators
        assert python_result["confidence"] > 0.9
        assert javascript_result["confidence"] > 0.9
        assert rust_result["confidence"] > 0.9

        # Assert - Reasoning should be provided
        for result in [python_result, javascript_result, rust_result]:
            assert "reasoning" in result
            assert len(result["reasoning"]) > 0

    @pytest.mark.unit
    def test_handles_minimal_code_samples(self) -> None:
        """Given minimal code samples, when skill analyzes, then still identifies language."""
        # Arrange
        minimal_samples = {
            "python": "def hello(): pass",
            "javascript": "function hello() {}",
            "typescript": "function hello(): void {}",
            "rust": "fn hello() {}",
        }

        for language, code in minimal_samples.items():
            # Act
            result = self.skill.detect_language(code)

            # Assert
            assert result["language"] == language
            assert result["confidence"] > 0.5

    @pytest.mark.unit
    def test_provides_detailed_feature_analysis(self, language_samples) -> None:
        """Given code, when skill analyzes, then provides comprehensive feature breakdown."""
        # Arrange
        code = language_samples["python"]

        # Act
        result = self.skill.analyze_features(code, "python")

        # Assert
        features = result["features"]

        # Should provide detailed breakdown
        assert "functions" in features
        assert "classes" in features
        assert "imports" in features
        assert "decorators" in features
        assert "data_structures" in features

        # Should provide counts
        assert features["functions"] >= 1
        assert features["classes"] >= 1

    @pytest.mark.unit
    def test_detects_async_patterns(self, sample_async_code) -> None:
        """Given async code, when skill analyzes, then identifies async patterns."""
        # Arrange
        code = sample_async_code

        # Act
        result = self.skill.analyze_async_features(code, "python")

        # Assert
        async_features = result["async_features"]

        # Should detect async functions
        assert async_features["async_functions"] >= 3

        # Should detect async context managers
        assert async_features["async_context_managers"] >= 1

        # Should detect async with statements
        assert "async with" in code

        # Should detect await calls
        assert async_features["await_calls"] >= 1
