"""Tests for base review skill classes.

Tests the BaseReviewSkill class and associated dataclasses.
"""

from __future__ import annotations

from typing import ClassVar
from unittest.mock import Mock

import pytest

from pensive.skills.base import (
    AnalysisResult,
    ApiExport,
    BaseReviewSkill,
    ReviewFinding,
)
from pensive.utils import content_parser
from pensive.utils.severity_mapper import categorize


class TestReviewFinding:
    """Test the ReviewFinding dataclass."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_finding_with_required_fields(self) -> None:
        """Given required fields, creates finding correctly."""
        finding = ReviewFinding(
            file="src/main.py",
            line=42,
            severity="high",
            category="security",
            message="Potential SQL injection",
        )

        assert finding.file == "src/main.py"
        assert finding.line == 42
        assert finding.severity == "high"
        assert finding.category == "security"
        assert finding.message == "Potential SQL injection"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_finding_with_optional_fields(self) -> None:
        """Given optional fields, includes them correctly."""
        finding = ReviewFinding(
            file="app.py",
            line=10,
            severity="low",
            category="style",
            message="Long line",
            suggestion="Break into multiple lines",
            code_snippet="x = 1 + 2 + 3 + 4 + 5",
        )

        assert finding.suggestion == "Break into multiple lines"
        assert finding.code_snippet == "x = 1 + 2 + 3 + 4 + 5"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_optional_fields_are_empty(self) -> None:
        """Given no optional fields, defaults to empty strings."""
        finding = ReviewFinding(
            file="test.py",
            line=1,
            severity="info",
            category="docs",
            message="Missing docstring",
        )

        assert finding.suggestion == ""
        assert finding.code_snippet == ""


class TestApiExport:
    """Test the ApiExport dataclass."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_export_with_required_fields(self) -> None:
        """Given required fields, creates export correctly."""
        export = ApiExport(name="calculate", export_type="function")

        assert export.name == "calculate"
        assert export.export_type == "function"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_export_with_optional_fields(self) -> None:
        """Given optional fields, includes them correctly."""
        export = ApiExport(
            name="MyClass",
            export_type="class",
            visibility="protected",
            documentation="A sample class",
            line=100,
        )

        assert export.visibility == "protected"
        assert export.documentation == "A sample class"
        assert export.line == 100

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_visibility_is_public(self) -> None:
        """Given no visibility, defaults to public."""
        export = ApiExport(name="helper", export_type="function")

        assert export.visibility == "public"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_line_is_zero(self) -> None:
        """Given no line number, defaults to zero."""
        export = ApiExport(name="CONSTANT", export_type="const")

        assert export.line == 0


