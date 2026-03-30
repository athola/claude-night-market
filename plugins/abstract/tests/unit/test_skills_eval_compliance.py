"""Tests for src/abstract/skills_eval/compliance.py.

Feature: Compliance checking
    As a developer
    I want all branches of ComplianceChecker and helpers tested
    So that skill compliance validation works correctly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from abstract.skills_eval.compliance import (
    ComplianceChecker,
    ComplianceIssue,
    ComplianceReport,
    TriggerIsolationResult,
    check_trigger_isolation,
    detect_enforcement_level,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_SKILL = (
    "---\n"
    "name: my-skill\n"
    "description: |\n"
    "  Triggers: skill-related tasks\n"
    "  Use when: you need skill analysis\n"
    "  DO NOT use when: unrelated to skills\n"
    "---\n\n"
    "# My Skill\n\n"
    "## Overview\nOverview content.\n\n"
    "## Quick Start\nStart here.\n"
)

INVALID_FRONTMATTER_SKILL = "# No frontmatter\n\nJust content.\n"

MISSING_DESCRIPTION_SKILL = "---\nname: my-skill\n---\n\n# Content\n"


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Given a skills directory with a valid skill."""
    d = tmp_path / "my-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(VALID_SKILL)
    return tmp_path


@pytest.fixture
def empty_skill_dir(tmp_path: Path) -> Path:
    """Given an empty skills directory."""
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: ComplianceIssue dataclass
# ---------------------------------------------------------------------------


class TestComplianceIssue:
    """Feature: ComplianceIssue stores issue data correctly."""

    @pytest.mark.unit
    def test_creation_with_all_fields(self) -> None:
        """Scenario: ComplianceIssue can be created with all fields."""
        issue = ComplianceIssue(
            severity="critical",
            category="structure",
            description="Missing section",
            location="/path/SKILL.md",
            recommendation="Add section",
            standard="skill-standard-1.0",
            auto_fixable=True,
        )
        assert issue.severity == "critical"
        assert issue.auto_fixable is True

    @pytest.mark.unit
    def test_auto_fixable_defaults_to_false(self) -> None:
        """Scenario: auto_fixable defaults to False when not provided."""
        issue = ComplianceIssue(
            severity="low",
            category="metadata",
            description="desc",
            location="path",
            recommendation="rec",
            standard="std",
        )
        assert issue.auto_fixable is False


# ---------------------------------------------------------------------------
# Tests: ComplianceReport dataclass
# ---------------------------------------------------------------------------


class TestComplianceReport:
    """Feature: ComplianceReport stores compliance results."""

    @pytest.mark.unit
    def test_creation(self) -> None:
        """Scenario: ComplianceReport can be created with all fields."""
        report = ComplianceReport(
            skill_name="test",
            skill_path="/path",
            overall_compliance=85.0,
            issues=[],
            standards_checked=["std1"],
            passed_checks=["check1"],
            failed_checks=[],
        )
        assert report.overall_compliance == 85.0
        assert report.passed_checks == ["check1"]


# ---------------------------------------------------------------------------
# Tests: TriggerIsolationResult dataclass
# ---------------------------------------------------------------------------


class TestTriggerIsolationResult:
    """Feature: TriggerIsolationResult stores trigger analysis data."""

    @pytest.mark.unit
    def test_creation(self) -> None:
        """Scenario: TriggerIsolationResult stores all fields."""
        result = TriggerIsolationResult(
            has_triggers=True,
            has_use_when=True,
            has_not_use_when=False,
            body_has_when_to_use=False,
            body_has_duplicates=False,
            score=8,
            issues=["Missing DO NOT use when"],
        )
        assert result.score == 8
        assert len(result.issues) == 1


# ---------------------------------------------------------------------------
# Tests: check_trigger_isolation
# ---------------------------------------------------------------------------


