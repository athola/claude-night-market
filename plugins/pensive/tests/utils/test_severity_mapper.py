"""Unit tests for the severity mapper utility.

Tests issue categorization, severity weights,
and severity counting functionality.
"""

from __future__ import annotations

import pytest

from pensive.utils.severity_mapper import SeverityMapper


class TestSeverityMapper:
    """Test suite for SeverityMapper utility class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.mapper = SeverityMapper()

    # ========================================================================
    # categorize tests
    # ========================================================================

    @pytest.mark.unit
    def test_categorize_known_issue_types(self) -> None:
        """Given issues with known types, assigns correct severity."""
        # Arrange
        issues = [
            {"type": "sql_injection", "issue": "SQL injection in query"},
            {"type": "null_pointer", "issue": "Potential null dereference"},
            {"type": "performance", "issue": "Slow loop detected"},
        ]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["severity"] == "critical"
        assert categorized[1]["severity"] == "high"
        assert categorized[2]["severity"] == "low"

    @pytest.mark.unit
    def test_categorize_unknown_type_defaults_to_low(self) -> None:
        """Given unknown issue type, defaults to low severity."""
        # Arrange
        issues = [{"type": "unknown_type", "issue": "Some unknown issue"}]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["severity"] == "low"

    @pytest.mark.unit
    def test_categorize_with_custom_map(self) -> None:
        """Given custom severity map, uses custom mappings."""
        # Arrange
        issues = [{"type": "custom_issue", "issue": "A custom issue"}]
        custom_map = {"custom_issue": "critical"}

        # Act
        categorized = SeverityMapper.categorize(issues, custom_map)

        # Assert
        assert categorized[0]["severity"] == "critical"

    @pytest.mark.unit
    def test_categorize_custom_map_overrides_default(self) -> None:
        """Given custom map, overrides default mapping."""
        # Arrange - performance is normally "low"
        issues = [{"type": "performance", "issue": "Performance issue"}]
        custom_map = {"performance": "high"}

        # Act
        categorized = SeverityMapper.categorize(issues, custom_map)

        # Assert
        assert categorized[0]["severity"] == "high"

    @pytest.mark.unit
    def test_categorize_preserves_original_fields(self) -> None:
        """Given issue with extra fields, preserves them."""
        # Arrange
        issues = [
            {
                "type": "memory_leak",
                "issue": "Memory leak detected",
                "file": "main.py",
                "line": 42,
                "custom_field": "custom_value",
            }
        ]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["file"] == "main.py"
        assert categorized[0]["line"] == 42
        assert categorized[0]["custom_field"] == "custom_value"

    @pytest.mark.unit
    def test_categorize_does_not_modify_original(self) -> None:
        """Given issues, does not modify original list."""
        # Arrange
        original_issues = [{"type": "security", "issue": "Security issue"}]
        original_copy = [dict(issue) for issue in original_issues]

        # Act
        _ = SeverityMapper.categorize(original_issues)

        # Assert
        assert original_issues == original_copy
        assert "severity" not in original_issues[0]

    @pytest.mark.unit
    def test_categorize_keyword_override_critical(self) -> None:
        """Given critical keywords in description, overrides to critical."""
        # Arrange - type is "performance" (low) but description mentions SQL injection
        issues = [{"type": "performance", "issue": "SQL injection vulnerability found"}]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["severity"] == "critical"

    @pytest.mark.unit
    def test_categorize_keyword_override_high(self) -> None:
        """Given high-severity keywords in description, overrides to high."""
        # Arrange
        issues = [{"type": "style", "issue": "Dangerous code pattern detected"}]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["severity"] == "high"

    @pytest.mark.unit
    def test_categorize_empty_list(self) -> None:
        """Given empty issues list, returns empty list."""
        # Act
        categorized = SeverityMapper.categorize([])

        # Assert
        assert categorized == []

    @pytest.mark.unit
    def test_categorize_case_insensitive(self) -> None:
        """Given mixed case type, matches regardless of case."""
        # Arrange
        issues = [{"type": "SQL_INJECTION", "issue": "Issue"}]

        # Act
        categorized = SeverityMapper.categorize(issues)

        # Assert
        assert categorized[0]["severity"] == "critical"

    # ========================================================================
    # get_severity_weight tests
    # ========================================================================

    @pytest.mark.unit
    def test_get_severity_weight_critical(self) -> None:
        """Given critical severity, returns highest weight."""
        # Act
        weight = SeverityMapper.get_severity_weight("critical")

        # Assert
        assert weight == 10.0

    @pytest.mark.unit
    def test_get_severity_weight_high(self) -> None:
        """Given high severity, returns appropriate weight."""
        # Act
        weight = SeverityMapper.get_severity_weight("high")

        # Assert
        assert weight == 5.0

    @pytest.mark.unit
    def test_get_severity_weight_medium(self) -> None:
        """Given medium severity, returns appropriate weight."""
        # Act
        weight = SeverityMapper.get_severity_weight("medium")

        # Assert
        assert weight == 2.5

    @pytest.mark.unit
    def test_get_severity_weight_low(self) -> None:
        """Given low severity, returns lowest weight."""
        # Act
        weight = SeverityMapper.get_severity_weight("low")

        # Assert
        assert weight == 1.0

    @pytest.mark.unit
    def test_get_severity_weight_unknown_defaults_to_low(self) -> None:
        """Given unknown severity, defaults to low weight."""
        # Act
        weight = SeverityMapper.get_severity_weight("unknown")

        # Assert
        assert weight == 1.0

    @pytest.mark.unit
    def test_get_severity_weight_case_insensitive(self) -> None:
        """Given mixed case severity, matches correctly."""
        # Act
        weight = SeverityMapper.get_severity_weight("CRITICAL")

        # Assert
        assert weight == 10.0

    # ========================================================================
    # count_by_severity tests
    # ========================================================================

    @pytest.mark.unit
    def test_count_by_severity_mixed(self) -> None:
        """Given mixed severity issues, counts correctly."""
        # Arrange
        issues = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "low"},
            {"severity": "low"},
        ]

        # Act
        counts = SeverityMapper.count_by_severity(issues)

        # Assert
        assert counts == {"critical": 1, "high": 2, "medium": 1, "low": 3}

    @pytest.mark.unit
    def test_count_by_severity_empty_list(self) -> None:
        """Given empty issues list, returns all zeros."""
        # Act
        counts = SeverityMapper.count_by_severity([])

        # Assert
        assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 0}

    @pytest.mark.unit
    def test_count_by_severity_only_critical(self) -> None:
        """Given only critical issues, counts correctly."""
        # Arrange
        issues = [{"severity": "critical"}, {"severity": "critical"}]

        # Act
        counts = SeverityMapper.count_by_severity(issues)

        # Assert
        assert counts == {"critical": 2, "high": 0, "medium": 0, "low": 0}

    @pytest.mark.unit
    def test_count_by_severity_missing_field(self) -> None:
        """Given issues without severity field, defaults to low."""
        # Arrange
        issues = [{"issue": "No severity specified"}]

        # Act
        counts = SeverityMapper.count_by_severity(issues)

        # Assert
        assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 1}

    @pytest.mark.unit
    def test_count_by_severity_unknown_level(self) -> None:
        """Given unknown severity level, does not count it."""
        # Arrange
        issues = [{"severity": "unknown_level"}]

        # Act
        counts = SeverityMapper.count_by_severity(issues)

        # Assert
        # Unknown levels are not counted
        assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 0}

    @pytest.mark.unit
    def test_count_by_severity_case_insensitive(self) -> None:
        """Given mixed case severities, counts correctly."""
        # Arrange
        issues = [
            {"severity": "CRITICAL"},
            {"severity": "High"},
            {"severity": "MEDIUM"},
            {"severity": "low"},
        ]

        # Act
        counts = SeverityMapper.count_by_severity(issues)

        # Assert
        assert counts == {"critical": 1, "high": 1, "medium": 1, "low": 1}


class TestSeverityMapContent:
    """Test the default severity mapping content."""

    @pytest.mark.unit
    def test_security_issues_are_critical(self) -> None:
        """Security-related issues should be critical severity."""
        security_types = [
            "sql_injection",
            "timing_attack",
            "security",
            "command_injection",
            "privilege_escalation",
            "buffer_overflow",
            "data_race",
        ]

        for issue_type in security_types:
            issues = [{"type": issue_type, "issue": "test"}]
            categorized = SeverityMapper.categorize(issues)
            assert categorized[0]["severity"] == "critical", (
                f"{issue_type} should be critical"
            )

    @pytest.mark.unit
    def test_memory_issues_are_high(self) -> None:
        """Memory-related issues should be high severity."""
        memory_types = ["null_pointer", "race_condition", "memory_leak", "unsafe_code"]

        for issue_type in memory_types:
            issues = [{"type": issue_type, "issue": "test"}]
            categorized = SeverityMapper.categorize(issues)
            assert categorized[0]["severity"] == "high", f"{issue_type} should be high"

    @pytest.mark.unit
    def test_code_quality_issues_are_low_or_medium(self) -> None:
        """Code quality issues should be low or medium severity."""
        quality_types = ["performance", "style", "type_confusion"]

        for issue_type in quality_types:
            issues = [{"type": issue_type, "issue": "test"}]
            categorized = SeverityMapper.categorize(issues)
            assert categorized[0]["severity"] in [
                "low",
                "medium",
            ], f"{issue_type} should be low or medium"
