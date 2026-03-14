"""Unit tests for the unified review skill.

Tests the intelligent skill selection logic and orchestration
of multiple review skills based on repository characteristics.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the skill we're testing
from pensive.skills.base import AnalysisResult
from pensive.skills.unified_review import UnifiedReviewSkill


class TestUnifiedReviewSkill:
    """Test suite for UnifiedReviewSkill business logic."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = UnifiedReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_rust_project_by_cargo_toml(self, mock_skill_context) -> None:
        """Given Cargo.toml, skill detects Rust with correct file count."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Cargo.toml",
            "src/main.rs",
            "src/lib.rs",
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "rust" in languages
        assert languages["rust"]["files"] == 3
        assert languages["rust"]["cargo_toml"] is True
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_python_project_by_requirements(self, mock_skill_context) -> None:
        """Given requirements.txt, skill detects Python with test flag."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "requirements.txt",
            "setup.py",
            "src/app.py",
            "tests/test_app.py",
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "python" in languages
        assert languages["python"]["files"] == 4
        assert languages["python"]["test_files"] is True
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.unit
    def test_detects_javascript_project_by_package_json(
        self, mock_skill_context
    ) -> None:
        """Given package.json, skill detects JavaScript."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "package.json",
            "src/index.js",
            "src/utils.js",
            "dist/bundle.js",
        ]

        # Act
        languages = self.skill.detect_languages(mock_skill_context)

        # Assert
        assert "javascript" in languages
        assert languages["javascript"]["files"] >= 2
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_makefile_build_system(self, mock_skill_context) -> None:
        """Given Makefile, skill returns both 'make' and 'makefile'."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Makefile",
            "src/main.c",
            "src/utils.c",
        ]

        # Act
        build_systems = self.skill.detect_build_systems(mock_skill_context)

        # Assert
        assert isinstance(build_systems, list)
        assert "make" in build_systems
        assert "makefile" in build_systems
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_selects_rust_review_for_rust_project(self, mock_skill_context) -> None:
        """Given Rust project, skill selects rust-review and base reviewer."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Cargo.toml",
            "src/main.rs",
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert isinstance(selected_skills, list)
        assert "rust-review" in selected_skills
        assert "code-reviewer" in selected_skills
        mock_skill_context.get_files.assert_called()

    @pytest.mark.unit
    def test_selects_test_review_for_projects_with_tests(
        self, mock_skill_context
    ) -> None:
        """Given test files, skill selects test-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/app.py",
            "tests/test_app.py",
            "test/integration_test.py",
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "test-review" in selected_skills
        mock_skill_context.get_files.assert_called()

    @pytest.mark.unit
    def test_selects_makefile_review_for_make_projects(
        self, mock_skill_context
    ) -> None:
        """Given Makefile, skill selects makefile-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "Makefile",
            "src/main.c",
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "makefile-review" in selected_skills
        mock_skill_context.get_files.assert_called()

    @pytest.mark.unit
    def test_selects_math_review_for_mathematical_code(
        self, mock_skill_context
    ) -> None:
        """Given math library imports, skill selects math-review."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/algorithms.py",
            "src/matrix_math.py",
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
        mock_skill_context.get_file_content.assert_called()

    @pytest.mark.unit
    def test_excludes_irrelevant_skills_for_simple_project(
        self, mock_skill_context
    ) -> None:
        """Given simple JS project, skill excludes specialized skills."""
        # Arrange
        mock_skill_context.get_files.return_value = [
            "src/utils.js",
            "README.md",
        ]

        # Act
        selected_skills = self.skill.select_review_skills(mock_skill_context)

        # Assert
        assert "rust-review" not in selected_skills
        assert "math-review" not in selected_skills
        assert "makefile-review" not in selected_skills
        assert "code-reviewer" in selected_skills

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_prioritizes_findings_by_severity(self, sample_findings) -> None:
        """Given mixed-severity findings, sorts high before low."""
        # Arrange
        findings = sample_findings

        # Act
        prioritized = self.skill.prioritize_findings(findings)

        # Assert
        assert len(prioritized) == 3
        assert prioritized[0]["severity"] == "high"
        assert prioritized[0]["id"] == "SEC001"
        assert prioritized[1]["severity"] == "medium"
        assert prioritized[1]["id"] == "BUG001"
        assert prioritized[2]["severity"] == "low"
        assert prioritized[2]["id"] == "PERF001"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_consolidates_duplicate_findings(self, sample_findings) -> None:
        """Given duplicate SEC001 entries, deduplicates to one."""
        # Arrange
        duplicate_findings = [
            *sample_findings,
            {
                "id": "SEC001",
                "title": "Hardcoded API Key",
                "location": "src/auth.ts:5",
                "severity": "high",
                "issue": "API key is hardcoded",
                "fix": "Use environment variables",
            },
        ]

        # Act
        consolidated = self.skill.consolidate_findings(duplicate_findings)

        # Assert
        assert len(consolidated) == 3
        sec_findings = [f for f in consolidated if f["id"] == "SEC001"]
        assert len(sec_findings) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generates_summary_with_all_sections(self, sample_findings) -> None:
        """Given findings, summary contains all required sections."""
        # Arrange / Act
        summary = self.skill.generate_summary(sample_findings)

        # Assert
        assert "## Summary" in summary
        assert "## Findings" in summary
        assert "## Action Items" in summary
        assert "## Recommendation" in summary
        assert "SEC001" in summary
        assert "BUG001" in summary
        assert "PERF001" in summary
        assert "high" in summary.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_approval_for_no_critical_issues(self) -> None:
        """Given only low-severity findings, recommends Approve."""
        # Arrange
        findings = [
            {
                "id": "STYLE001",
                "severity": "low",
                "issue": "Minor style issue",
            },
        ]

        # Act
        recommendation = self.skill.generate_recommendation(findings)

        # Assert
        assert "Approve" in recommendation
        assert "Block" not in recommendation

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommends_block_for_critical_security_issues(self) -> None:
        """Given critical severity, recommends Block."""
        # Arrange
        findings = [
            {
                "id": "SEC001",
                "severity": "critical",
                "issue": "SQL injection vulnerability",
            },
        ]

        # Act
        recommendation = self.skill.generate_recommendation(findings)

        # Assert
        assert recommendation == (
            "Block - Critical security/functionality issues must be resolved"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_repository_gracefully(self, mock_skill_context) -> None:
        """Given empty file list, returns AnalysisResult with warning."""
        # Arrange
        mock_skill_context.get_files.return_value = []

        # Act
        result = self.skill.analyze(mock_skill_context)

        # Assert
        assert isinstance(result, AnalysisResult)
        assert len(result.warnings) == 1
        assert "No code files found" in result.warnings[0]
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_api_exports(self, mock_skill_context) -> None:
        """Given TypeScript exports, detect_api_surface counts them."""
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
        assert api_surface["exports"] == 3
        assert api_surface["classes"] == 1
        assert api_surface["functions"] == 1
        assert api_surface["interfaces"] == 1
        mock_skill_context.get_files.assert_called_once()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_executes_selected_skills_concurrently(self, mock_skill_context) -> None:
        """Given skill list, dispatches each and returns all results."""
        # Arrange
        selected_skills = [
            "code-reviewer",
            "rust-review",
            "test-review",
        ]

        with patch(
            "pensive.skills.unified_review.dispatch_agent",
        ) as mock_dispatch:
            mock_dispatch.side_effect = [
                "Code review findings...",
                "Rust review findings...",
                "Test review findings...",
            ]

            # Act
            results = self.skill.execute_skills(
                selected_skills,
                mock_skill_context,
            )

            # Assert
            assert len(results) == 3
            assert results[0] == "Code review findings..."
            assert results[1] == "Rust review findings..."
            assert results[2] == "Test review findings..."
            assert mock_dispatch.call_count == 3

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_formats_findings_consistently(self, sample_findings) -> None:
        """Given raw findings, formatted output has all required keys
        with valid severity values.
        """
        # Act
        formatted = self.skill.format_findings(sample_findings)

        # Assert
        assert len(formatted) == 3
        required_keys = {"id", "title", "location", "severity", "issue", "fix"}
        for finding in formatted:
            assert set(finding.keys()) == required_keys
            assert finding["severity"] in {
                "critical",
                "high",
                "medium",
                "low",
            }
        assert formatted[0]["id"] == "SEC001"
        assert formatted[1]["id"] == "BUG001"
        assert formatted[2]["id"] == "PERF001"
