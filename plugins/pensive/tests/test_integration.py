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
from pensive.reporting.formatters import (
    MarkdownFormatter,
    SarifFormatter,
)
from pensive.skills.unified_review import UnifiedReviewSkill
from pensive.workflows.code_review import CodeReviewWorkflow
from pensive.workflows.skill_coordinator import SkillCoordinator

# Integration tests - now enabled with full implementations


class TestPensiveIntegration:
    """Integration tests for pensive plugin workflows."""

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_end_to_end_code_review_workflow(
        self, temp_repository
    ) -> None:
        """Given repo code, full review generates a report with
        expected metrics and finding structure.
        """
        # Arrange
        workflow = CodeReviewWorkflow()
        repo_path = temp_repository

        # Act
        review_result = workflow.execute_full_review(repo_path)

        # Assert
        assert isinstance(review_result, dict)
        assert isinstance(review_result["summary"], str)
        assert isinstance(review_result["findings"], list)
        assert isinstance(review_result["recommendations"], list)
        assert isinstance(review_result["metrics"], dict)

        metrics = review_result["metrics"]
        assert metrics["skills_executed"] >= 2
        assert metrics["files_analyzed"] > 0
        assert isinstance(metrics["total_findings"], int)

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_skill_coordination_and_result_consolidation(
        self, temp_repository
    ) -> None:
        """Given two skills, parallel execution returns two results
        and dispatches exactly twice.
        """
        # Arrange
        unified_skill = UnifiedReviewSkill()
        context = Mock()
        context.repo_path = temp_repository
        context.working_dir = temp_repository

        # Act
        skills_to_execute = ["code-reviewer", "api-review"]
        with patch(
            "pensive.skills.unified_review.dispatch_agent",
        ) as mock_dispatch:
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
        assert results[0] == "Code review findings: 3 issues found"
        assert results[1] == "API review findings: 2 issues found"
        assert mock_dispatch.call_count == 2

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_real_repository_analysis(
        self, temp_repository
    ) -> None:
        """Given real Rust repo structure, analysis detects Rust,
        make, and cargo test framework.
        """
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
\tcargo build --release

test:
\tcargo test