class TestAnalysisResult:
    """Test the AnalysisResult dataclass."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_empty_result(self) -> None:
        """Given no arguments, creates empty result."""
        result = AnalysisResult()

        assert result.issues == []
        assert result.warnings == []
        assert result.info == {}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_result_with_issues(self) -> None:
        """Given issues, stores them correctly."""
        finding = ReviewFinding(
            file="test.py",
            line=1,
            severity="low",
            category="test",
            message="Test issue",
        )
        result = AnalysisResult(issues=[finding])

        assert len(result.issues) == 1
        assert result.issues[0].message == "Test issue"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_result_with_warnings(self) -> None:
        """Given warnings, stores them correctly."""
        result = AnalysisResult(warnings=["Warning 1", "Warning 2"])

        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_creates_result_with_info(self) -> None:
        """Given info dict, stores it correctly."""
        result = AnalysisResult(info={"files_analyzed": 5, "time_taken": 1.5})

        assert result.info["files_analyzed"] == 5
        assert result.info["time_taken"] == 1.5


class TestBaseReviewSkill:
    """Test the BaseReviewSkill class."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_initializes_with_empty_findings(self) -> None:
        """Given new instance, has empty findings list."""
        skill = BaseReviewSkill()

        assert skill.findings == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_default_skill_name(self) -> None:
        """Given base class, has 'base' skill name."""
        skill = BaseReviewSkill()

        assert skill.skill_name == "base"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_empty_supported_languages(self) -> None:
        """Given base class, has empty supported languages."""
        skill = BaseReviewSkill()

        assert skill.supported_languages == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyze_returns_empty_result(self) -> None:
        """Given base implementation, analyze returns empty result."""
        skill = BaseReviewSkill()
        mock_context = Mock()

        result = skill.analyze(mock_context, "test.py")

        assert isinstance(result, AnalysisResult)
        assert result.issues == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generate_report_with_no_findings(self) -> None:
        """Given no findings, returns no issues message."""
        skill = BaseReviewSkill()

        report = skill.generate_report([])

        assert report == "No issues found."

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_generate_report_with_findings(self) -> None:
        """Given findings, generates formatted report."""
        skill = BaseReviewSkill()
        findings = [
            ReviewFinding(
                file="main.py",
                line=10,
                severity="high",
                category="security",
                message="Security issue detected",
                suggestion="Fix the issue",
            ),
            ReviewFinding(
                file="utils.py",
                line=25,
                severity="low",
                category="style",
                message="Style warning",
            ),
        ]

        report = skill.generate_report(findings)

        assert "Found 2 issue(s):" in report
        assert "[high] main.py:10" in report
        assert "Security issue detected" in report
        assert "Suggestion: Fix the issue" in report
        assert "[low] utils.py:25" in report

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_content_with_context_method(self) -> None:
        """Given context with method, extracts content."""
        mock_context = Mock()
        mock_context.get_file_content.return_value = "file content"

        content = content_parser.get_file_content(mock_context)

        assert content == "file content"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_content_with_filename(self) -> None:
        """Given filename, calls context with filename."""
        mock_context = Mock()
        mock_context.get_file_content.return_value = "specific content"

        content = content_parser.get_file_content(mock_context, "specific.py")

        assert content == "specific content"
        mock_context.get_file_content.assert_called_once_with("specific.py")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_content_without_method(self) -> None:
        """Given context without method, returns empty string."""
        mock_context = Mock(spec=[])  # No methods

        content = content_parser.get_file_content(mock_context)

        assert content == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_content_non_string_return(self) -> None:
        """Given context returning non-string, returns empty string."""
        mock_context = Mock()
        mock_context.get_file_content.return_value = None

        content = content_parser.get_file_content(mock_context)

        assert content == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_find_line_basic(self) -> None:
        """Given position, finds correct line number."""
        content = "line1\nline2\nline3"

        line = content_parser.find_line_number(content, 0)  # Start of line 1
        assert line == 1

        line = content_parser.find_line_number(content, 6)  # Start of line 2
        assert line == 2

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_basic(self) -> None:
        """Given line number, extracts snippet."""
        content = "def foo():\n    return True\n"

        snippet = content_parser.extract_code_snippet(content, 1)

        assert "def foo():" in snippet

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_snippet_invalid_line(self) -> None:
        """Given invalid line number, returns empty string."""
        content = "line1\nline2"

        snippet = content_parser.extract_code_snippet(content, 0)
        assert snippet == ""

        snippet = content_parser.extract_code_snippet(content, 100)
        assert snippet == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_categorize_severity_basic(self) -> None:
        """Given issues, categorizes by severity."""
        issues = [
            {"type": "security", "issue": "Security issue"},
            {"type": "performance", "issue": "Performance issue"},
        ]

        categorized = categorize(issues)

        assert len(categorized) == 2


class TestBaseReviewSkillSubclassing:
    """Test that BaseReviewSkill can be properly subclassed."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_subclass_can_override_skill_name(self) -> None:
        """Given subclass, can override skill_name."""

        class CustomSkill(BaseReviewSkill):
            skill_name = "custom"

        skill = CustomSkill()
        assert skill.skill_name == "custom"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_subclass_can_override_supported_languages(self) -> None:
        """Given subclass, can override supported_languages."""

        class PythonSkill(BaseReviewSkill):
            supported_languages: ClassVar[list[str]] = ["python", "cython"]

        skill = PythonSkill()
        assert skill.supported_languages == ["python", "cython"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_subclass_can_override_analyze(self) -> None:
        """Given subclass, can override analyze method."""

        class CustomSkill(BaseReviewSkill):
            def analyze(self, context, file_path):
                finding = ReviewFinding(
                    file=file_path,
                    line=1,
                    severity="high",
                    category="custom",
                    message="Custom finding",
                )
                return AnalysisResult(issues=[finding])

        skill = CustomSkill()
        result = skill.analyze(Mock(), "test.py")

        assert len(result.issues) == 1
        assert result.issues[0].category == "custom"
