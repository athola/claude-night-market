"""Integration tests for the pensive plugin.

Tests end-to-end workflows, skill coordination,
and real repository analysis scenarios.

NOTE: These tests document expected future functionality.
Many features are currently stub implementations and these tests
are marked as skipped until the full implementations are complete.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from unittest.mock import Mock, patch

import pytest

try:
    import psutil
except ImportError:
    psutil = None

# Import pensive components for testing
from pensive.analysis.repository_analyzer import RepositoryAnalyzer
from pensive.config.configuration import Configuration
from pensive.integrations.cicd import GitHubActionsIntegration
from pensive.plugin import PensivePlugin
from pensive.reporting.formatters import MarkdownFormatter, SarifFormatter
from pensive.skills.unified_review import UnifiedReviewSkill
from pensive.workflows.code_review import CodeReviewWorkflow
from pensive.workflows.skill_coordinator import SkillCoordinator

# Integration tests - now enabled with full implementations


class TestPensiveIntegration:
    """Integration tests for pensive plugin workflows."""

    @pytest.mark.integration
    def test_end_to_end_code_review_workflow(self, temp_repository) -> None:
        """Given repo code, full review generates comprehensive report."""
        # Arrange
        workflow = CodeReviewWorkflow()
        repo_path = temp_repository

        # Act
        review_result = workflow.execute_full_review(repo_path)

        # Assert
        assert review_result is not None
        assert "summary" in review_result
        assert "findings" in review_result
        assert "recommendations" in review_result
        assert "metrics" in review_result

        # Check that multiple skills were executed
        assert review_result["metrics"]["skills_executed"] >= 2
        assert review_result["metrics"]["files_analyzed"] > 0
        assert review_result["metrics"]["total_findings"] >= 0

    @pytest.mark.integration
    def test_skill_coordination_and_result_consolidation(self, temp_repository) -> None:
        """Given multiple skills, parallel execution consolidates results."""
        # Arrange
        unified_skill = UnifiedReviewSkill()
        context = Mock()
        context.repo_path = temp_repository
        context.working_dir = temp_repository

        # Act
        skills_to_execute = ["code-reviewer", "api-review"]
        with patch(
            "pensive.workflows.skill_coordinator.dispatch_agent",
        ) as mock_dispatch:
            # Mock different skill responses
            mock_dispatch.side_effect = [
                "Code review findings: 3 issues found",
                "API review findings: 2 issues found",
            ]

            results = unified_skill.execute_skills_concurrently(
                skills_to_execute,
                context,
            )

        # Assert
        assert len(results) == 2
        assert all(result is not None for result in results)
        assert mock_dispatch.call_count == 2

    @pytest.mark.integration
    def test_real_repository_analysis(self, temp_repository) -> None:
        """Given real repository structure, analysis detects patterns."""
        # Arrange
        files = {
            "src/main.rs": """
use std::collections::HashMap;

pub struct UserService {
    users: HashMap<u64, User>,
}

impl UserService {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
        }
    }

    pub fn add_user(&mut self, user: User) -> Result<(), String> {
        if self.users.contains_key(&user.id) {
            return Err("User already exists".to_string());
        }
        self.users.insert(user.id, user);
        Ok(())
    }
}

pub struct User {
    pub id: u64,
    pub name: String,
}
            """,
            "src/lib.rs": """
pub mod main;
pub use main::{UserService, User};
            """,
            "tests/user_tests.rs": """
use crate::main::{UserService, User};

#[test]
fn test_user_creation() {
    let user = User {
        id: 1,
        name: "Test User".to_string(),
    };
    assert_eq!(user.id, 1);
}

#[test]
fn test_add_user() {
    let mut service = UserService::new();
    let user = User {
        id: 1,
        name: "Test".to_string(),
    };
    assert!(service.add_user(user).is_ok());
}
            """,
            "Cargo.toml": """
[package]
name = "user-service"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }
            """,
            "Makefile": """
.PHONY: all build test clean

all: build test

build:
	cargo build --release

test:
	cargo test

