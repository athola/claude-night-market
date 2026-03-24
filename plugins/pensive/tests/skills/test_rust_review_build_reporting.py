"""Tests for RustReviewSkill build configuration and reporting.

Covers:
- TestRustReviewBuildReporting: Cargo.toml dependencies, macros,
  traits, const generics, build optimization, security report
  generation, severity categorization, best practices
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pensive.skills.rust_review import RustReviewSkill


@pytest.mark.unit
class TestRustReviewBuildReporting:
    """Test suite for Rust build configuration and reporting."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = RustReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_cargo_toml_dependencies(self, mock_skill_context) -> None:
        """Given Cargo.toml, skill validates dependencies and features."""
        # Arrange
        cargo_toml_content = """
        [package]
        name = "my-app"
        version = "0.1.0"
        edition = "2021"

        [dependencies]
        serde = "1.0"  # Missing version range
        tokio = { version = "1.0", features = ["full"] }  # Too many features
        rand = "0.8.5"

        # Potential security vulnerabilities
        openssl = "0.10"  # Older version might have vulns
        url = "2.2"       # Should check for latest

        [dev-dependencies]
        tokio-test = "0.4"

        [features]
        default = ["serde", "tokio"]
        experimental = []  # Empty feature
        """

        mock_skill_context.get_file_content.return_value = cargo_toml_content

        # Act
        dependency_analysis = self.skill.analyze_dependencies(mock_skill_context)

        # Assert
        assert "dependencies" in dependency_analysis
        assert "version_issues" in dependency_analysis
        assert "security_concerns" in dependency_analysis
        assert "feature_analysis" in dependency_analysis
        assert len(dependency_analysis["version_issues"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_macro_usage_patterns(self, mock_skill_context) -> None:
        """Given macros, skill identifies problematic patterns."""
        # Arrange
        macro_code = """
        use serde_derive::{Serialize, Deserialize};

        // Good: derive macros
        #[derive(Debug, Clone, Serialize, Deserialize)]
        struct User {
            id: u64,
            name: String,
        }

        // Potentially problematic: custom macros without documentation
        macro_rules! unsafe_macro {
            ($expr:expr) => {
                unsafe { $expr }
            };
        }

        // Good: well-documented macro
        /// Logs a message with timestamp
        macro_rules! log {
            ($($arg:tt)*) => {
                println!("[{}] {}", chrono::Utc::now(), format!($($arg)*))
            };
        }

        // Problematic: macro that hides control flow
        macro_rules! try_unwrap {
            ($expr:expr) => {
                match $expr {
                    Ok(val) => val,
                    Err(_) => return None,  // Hidden early return
                }
            };
        }

        fn example_usage() {
            let data = try_unwrap!(some_operation());
            let unsafe_result = unsafe_macro!(raw_pointer_operation());
        }

        fn some_operation() -> Result<i32, &'static str> {
            Ok(42)
        }

        fn raw_pointer_operation() -> i32 {
            42
        }
        """

        mock_skill_context.get_file_content.return_value = macro_code

        # Act
        macro_analysis = self.skill.analyze_macros(mock_skill_context, "macros.rs")

        # Assert
        assert "custom_macros" in macro_analysis
        assert "derive_macros" in macro_analysis
        assert "problematic_patterns" in macro_analysis
        assert len(macro_analysis["problematic_patterns"]) >= 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzes_trait_implementations(self, mock_skill_context) -> None:
        """Given trait implementations, skill detects related issues."""
        # Arrange
        trait_code = """
        use std::fmt;

        // Good trait definition
        trait Processor {
            type Output;
            fn process(&self) -> Self::Output;
            fn validate(&self) -> bool { true }  // Default implementation
        }

        // Good implementation
        struct DataProcessor {
            data: Vec<i32>,
        }

        impl Processor for DataProcessor {
            type Output = i32;

            fn process(&self) -> Self::Output {
                self.data.iter().sum()
            }
        }

        // Problematic: partial implementation
        trait ComplexTrait {
            fn method_a(&self) -> String;
            fn method_b(&self) -> i32;
            fn method_c(&self) -> bool;
        }

        struct IncompleteImpl;

        impl ComplexTrait for IncompleteImpl {
            fn method_a(&self) -> String {
                "a".to_string()
            }
            // Missing method_b and method_c - compilation error
        }

        // Good: proper error handling in trait
        trait FallibleProcessor {
            fn process(&self) -> Result<String, Box<dyn std::error::Error>>;
        }

        // Problematic: trait object safety issues
        trait NotObjectSafe {
            fn generic_method<T>(&self, item: T) -> T;  // Generic method
            fn static_method() -> i32;  // Static method
        }

        // Good: object-safe trait
        trait ObjectSafe {
            fn process(&self) -> String;
            fn validate(&self) -> bool;
        }
        """

        mock_skill_context.get_file_content.return_value = trait_code

        # Act
        trait_analysis = self.skill.analyze_traits(mock_skill_context, "traits.rs")

        # Assert
        assert "trait_definitions" in trait_analysis
        assert "implementations" in trait_analysis
        assert "object_safety_issues" in trait_analysis
        assert "missing_methods" in trait_analysis

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_checks_const_generic_usage(self, mock_skill_context) -> None:
        """Given const generics, skill validates those patterns."""
        # Arrange
        const_generic_code = """
        // Good: const generic usage
        struct Array<T, const N: usize> {
            data: [T; N],
        }

        impl<T, const N: usize> Array<T, N> {
            fn new(data: [T; N]) -> Self {
                Self { data }
            }

            fn len(&self) -> usize {
                N
            }
        }

        // Problematic: unconstrained const generic
        struct Unconstrained<T, const N: usize> {
            data: Vec<T>,
            phantom: std::marker::PhantomData<[(); N]>,
        }

        impl<T, const N: usize> Unconstrained<T, N> {
            fn method(&self) -> usize {
                N  // N doesn't actually constrain anything
            }
        }

        // Good: bounded const generic
        struct Bounded<const MAX: usize> {
            value: u32,
        }

        impl<const MAX: usize> Bounded<MAX> {
            fn new(value: u32) -> Option<Self> {
                if value <= MAX as u32 {
                    Some(Self { value })
                } else {
                    None
                }
            }
        }

        fn example_usage() {
            let arr = Array::new([1, 2, 3]);
            assert_eq!(arr.len(), 3);

            let bounded = Bounded::<100>::new(42);
            let invalid = Bounded::<100>::new(200);  // Should be None
        }
        """

        mock_skill_context.get_file_content.return_value = const_generic_code

        # Act
        const_generic_analysis = self.skill.analyze_const_generics(
            mock_skill_context,
            "const_generics.rs",
        )

        # Assert
        assert "const_generic_structs" in const_generic_analysis
        assert "bounded_generics" in const_generic_analysis
        assert "unconstrained_usage" in const_generic_analysis
        assert len(const_generic_analysis["unconstrained_usage"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_build_optimization_issues(self, mock_skill_context) -> None:
        """Given build config, skill finds optimization opportunities."""
        # Arrange
        build_files = {
            "Cargo.toml": """
            [package]
            name = "my-app"
            version = "0.1.0"
            edition = "2021"

            [dependencies]
            serde = { version = "1.0", features = ["derive"] }
            """,
            ".cargo/config.toml": """
            [build]
            target = "x86_64-unknown-linux-gnu"

            [target.x86_64-unknown-linux-gnu]
            linker = "clang"
            """,
            "src/main.rs": """
            fn main() {
                println!("Hello, world!");
            }
            """,
        }

        def mock_get_file_content(path):
            return build_files.get(str(path), "")

        mock_skill_context.get_file_content.side_effect = mock_get_file_content
        mock_skill_context.get_files.return_value = list(build_files.keys())

        # Act
        build_analysis = self.skill.analyze_build_configuration(mock_skill_context)

        # Assert
        assert "optimization_level" in build_analysis
        assert "target_specific" in build_analysis
        assert "dependency_optimization" in build_analysis
        assert "recommendations" in build_analysis

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_rust_security_report(self, sample_findings) -> None:
        """Given full Rust analysis, skill creates security-focused summary."""
        # Arrange
        rust_analysis = {
            "unsafe_blocks": 5,
            "unsafe_documented": 2,
            "ownership_violations": 3,
            "data_races": 2,
            "memory_safety_issues": 4,
            "dependency_vulnerabilities": 1,
            "panic_points": 6,
            "security_score": 7.2,
            "findings": sample_findings,
        }

        # Act
        report = self.skill.create_rust_security_report(rust_analysis)

        # Assert
        assert "## Rust Security Assessment" in report
        assert "## Unsafe Code Analysis" in report
        assert "## Memory Safety" in report
        assert "## Concurrency Safety" in report
        assert "## Dependency Security" in report
        assert "5" in report  # unsafe blocks
        assert "7.2" in report  # security score
        assert "unsafe" in report.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_categorizes_rust_issue_severity(self) -> None:
        """Given Rust issues, skill assigns severities."""
        # Arrange
        rust_issues = [
            {"type": "buffer_overflow", "context": "unsafe block"},
            {"type": "data_race", "context": "RefCell across threads"},
            {"type": "unwrap_usage", "context": "in library function"},
            {"type": "missing_docs", "context": "unsafe block"},
            {"type": "deprecated_dependency", "context": "Cargo.toml"},
        ]

        # Act
        categorized = self.skill.categorize_rust_severity(rust_issues)

        # Assert
        severity_map = {issue["type"]: issue["severity"] for issue in categorized}
        assert severity_map["buffer_overflow"] == "critical"
        assert severity_map["data_race"] == "critical"
        assert severity_map["unwrap_usage"] in ["high", "medium"]
        assert severity_map["missing_docs"] in ["medium", "low"]
        assert severity_map["deprecated_dependency"] in ["medium", "high"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_rust_best_practices(self, mock_skill_context) -> None:
        """Given Rust analysis, skill recommends best practices."""
        # Arrange
        codebase_analysis = {
            "uses_unsafe": True,
            "async_code": True,
            "macro_heavy": True,
            "dependency_count": 25,
            "test_coverage": 0.6,
        }

        # Act
        recommendations = self.skill.generate_rust_recommendations(codebase_analysis)

        # Assert
        assert len(recommendations) > 0
        categories = [rec["category"] for rec in recommendations]
        assert "unsafe" in categories
        assert "async" in categories
        assert "testing" in categories
        assert "dependencies" in categories

        for rec in recommendations:
            assert "practice" in rec
            assert "benefit" in rec
            assert "implementation" in rec