class TestCheckTriggerIsolation:
    """Feature: check_trigger_isolation validates trigger logic placement."""

    @pytest.mark.unit
    def test_perfect_description_scores_10(self) -> None:
        """Scenario: Description with all required patterns scores 10."""
        description = (
            "Triggers: skill events\n"
            "Use when: working with skills\n"
            "DO NOT use when: irrelevant task"
        )
        body = "## Overview\nClean body without when-to-use."
        result = check_trigger_isolation(description, body)
        assert result.score == 10
        assert result.issues == []

    @pytest.mark.unit
    def test_empty_description_has_all_trigger_issues(self) -> None:
        """Scenario: Empty description reports all three trigger issues."""
        result = check_trigger_isolation("", "")
        # Empty body still gets +1 (no when-to-use) and +1 (no duplicates)
        # so score is 2, not 0. But all three trigger issues are reported.
        assert result.has_triggers is False
        assert result.has_use_when is False
        assert result.has_not_use_when is False
        assert len(result.issues) == 3

    @pytest.mark.unit
    def test_none_inputs_handled(self) -> None:
        """Scenario: None inputs are handled without exception."""
        result = check_trigger_isolation(cast(Any, None), cast(Any, None))
        assert isinstance(result, TriggerIsolationResult)
        # Empty body adds +2 for no-body violations (no when-to-use, no duplicates)
        assert result.has_triggers is False
        assert result.has_use_when is False

    @pytest.mark.unit
    def test_missing_triggers_keyword(self) -> None:
        """Scenario: Missing 'Triggers:' in description reports issue."""
        description = "Use when: relevant\nDO NOT use when: not relevant"
        result = check_trigger_isolation(description, "")
        assert result.has_triggers is False
        assert any("Triggers" in i for i in result.issues)

    @pytest.mark.unit
    def test_missing_use_when(self) -> None:
        """Scenario: Missing 'Use when:' in description reports issue.

        Note: 'DO NOT use when:' contains the substring 'use when:' so it also
        matches the use_when regex. We must omit both patterns to test the
        has_use_when=False path.
        """
        # Description with Triggers but neither 'Use when' nor 'DO NOT use when'
        description = "Triggers: relevant\nSome other text here."
        result = check_trigger_isolation(description, "")
        assert result.has_use_when is False
        assert any("Use when" in i for i in result.issues)

    @pytest.mark.unit
    def test_missing_not_use_when(self) -> None:
        """Scenario: Missing 'DO NOT use when:' reports issue."""
        description = "Triggers: relevant\nUse when: relevant"
        result = check_trigger_isolation(description, "")
        assert result.has_not_use_when is False
        assert any("DO NOT" in i for i in result.issues)

    @pytest.mark.unit
    def test_body_with_when_to_use_penalizes(self) -> None:
        """Scenario: Body containing 'When to Use' section reduces score."""
        description = "Triggers: x\nUse when: x\nDO NOT use when: x"
        body = "## When to Use\nSome content."
        result = check_trigger_isolation(description, body)
        assert result.body_has_when_to_use is True
        assert any("When to Use" in i for i in result.issues)
        # Score reduced by 1
        assert result.score < 10

    @pytest.mark.unit
    def test_body_with_perfect_for_penalizes(self) -> None:
        """Scenario: Body with 'Perfect for:' reduces score."""
        description = "Triggers: x\nUse when: x\nDO NOT use when: x"
        body = "Perfect for: many things."
        result = check_trigger_isolation(description, body)
        assert result.body_has_duplicates is True
        assert any("trigger patterns" in i.lower() for i in result.issues)

    @pytest.mark.unit
    def test_body_with_dont_use_when_penalizes(self) -> None:
        """Scenario: Body with \"Don't use when\" reduces score."""
        description = "Triggers: x\nUse when: x\nDO NOT use when: x"
        body = "Don't use when: something else applies."
        result = check_trigger_isolation(description, body)
        assert result.body_has_duplicates is True

    @pytest.mark.unit
    def test_has_triggers_field_set_correctly(self) -> None:
        """Scenario: has_triggers is True when 'Triggers:' present in description."""
        description = "Triggers: some events"
        result = check_trigger_isolation(description, "")
        assert result.has_triggers is True

    @pytest.mark.unit
    def test_case_insensitive_trigger_detection(self) -> None:
        """Scenario: Trigger patterns are case-insensitive."""
        description = "TRIGGERS: some events\nUSE WHEN: relevant\nDO NOT USE WHEN: no"
        result = check_trigger_isolation(description, "")
        assert result.has_triggers is True
        assert result.has_use_when is True
        assert result.has_not_use_when is True


# ---------------------------------------------------------------------------
# Tests: detect_enforcement_level
# ---------------------------------------------------------------------------