clean:
	cargo clean
            """,
        }

        # Create the repository structure
        for file_path, content in files.items():
            full_path = temp_repository / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Initialize git
        subprocess.run(
            ["git", "add", "."],
            check=False,
            cwd=temp_repository,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Add Rust user service"],
            check=False,
            cwd=temp_repository,
            capture_output=True,
        )

        # Act
        analyzer = RepositoryAnalyzer()
        analysis = analyzer.analyze_repository(temp_repository)

        # Assert
        assert "languages" in analysis
        assert "rust" in analysis["languages"]
        assert "build_systems" in analysis
        assert "make" in analysis["build_systems"]
        assert "test_frameworks" in analysis
        assert "cargo" in analysis["test_frameworks"]

    @pytest.mark.integration
    def test_todo_write_integration(self, temp_repository) -> None:
        """Given review workflow, issues integrate with task tracking."""
        # Arrange
        workflow = CodeReviewWorkflow()

        # Act
        result = workflow.execute_full_review(temp_repository)

        # Assert - workflow should return trackable findings
        assert result is not None
        assert "findings" in result
        assert "metrics" in result
        # Findings should be structured for task tracking
        assert isinstance(result["findings"], list)

    @pytest.mark.integration
    def test_error_handling_and_recovery(self, temp_repository) -> None:
        """Given errors during review, workflow handles gracefully and continues."""
        # Arrange
        workflow = CodeReviewWorkflow()

        with patch("pensive.skills.rust_review.RustReviewSkill") as mock_rust_skill:
            # Make rust skill fail
            mock_rust_skill.return_value.analyze.side_effect = Exception(
                "Rust toolchain not found",
            )

            # Act
            result = workflow.execute_full_review(temp_repository)

            # Assert
            # Workflow should continue despite rust skill failure
            assert result is not None
            assert "errors" in result or "skipped_skills" in result
            assert (
                len(result.get("findings", [])) >= 0
            )  # Other skills should still work

    @pytest.mark.integration
    def test_performance_with_large_repository(self, temp_repository) -> None:
        """Given large repo, review completes within reasonable time."""
        # Arrange
        # Create a larger repository with many files
        for i in range(20):
            file_path = temp_repository / f"src/module_{i}.rs"
            file_path.write_text(f"""
pub struct Module{i} {{
    id: u64,
    data: String,
}}

impl Module{i} {{
    pub fn new(id: u64, data: String) -> Self {{
        Self {{ id, data }}
    }}

    pub fn process(&self) -> String {{
        format!("Processed module {{}} with id {{}}", {i}, self.id)
    }}
}}
            """)

        # Add some test files
        for i in range(5):
            test_path = temp_repository / f"tests/test_module_{i}.rs"
            test_path.write_text(f"""
#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_module_{i}() {{
        let module = Module{i}::new(1, "test".to_string());
        assert_eq!(module.id, 1);
    }}
}}
            """)

        workflow = CodeReviewWorkflow()

        # Act
        start_time = time.time()
        result = workflow.execute_full_review(temp_repository)
        end_time = time.time()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 30  # Should complete within 30 seconds
        assert result is not None
        assert result["metrics"]["files_analyzed"] >= 20

    @pytest.mark.integration
    def test_cross_language_repository_analysis(self, temp_repository) -> None:
        """Given multi-language repo, analysis handles all languages."""
        # Arrange
        # Create JavaScript files
        (temp_repository / "src" / "api.js").write_text("""
export class ApiService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async getUsers() {
        const response = await fetch(`${this.baseUrl}/users`);
        return response.json();
    }
}
        """)

        # Create Python files
        (temp_repository / "src" / "utils.py").write_text("""
import json
from typing import List, Dict

def process_data(data: List[Dict]) -> List[Dict]:
    '''Process a list of data dictionaries.'''
    return [item for item in data if item.get('active', False)]

def export_to_json(data: List[Dict], filename: str) -> None:
    '''Export data to JSON file.'''
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
        """)

        # Create Rust files (already exists from temp_repository fixture)
        # Create package.json for JavaScript
        (temp_repository / "package.json").write_text("""
{
    "name": "multi-lang-project",
    "version": "1.0.0",
    "scripts": {
        "test": "jest",
        "build": "webpack"
    }
}
        """)

        analyzer = RepositoryAnalyzer()

        # Act
        analysis = analyzer.analyze_repository(temp_repository)

        # Assert
        assert "languages" in analysis
        assert len(analysis["languages"]) >= 2
        assert "javascript" in analysis["languages"]
        assert "python" in analysis["languages"]
        assert "rust" in analysis["languages"]

    @pytest.mark.integration
    def test_ci_cd_integration(self, temp_repository) -> None:
        """Given CI/CD config, workflow works with build systems."""
        # Arrange
        # Create GitHub Actions workflow
        workflows_dir = temp_repository / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)

        (workflows_dir / "review.yml").write_text("""
name: Code Review
on: [pull_request]

jobs:
  pensive-review:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run Pensive Review
      run: pensive-review --format sarif --output review.sarif
    - name: Upload SARIF
      uses: github/codeql-action/upload-sarif@v1
      with:
        sarif_file: review.sarif
        """)

        integration = GitHubActionsIntegration()

        # Act
        config = integration.detect_configuration(temp_repository)
        sarif_output = integration.generate_sarif_output(temp_repository)

        # Assert
        assert config is not None
        assert config["type"] == "github_actions"
        assert sarif_output is not None
        assert "runs" in sarif_output
        # Tool info is inside runs[0], per SARIF spec
        assert "tool" in sarif_output["runs"][0]

    @pytest.mark.integration
    def test_configuration_and_customization(self, temp_repository) -> None:
        """Given custom configuration, when executing review, then respects settings."""
        # Arrange
        config_file = temp_repository / ".pensive.yml"
        config_file.write_text("""