clean:
\tcargo clean
            """,
        }

        for file_path, content in files.items():
            full_path = temp_repository / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

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
        assert isinstance(analysis["languages"], dict)
        assert "rust" in analysis["languages"]
        assert isinstance(analysis["build_systems"], list)
        assert "make" in analysis["build_systems"]
        assert isinstance(analysis["test_frameworks"], list)
        assert "cargo" in analysis["test_frameworks"]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_todo_write_integration(
        self, temp_repository
    ) -> None:
        """Given review workflow, result contains list-typed findings
        and dict-typed metrics.
        """
        # Arrange
        workflow = CodeReviewWorkflow()

        # Act
        result = workflow.execute_full_review(temp_repository)

        # Assert
        assert isinstance(result["findings"], list)
        assert isinstance(result["metrics"], dict)

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_error_handling_and_recovery(
        self, temp_repository
    ) -> None:
        """Given a failing Rust skill, workflow continues and
        reports errors or skipped skills.
        """
        # Arrange
        workflow = CodeReviewWorkflow()

        with patch(
            "pensive.skills.rust_review.RustReviewSkill",
        ) as mock_rust_skill:
            mock_rust_skill.return_value.analyze.side_effect = (
                Exception("Rust toolchain not found")
            )

            # Act
            result = workflow.execute_full_review(temp_repository)

            # Assert
            assert isinstance(result, dict)
            has_error_info = (
                "errors" in result or "skipped_skills" in result
            )
            assert has_error_info
            assert isinstance(result.get("findings", []), list)

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_performance_with_large_repository(
        self, temp_repository
    ) -> None:
        """Given 20+ module files, review completes under 30 seconds."""
        # Arrange
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
        execution_time = time.time() - start_time

        # Assert
        assert execution_time < 30
        assert isinstance(result, dict)
        assert result["metrics"]["files_analyzed"] >= 20

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_cross_language_repository_analysis(
        self, temp_repository
    ) -> None:
        """Given JS, Python, and Rust files, analysis detects all
        three languages.
        """
        # Arrange
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
        assert isinstance(analysis["languages"], dict)
        assert len(analysis["languages"]) >= 2
        assert "javascript" in analysis["languages"]
        assert "python" in analysis["languages"]
        assert "rust" in analysis["languages"]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_ci_cd_integration(self, temp_repository) -> None:
        """Given GitHub Actions workflow YAML, CI/CD integration
        detects config and generates valid SARIF output.
        """
        # Arrange
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
        sarif_output = integration.generate_sarif_output(
            temp_repository
        )

        # Assert
        assert config["type"] == "github_actions"
        assert isinstance(sarif_output, dict)
        assert isinstance(sarif_output["runs"], list)
        assert len(sarif_output["runs"]) > 0
        assert "tool" in sarif_output["runs"][0]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_configuration_and_customization(
        self, temp_repository
    ) -> None:
        """Given custom .pensive.yml config, workflow loads and
        applies the skill and exclusion settings.
        """
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
    pattern: 'password.*='
    severity: critical
  - id: require-docs
    pattern: 'pub fn'
    severity: medium
        """)

        config = Configuration.load_from_file(config_file)
        workflow = CodeReviewWorkflow(config=config)

        # Act
        result = workflow.execute_full_review(temp_repository)

        # Assert
        assert isinstance(result, dict)
        assert "unified-review" in config.enabled_skills
        assert "rust-review" in config.enabled_skills
        assert "api-review" in config.enabled_skills
        assert len(config.exclude_patterns) > 0

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_memory_usage_and_resource_management(
        self, temp_repository
    ) -> None:
        """Given 100 large files, memory increase stays under 100 MB."""
        # Arrange
        for i in range(100):
            file_path = temp_repository / f"src/large_file_{i}.rs"
            file_path.write_text("x" * 10000)

        workflow = CodeReviewWorkflow()

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
            assert memory_increase < 100 * 1024 * 1024
        assert isinstance(result, dict)

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_concurrent_skill_execution(
        self, temp_repository
    ) -> None:
        """Given three skills, coordinator dispatches all three
        and returns matching result count.
        """
        # Arrange
        coordinator = SkillCoordinator()
        skills = ["code-reviewer", "api-review", "test-review"]

        # Act
        with patch(
            "pensive.workflows.skill_coordinator.dispatch_agent",
        ) as mock_dispatch:
            mock_dispatch.side_effect = [
                "Code review completed",
                "API review completed",
                "Test review completed",
            ]

            results = coordinator.execute_skills_concurrently(
                skills, temp_repository
            )

        # Assert
        assert len(results) == 3
        assert results[0] == "Code review completed"
        assert results[1] == "API review completed"
        assert results[2] == "Test review completed"
        assert mock_dispatch.call_count == 3

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_output_formatting_and_reporting(
        self, temp_repository
    ) -> None:
        """Given findings, markdown and SARIF formatters produce
        valid output containing finding IDs and locations.
        """
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
                "issue": "Nested loop with O(n^2) complexity",
                "fix": "Consider using HashMap for O(1) lookup",
            },
        ]

        # Act
        markdown_report = MarkdownFormatter().format(
            sample_findings, temp_repository
        )
        sarif_report = SarifFormatter().format(
            sample_findings, temp_repository
        )

        # Assert -- markdown
        assert "SEC001" in markdown_report
        assert "critical" in markdown_report
        assert "src/config.rs:15" in markdown_report

        # Assert -- SARIF is valid JSON with expected structure
        sarif_data = json.loads(sarif_report)
        assert isinstance(sarif_data["runs"], list)
        assert len(sarif_data["runs"]) > 0
        assert "results" in sarif_data["runs"][0]

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_plugin_lifecycle_and_cleanup(
        self, temp_repository
    ) -> None:
        """Given plugin lifecycle, init/execute/cleanup completes
        without raising exceptions.
        """
        # Arrange
        plugin = PensivePlugin()
        plugin.initialize()

        # Act
        try:
            plugin.execute_review(temp_repository)
        finally:
            plugin.cleanup()

        # Assert
        assert isinstance(plugin, PensivePlugin)