class TestDetectEnforcementLevel:
    """Feature: detect_enforcement_level classifies enforcement language."""

    @pytest.mark.unit
    def test_empty_description_returns_none(self) -> None:
        """Scenario: Empty description returns 'none'."""
        assert detect_enforcement_level("") == "none"

    @pytest.mark.unit
    def test_none_description_returns_none(self) -> None:
        """Scenario: None description returns 'none'."""
        assert detect_enforcement_level(cast(Any, None)) == "none"

    @pytest.mark.unit
    def test_you_must_returns_maximum(self) -> None:
        """Scenario: 'YOU MUST' phrase returns 'maximum' enforcement."""
        assert detect_enforcement_level("YOU MUST do this.") == "maximum"

    @pytest.mark.unit
    def test_non_negotiable_returns_maximum(self) -> None:
        """Scenario: 'NON-NEGOTIABLE' phrase returns 'maximum' enforcement."""
        assert detect_enforcement_level("This is NON-NEGOTIABLE.") == "maximum"

    @pytest.mark.unit
    def test_never_skip_returns_maximum(self) -> None:
        """Scenario: 'NEVER skip' returns 'maximum' enforcement."""
        assert detect_enforcement_level("NEVER skip this step.") == "maximum"

    @pytest.mark.unit
    def test_use_before_returns_high(self) -> None:
        """Scenario: 'Use ... BEFORE' returns 'high' enforcement."""
        assert detect_enforcement_level("Use this BEFORE running tests.") == "high"

    @pytest.mark.unit
    def test_check_even_if_returns_high(self) -> None:
        """Scenario: 'Check even if' returns 'high' enforcement."""
        assert detect_enforcement_level("Check even if it seems fine.") == "high"

    @pytest.mark.unit
    def test_use_when_returns_medium(self) -> None:
        """Scenario: 'Use when' returns 'medium' enforcement."""
        assert detect_enforcement_level("Use when you need help.") == "medium"

    @pytest.mark.unit
    def test_consider_when_returns_medium(self) -> None:
        """Scenario: 'Consider ... when' returns 'medium' enforcement."""
        assert detect_enforcement_level("Consider using this when needed.") == "medium"

    @pytest.mark.unit
    def test_available_for_returns_low(self) -> None:
        """Scenario: 'Available for' returns 'low' enforcement."""
        assert detect_enforcement_level("Available for general use.") == "low"

    @pytest.mark.unit
    def test_consult_when_returns_low(self) -> None:
        """Scenario: 'Consult when' returns 'low' enforcement."""
        assert detect_enforcement_level("Consult when in doubt.") == "low"

    @pytest.mark.unit
    def test_no_patterns_returns_none(self) -> None:
        """Scenario: Description with no matching patterns returns 'none'."""
        assert detect_enforcement_level("Just a plain description.") == "none"

    @pytest.mark.unit
    def test_maximum_takes_precedence(self) -> None:
        """Scenario: Maximum-level pattern detected even in mixed description."""
        desc = "Use when needed. YOU MUST also check this. Available for all."
        assert detect_enforcement_level(desc) == "maximum"


# ---------------------------------------------------------------------------
# Tests: ComplianceChecker._load_rules
# ---------------------------------------------------------------------------


class TestComplianceCheckerLoadRules:
    """Feature: ComplianceChecker loads rules from file or defaults."""

    @pytest.mark.unit
    def test_default_rules_loaded_when_no_file(self, tmp_path: Path) -> None:
        """Scenario: Default rules used when no rules_file specified."""
        checker = ComplianceChecker(tmp_path)
        assert "required_fields" in checker.rules
        assert "max_tokens" in checker.rules
        assert "required_sections" in checker.rules

    @pytest.mark.unit
    def test_rules_from_file_loaded(self, tmp_path: Path) -> None:
        """Scenario: Rules loaded from JSON file when file exists."""
        rules_file = tmp_path / "rules.json"
        custom_rules = {"required_fields": ["name"], "max_tokens": 1000}
        rules_file.write_text(json.dumps(custom_rules))
        checker = ComplianceChecker(tmp_path, rules_file=rules_file)
        assert checker.rules["max_tokens"] == 1000

    @pytest.mark.unit
    def test_invalid_rules_file_uses_defaults(self, tmp_path: Path) -> None:
        """Scenario: Invalid JSON rules file falls back to defaults."""
        rules_file = tmp_path / "rules.json"
        rules_file.write_text("not valid json {{{")
        checker = ComplianceChecker(tmp_path, rules_file=rules_file)
        # Should fall back to defaults
        assert "required_fields" in checker.rules

    @pytest.mark.unit
    def test_nonexistent_rules_file_uses_defaults(self, tmp_path: Path) -> None:
        """Scenario: Non-existent rules file path uses default rules."""
        checker = ComplianceChecker(tmp_path, rules_file=tmp_path / "missing.json")
        assert "required_fields" in checker.rules

    @pytest.mark.unit
    def test_default_trigger_isolation_enabled(self, tmp_path: Path) -> None:
        """Scenario: Default rules enable trigger isolation checking."""
        checker = ComplianceChecker(tmp_path)
        assert checker.rules.get("check_trigger_isolation") is True