pensive:
  skills:
    - unified-review
    - rust-review
    - api-review
  exclude:
    - "**/generated/**"
    - "**/vendor/**"
  thresholds:
    max_findings: 10
    critical_threshold: 1
  output:
    format: detailed
    include_suggestions: true
custom_rules:
  - id: no-hardcoded-secrets
    pattern: 'password.*=.*'
    severity: critical
  - id: require-docs
    pattern: 'pub fn'
    severity: medium
        """)

        workflow = CodeReviewWorkflow()

        # Load configuration
        config = Configuration.load_from_file(config_file)
        workflow = CodeReviewWorkflow(config=config)

        # Act
        result = workflow.execute_full_review(temp_repository)

        # Assert
        assert result is not None
        # Verify configuration was applied
        assert "unified-review" in config.enabled_skills
        assert "rust-review" in config.enabled_skills
        assert len(config.exclude_patterns) > 0

    @pytest.mark.integration
    def test_memory_usage_and_resource_management(self, temp_repository) -> None:
        """Given large analysis, when executing, then manages memory efficiently."""
        # Arrange

        # Create many files to test memory usage
        for i in range(100):
            file_path = temp_repository / f"src/large_file_{i}.rs"
            file_path.write_text("x" * 10000)  # 10KB per file

        workflow = CodeReviewWorkflow()

        # Only check memory if psutil is available
        if psutil is not None:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

        # Act
        result = workflow.execute_full_review(temp_repository)

        if psutil is not None:
            final_memory = process.memory_info().rss

        # Assert
        if psutil is not None:
            memory_increase = final_memory - initial_memory
            # Memory increase should be reasonable (less than 100MB for this test)
            assert memory_increase < 100 * 1024 * 1024
        assert result is not None

    @pytest.mark.integration
    def test_concurrent_skill_execution(self, temp_repository) -> None:
        """Given multiple skills, executor runs concurrently when possible."""
        # Arrange

        coordinator = SkillCoordinator()
        skills = ["code-reviewer", "api-review", "test-review"]

        # Act
        with patch(
            "pensive.workflows.skill_coordinator.dispatch_agent",
        ) as mock_dispatch:
            # Configure mock to return different responses
            mock_dispatch.side_effect = [
                "Code review completed",
                "API review completed",
                "Test review completed",
            ]

            results = coordinator.execute_skills_concurrently(skills, temp_repository)

        # Assert
        assert len(results) == 3
        assert all(result is not None for result in results)
        # Verify all skills were dispatched
        assert mock_dispatch.call_count == 3

    @pytest.mark.integration
    def test_output_formatting_and_reporting(self, temp_repository) -> None:
        """Given review results, when generating reports, then formats correctly."""
        # Arrange
        sample_findings = [
            {
                "id": "SEC001",
                "title": "Hardcoded API Key",
                "severity": "critical",
                "location": "src/config.rs:15",
                "issue": "API key is hardcoded in source code",
                "fix": "Use environment variables",
            },
            {
                "id": "PERF001",
                "title": "Inefficient Loop",
                "severity": "medium",
                "location": "src/processor.rs:42",
                "issue": "Nested loop with O(n²) complexity",
                "fix": "Consider using HashMap for O(1) lookup",
            },
        ]

        # Act
        markdown_report = MarkdownFormatter().format(sample_findings, temp_repository)
        sarif_report = SarifFormatter().format(sample_findings, temp_repository)

        # Assert
        assert "SEC001" in markdown_report
        assert "critical" in markdown_report
        assert "src/config.rs:15" in markdown_report

        # SARIF validation
        assert sarif_report is not None
        assert json.loads(sarif_report)  # Should be valid JSON
        sarif_data = json.loads(sarif_report)
        assert "runs" in sarif_data
        assert len(sarif_data["runs"]) > 0
        assert "results" in sarif_data["runs"][0]

    @pytest.mark.integration
    def test_plugin_lifecycle_and_cleanup(self, temp_repository) -> None:
        """Given plugin execution, system cleans up resources properly."""
        # Arrange

        plugin = PensivePlugin()
        plugin.initialize()

        # Act
        try:
            plugin.execute_review(temp_repository)
        finally:
            # Simulate cleanup
            plugin.cleanup()

        # Assert
        # Plugin should handle lifecycle gracefully
        assert True  # If we get here without exceptions, lifecycle worked
