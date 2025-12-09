"""
Unit tests for the unified review skill.

Tests the intelligent skill selection logic and orchestration
of multiple review skills based on repository characteristics.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the skill we're testing
from pensive.skills.unified_review import UnifiedReviewSkill


class TestUnifiedReviewSkill:
    """Test suite for UnifiedReviewSkill business logic."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.skill = UnifiedReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path("/tmp/test_repo")
        self.mock_context.working_dir = Path("/tmp/test_repo")

    @pytest.mark.unit
    def test_detects_rust_project_by_cargo_toml(self, mock_skill_context):
        """Given a repository with Cargo.toml, when skill detects languages, then identifies Rust."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Cargo.toml",
            "src/main.rs",
            "src/lib.rs"
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "rust" in languages
        assert languages["rust"]["files"] == 2  # main.rs and lib.rs
        assert "cargo_toml" in languages["rust"]

    @pytest.mark.unit
    def test_detects_python_project_by_requirements(self, mock_skill_context):
        """Given a repository with requirements.txt, when skill detects languages, then identifies Python."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "requirements.txt",
            "setup.py",
            "src/app.py",
            "tests/test_app.py"
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "python" in languages
        assert languages["python"]["files"] == 2
        assert "test_files" in languages["python"]
        assert languages["python"]["test_files"] == 1

    @pytest.mark.unit
    def test_detects_javascript_project_by_package_json(self, mock_skill_context):
        """Given a repository with package.json, when skill detects languages, then identifies JavaScript."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "package.json",
            "src/index.js",
            "src/utils.js",
            "dist/bundle.js"
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "javascript" in languages
        assert "typescript" in languages  # Should detect TypeScript too
        assert languages["javascript"]["files"] >= 2

    @pytest.mark.unit
    def test_detects_makefile_build_system(self, mock_skill_context):
        """Given a repository with Makefile, when skill detects build systems, then identifies make."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Makefile",
            "src/main.c",
            "src/utils.c"
        ]

        # Act
        build_systems = self.skill.detect_build_systems(mock_skill_context)

        # Assert
        assert "make" in build_systems
        assert "makefile" in build_systems

    @pytest.mark.unit
    def test_selects_rust_review_for_rust_project(self, mock_skill_context):
        """Given a Rust project, when skill selects reviews, then includes rust-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Cargo.toml",
            "src/main.rs"
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "rust-review" in selected_skills
        assert "code-reviewer" in selected_skills  # General review always included

    @pytest.mark.unit
    def test_selects_test_review_for_projects_with_tests(self, mock_skill_context):
        """Given a project with test files, when skill selects reviews, then includes test-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/app.py",
            "tests/test_app.py",
            "test/integration_test.py"
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "test-review" in selected_skills

    @pytest.mark.unit
    def test_selects_makefile_review_for_make_projects(self, mock_skill_context):
        """Given a project with Makefile, when skill selects reviews, then includes makefile-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Makefile",
            "src/main.c"
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "makefile-review" in selected_skills

    @pytest.mark.unit
    def test_selects_math_review_for_mathematical_code(self, mock_skill_context):
        """Given mathematical code patterns, when skill selects reviews, then includes math-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/algorithms.py",
            "src/matrix_math.py"
        ]
        mock_skill_context.get_file_content.return_value = """
        import numpy as np
        from scipy.linalg import svd

        def matrix_decomposition(matrix):
            return svd(matrix)

        def calculate_eigenvalues(matrix):
            return np.linalg.eigvals(matrix)
        """

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "math-review" in selected_skills

    @pytest.mark.unit
    def test_excludes_irrelevant_skills_for_simple_project(self, mock_skill_context):
        """Given a simple project, when skill selects reviews, then excludes specialized skills."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/utils.js",
            "README.md"
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "rust-review" not in selected_skills
        assert "math-review" not in selected_skills
        assert "makefile-review" not in selected_skills
        assert "code-reviewer" in selected_skills  # Always included

    @pytest.mark.unit
    def test_prioritizes_findings_by_severity(self, sample_findings):
        """Given multiple findings, when skill prioritizes, then orders by severity."""
        # Arrange
        findings = sample_findings  # Contains high, medium, low severity findings

        # Act
        prioritized = self.skill.prioritize_findings(findings)

        # Assert
        assert len(prioritized) == 3
        assert prioritized[0]["severity"] == "high"
        assert prioritized[1]["severity"] == "medium"
        assert prioritized[2]["severity"] == "low"

    @pytest.mark.unit
    def test_consolidates_duplicate_findings(self, sample_findings):
        """Given duplicate findings, when skill consolidates, then removes duplicates."""
        # Arrange
        duplicate_findings = [*sample_findings, {"id": "SEC001", "title": "Hardcoded API Key", "location": "src/auth.ts:5", "severity": "high", "issue": "API key is hardcoded", "fix": "Use environment variables"}]

        # Act
        consolidated = self.skill.consolidate_findings(duplicate_findings)

        # Assert
        # Should have one less finding due to consolidation
        assert len(consolidated) == len(duplicate_findings) - 1
        # Check that SEC001 appears only once
        sec_findings = [f for f in consolidated if f["id"] == "SEC001"]
        assert len(sec_findings) == 1

    @pytest.mark.unit
    def test_generates_comprehensive_summary(self, sample_findings):
        """Given findings, when skill generates summary, then includes all key sections."""
        # Arrange
        findings = sample_findings

        # Act
        summary = self.skill.generate_summary(findings)

        # Assert
        assert "## Summary" in summary
        assert "## Findings" in summary
        assert "## Action Items" in summary
        assert "## Recommendation" in summary
        assert "SEC001" in summary  # Finding IDs should be present
        assert "high" in summary.lower()  # Severity levels should be present

    @pytest.mark.unit
    def test_recommends_approval_for_no_critical_issues(self):
        """Given no critical findings, when skill recommends, then suggests approval."""
        # Arrange
        findings = [
            {
                "id": "STYLE001",
                "severity": "low",
                "issue": "Minor style issue"
            }
        ]

        # Act
        recommendation = self.skill.generate_recommendation(findings)

        # Assert
        assert "Approve" in recommendation
        assert "Block" not in recommendation

    @pytest.mark.unit
    def test_recommends_block_for_critical_security_issues(self):
        """Given critical security issues, when skill recommends, then suggests block."""
        # Arrange
        findings = [
            {
                "id": "SEC001",
                "severity": "critical",
                "issue": "SQL injection vulnerability"
            }
        ]

        # Act
        recommendation = self.skill.generate_recommendation(findings)

        # Assert
        assert "Block" in recommendation
        assert "critical" in recommendation.lower()

    @pytest.mark.unit
    def test_creates_actionable_items(self, sample_findings):
        """Given findings, when skill creates action items, then assigns owners and deadlines."""
        # Arrange
        findings = sample_findings

        # Act
        action_items = self.skill.create_action_items(findings)

        # Assert
        assert len(action_items) == len(findings)
        for item in action_items:
            assert "action" in item
            assert "owner" in item
            assert "deadline" in item
            # High severity items should have sooner deadlines
            if item["severity"] == "high":
                assert "today" in item["deadline"].lower() or "asap" in item["deadline"].lower()

    @pytest.mark.unit
    def test_handles_empty_repository_gracefully(self, mock_skill_context):
        """Given an empty repository, when skill analyzes, then returns appropriate response."""
        # Arrange
        mock_skill_context.get_files.return_value = []

        # Act
        result = self.skill.analyze(mock_skill_context)

        # Assert
        assert "no code files found" in result.lower() or "empty" in result.lower()
        assert result is not None
        assert len(result) > 0

    @pytest.mark.unit
    def test_detects_api_exports(self, mock_skill_context):
        """Given code with exports, when skill analyzes, then identifies API surface."""
        # Arrange
        mock_skill_context.get_files.return_value = ["src/api.ts"]
        mock_skill_context.get_file_content.return_value = """
        export interface User {
            id: number;
            name: string;
        }

        export class AuthService {
            public login(): void {}
            public logout(): void {}
        }

        export function calculateTotal(items: Item[]): number {
            return items.reduce((sum, item) => sum + item.price, 0);
        }
        """

        # Act
        api_surface = self.skill.detect_api_surface(mock_skill_context)

        # Assert
        assert "exports" in api_surface
        assert api_surface["exports"] >= 3  # User interface, AuthService class, calculateTotal function
        assert "classes" in api_surface
        assert api_surface["classes"] >= 1  # AuthService

    @pytest.mark.unit
    async def test_executes_selected_skills_concurrently(self, mock_skill_context):
        """Given multiple skills, when skill executes, then runs them concurrently."""
        # Arrange
        selected_skills = ["code-reviewer", "rust-review", "test-review"]

        with patch('pensive.skills.unified_review.dispatch_agent') as mock_dispatch:
            # Configure mock dispatch to return different results for each skill
            mock_dispatch.side_effect = [
                "Code review findings...",
                "Rust review findings...",
                "Test review findings..."
            ]

            # Act
            results = await self.skill.execute_skills_concurrently(
                selected_skills,
                mock_skill_context
            )

            # Assert
            assert len(results) == len(selected_skills)
            # Verify all skills were dispatched
            assert mock_dispatch.call_count == len(selected_skills)

    @pytest.mark.unit
    def test_calculate_review_confidence_score(self, sample_findings):
        """Given findings and analysis, when skill calculates confidence, then returns appropriate score."""
        # Arrange
        analysis_data = {
            "languages_detected": ["rust", "javascript"],
            "files_analyzed": 10,
            "skills_executed": 3
        }

        # Act
        confidence = self.skill.calculate_confidence_score(sample_findings, analysis_data)

        # Assert
        assert 0 <= confidence <= 100  # Score should be between 0 and 100
        # More findings and comprehensive analysis should increase confidence
        assert confidence > 50  # Should have reasonable confidence with sample data

    @pytest.mark.unit
    def test_formats_findings_consistently(self, sample_findings):
        """Given findings, when skill formats, then maintains consistent structure."""
        # Arrange
        findings = sample_findings

        # Act
        formatted = self.skill.format_findings(findings)

        # Assert
        for finding in formatted:
            assert "id" in finding
            assert "title" in finding
            assert "location" in finding
            assert "severity" in finding
            assert "issue" in finding
            assert "fix" in finding
            # Check that severity is one of allowed values
            assert finding["severity"] in ["critical", "high", "medium", "low"]