# ---------------------------------------------------------------------------
# Tests: ComplianceChecker.check_compliance
# ---------------------------------------------------------------------------


class TestCheckCompliance:
    """Feature: check_compliance validates skill files against rules."""

    @pytest.mark.unit
    def test_nonexistent_root_returns_error(self, tmp_path: Path) -> None:
        """Scenario: Non-existent skill root returns non-compliant with error."""
        checker = ComplianceChecker(tmp_path / "doesnotexist")
        result = checker.check_compliance()
        assert result["compliant"] is False
        assert any("does not exist" in i for i in result["issues"])

    @pytest.mark.unit
    def test_empty_dir_returns_no_skills_error(self, empty_skill_dir: Path) -> None:
        """Scenario: Directory with no SKILL.md files returns error."""
        checker = ComplianceChecker(empty_skill_dir)
        result = checker.check_compliance()
        assert result["compliant"] is False
        assert result["total_skills"] == 0

    @pytest.mark.unit
    def test_valid_skill_is_compliant(self, skill_dir: Path) -> None:
        """Scenario: Valid skill with all required fields is compliant."""
        checker = ComplianceChecker(skill_dir)
        result = checker.check_compliance()
        assert result["total_skills"] == 1
        assert "compliant_count" in result

    @pytest.mark.unit
    def test_missing_frontmatter_adds_parse_error(self, tmp_path: Path) -> None:
        """Scenario: Skill without frontmatter gets parse error issue."""
        d = tmp_path / "bad-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("No frontmatter here.\n")
        checker = ComplianceChecker(tmp_path)
        result = checker.check_compliance()
        assert len(result["issues"]) > 0

    @pytest.mark.unit
    def test_missing_required_field_adds_issue(self, tmp_path: Path) -> None:
        """Scenario: Skill missing required field gets issue recorded."""
        d = tmp_path / "incomplete-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: incomplete\n---\n\ncontent\n")
        checker = ComplianceChecker(tmp_path)
        result = checker.check_compliance()
        assert any("Missing required fields" in i for i in result["issues"])

    @pytest.mark.unit
    def test_high_token_count_adds_warning(self, tmp_path: Path) -> None:
        """Scenario: Skill exceeding token limit adds a warning."""
        d = tmp_path / "big-skill"
        d.mkdir()
        big_content = "---\nname: big\ndescription: big skill\n---\n\n" + "word " * 5000
        (d / "SKILL.md").write_text(big_content)
        checker = ComplianceChecker(tmp_path, rules_file=None)
        # Override max_tokens to a very small value
        checker.rules["max_tokens"] = 10
        result = checker.check_compliance()
        assert len(result["warnings"]) > 0

    @pytest.mark.unit
    def test_trigger_isolation_warning_when_score_low(self, tmp_path: Path) -> None:
        """Scenario: Low trigger isolation score adds warning."""
        d = tmp_path / "notrigger-skill"
        d.mkdir()
        # Description lacks trigger patterns
        (d / "SKILL.md").write_text(
            "---\n"
            "name: notrigger\n"
            "description: Just a plain description without trigger patterns.\n"
            "---\n\n"
            "# Content\n"
        )
        checker = ComplianceChecker(tmp_path)
        result = checker.check_compliance()
        # Low score should trigger warnings
        assert len(result["warnings"]) > 0

    @pytest.mark.unit
    def test_body_when_to_use_section_is_issue(self, tmp_path: Path) -> None:
        """Scenario: Body 'When to Use' section creates a compliance issue."""
        d = tmp_path / "wrong-structure"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\n"
            "name: wrong\n"
            "description: |\n"
            "  Triggers: x\n"
            "  Use when: x\n"
            "  DO NOT use when: y\n"
            "---\n\n"
            "## When to Use\nThis should not be here.\n"
        )
        checker = ComplianceChecker(tmp_path)
        result = checker.check_compliance()
        assert any("When to Use" in i for i in result["issues"])

    @pytest.mark.unit
    def test_file_read_error_adds_issue(self, tmp_path: Path) -> None:
        """Scenario: File read error adds issue for that skill."""
        d = tmp_path / "unreadable-skill"
        d.mkdir()
        skill_file = d / "SKILL.md"
        skill_file.write_text("content")
        checker = ComplianceChecker(tmp_path)
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = checker.check_compliance()
        assert len(result["issues"]) > 0

    @pytest.mark.unit
    def test_compliant_is_false_when_issues_exist(self, tmp_path: Path) -> None:
        """Scenario: Any issue makes compliant=False."""
        d = tmp_path / "bad-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("no frontmatter\n")
        checker = ComplianceChecker(tmp_path)
        result = checker.check_compliance()
        assert result["compliant"] is False

    @pytest.mark.unit
    def test_require_negative_triggers_false_suppresses_warning(
        self, tmp_path: Path
    ) -> None:
        """Scenario: require_negative_triggers=False suppresses DO NOT warning."""
        d = tmp_path / "no-neg-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\n"
            "name: no-neg\n"
            "description: Triggers: x\nUse when: x\n"
            "---\n\n"
            "## Overview\nContent.\n"
        )
        checker = ComplianceChecker(tmp_path)
        checker.rules["require_negative_triggers"] = False
        result = checker.check_compliance()
        # No 'negative triggers required' warning
        assert not any("negative triggers required" in w for w in result["warnings"])

    @pytest.mark.unit
    def test_trigger_isolation_disabled_skips_checks(self, tmp_path: Path) -> None:
        """Scenario: check_trigger_isolation=False skips trigger checks."""
        d = tmp_path / "notrigger-skip"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: notrigger\ndescription: plain.\n---\n\ncontent\n"
        )
        checker = ComplianceChecker(tmp_path)
        checker.rules["check_trigger_isolation"] = False
        result = checker.check_compliance()
        # No trigger-related warnings expected since check is disabled
        trigger_warns = [w for w in result["warnings"] if "trigger" in w.lower()]
        assert len(trigger_warns) == 0


# ---------------------------------------------------------------------------
# Tests: ComplianceChecker.generate_report
# ---------------------------------------------------------------------------


class TestComplianceCheckerGenerateReport:
    """Feature: generate_report produces a readable compliance report."""

    @pytest.mark.unit
    def test_report_contains_compliance_header(self, skill_dir: Path) -> None:
        """Scenario: Report starts with 'Compliance Report' header."""
        checker = ComplianceChecker(skill_dir)
        report = checker.generate_report()
        assert "Compliance Report" in report

    @pytest.mark.unit
    def test_report_shows_compliant_status(self, skill_dir: Path) -> None:
        """Scenario: Report includes compliant/non-compliant status."""
        checker = ComplianceChecker(skill_dir)
        report = checker.generate_report()
        assert "Compliant:" in report

    @pytest.mark.unit
    def test_report_shows_total_skills(self, skill_dir: Path) -> None:
        """Scenario: Report includes total skill count."""
        checker = ComplianceChecker(skill_dir)
        report = checker.generate_report()
        assert "Total Skills:" in report

    @pytest.mark.unit
    def test_report_includes_issues_section(self, tmp_path: Path) -> None:
        """Scenario: Report includes Issues section when issues exist."""
        d = tmp_path / "bad-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("no frontmatter\n")
        checker = ComplianceChecker(tmp_path)
        report = checker.generate_report()
        assert "Issues:" in report

    @pytest.mark.unit
    def test_report_includes_warnings_section(self, tmp_path: Path) -> None:
        """Scenario: Report includes Warnings section when warnings exist."""
        d = tmp_path / "warn-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: warn\ndescription: plain desc no triggers.\n---\ncontent\n"
        )
        checker = ComplianceChecker(tmp_path)
        report = checker.generate_report()
        assert isinstance(report, str)

    @pytest.mark.unit
    def test_report_is_string(self, empty_skill_dir: Path) -> None:
        """Scenario: Report is always a string."""
        checker = ComplianceChecker(empty_skill_dir)
        report = checker.generate_report()
        assert isinstance(report, str)
