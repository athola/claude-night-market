"""Tests for compliance checking functionality."""

import json

import pytest

from abstract.skills_eval import ComplianceChecker
from abstract.skills_eval.compliance import (
    TriggerIsolationResult,
    check_trigger_isolation,
    detect_enforcement_level,
)


class TestComplianceChecker:
    """Test cases for ComplianceChecker."""

    # Test constants
    EXPECTED_TOTAL_SKILLS = 3
    CUSTOM_MAX_TOKENS = 1500

    @pytest.fixture
    def sample_skill_content(self) -> str:
        """Sample skill content for testing."""
        return """---
name: test-skill
description: A test skill for compliance checking
category: testing
dependencies: []
---

# Test Skill

## Overview
This is a test skill.

## Quick Start
Use this skill by running the command.

## Detailed Resources
More information here.
"""

    @pytest.fixture
    def temp_skill_dir(self, tmp_path, sample_skill_content):
        """Create a temporary directory with a skill file."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_content)
        return tmp_path

    def test_checker_initialization(self, temp_skill_dir) -> None:
        """Test checker initializes correctly."""
        checker = ComplianceChecker(temp_skill_dir)
        assert checker.skill_root == temp_skill_dir
        assert isinstance(checker.rules, dict)

    def test_check_basic_compliance(self, temp_skill_dir) -> None:
        """Test basic compliance checking."""
        checker = ComplianceChecker(temp_skill_dir)
        results = checker.check_compliance()

        assert "compliant" in results
        assert "issues" in results
        assert "warnings" in results
        assert isinstance(results["issues"], list)
        assert isinstance(results["warnings"], list)

    def test_check_missing_frontmatter(self, tmp_path) -> None:
        """Test compliance check for missing frontmatter."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter content")

        checker = ComplianceChecker(tmp_path)
        results = checker.check_compliance()

        assert not results["compliant"]
        assert any("frontmatter" in issue.lower() for issue in results["issues"])

    def test_check_required_fields(self, tmp_path) -> None:
        """Test compliance check for required fields."""
        skill_dir = tmp_path / "incomplete-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: incomplete-skill
---

# Incomplete Skill
Missing required fields.
""")

        checker = ComplianceChecker(tmp_path)
        results = checker.check_compliance()

        assert not results["compliant"]
        assert any("description" in issue.lower() for issue in results["issues"])

    def test_check_token_limits(self, temp_skill_dir) -> None:
        """Test token limit compliance checking."""
        checker = ComplianceChecker(temp_skill_dir)
        # Create a skill that exceeds token limits
        large_content = "# Large Skill\n" + "This is content. " * 1000
        (temp_skill_dir / "test-skill" / "SKILL.md").write_text(large_content)

        results = checker.check_compliance()

        # Should have warnings about token usage
        assert len(results["warnings"]) > 0

    def test_generate_report(self, temp_skill_dir) -> None:
        """Test compliance report generation."""
        checker = ComplianceChecker(temp_skill_dir)
        checker.check_compliance()
        report = checker.generate_report()

        assert "Compliance Report" in report
        assert str(temp_skill_dir) in report
        assert "compliant" in report.lower()

    def test_check_multiple_skills(self, tmp_path) -> None:
        """Test compliance checking across multiple skills."""
        # Create multiple skills
        for i in range(3):
            skill_dir = tmp_path / f"skill-{i}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: skill-{i}
description: Skill number {i}
category: testing
---

# Skill {i}
""")

        checker = ComplianceChecker(tmp_path)
        results = checker.check_compliance()

        assert "total_skills" in results
        assert results["total_skills"] == self.EXPECTED_TOTAL_SKILLS

    def test_load_custom_rules(self, tmp_path) -> None:
        """Test loading custom compliance rules."""
        custom_rules = {
            "required_fields": ["name", "description", "category", "version"],
            "max_tokens": self.CUSTOM_MAX_TOKENS,
            "required_sections": ["Overview", "Usage"],
        }

        rules_file = tmp_path / "compliance_rules.json"
        rules_file.write_text(json.dumps(custom_rules))

        checker = ComplianceChecker(tmp_path, rules_file=rules_file)

        assert checker.rules["max_tokens"] == self.CUSTOM_MAX_TOKENS
        assert "version" in checker.rules["required_fields"]


class TestCheckTriggerIsolation:
    """BDD-style tests for check_trigger_isolation function.

    Tests the trigger isolation analysis that validates skill descriptions
    contain proper trigger patterns and bodies don't duplicate them.
    """

    def test_perfect_trigger_isolation_scores_maximum(self) -> None:
        """Test that all trigger patterns present yields maximum score.

        GIVEN a description with Triggers, Use when, and DO NOT use when
        AND a body without trigger duplication
        WHEN check_trigger_isolation is called
        THEN score is 10, all flags True, no issues.
        """
        description = (
            "Triggers: code changes. "
            "Use when: writing new features. "
            "DO NOT use when: quick fixes - use hotfix instead."
        )
        body = "# Implementation\nSome content without trigger patterns."

        result = check_trigger_isolation(description, body)

        assert result.score == 10
        assert result.has_triggers is True
        assert result.has_use_when is True
        assert result.has_not_use_when is True
        assert result.body_has_when_to_use is False
        assert result.body_has_duplicates is False
        assert result.issues == []

    def test_missing_all_triggers_scores_minimum(self) -> None:
        """Test that missing all triggers yields minimum score with issues."""
        result = check_trigger_isolation("A simple skill description.", "# Content")

        assert result.score == 2  # Only points for clean body
        assert result.has_triggers is False
        assert result.has_use_when is False
        assert result.has_not_use_when is False
        assert "Missing 'Triggers:'" in str(result.issues)
        assert "Missing 'Use when:'" in str(result.issues)
        assert "Missing 'DO NOT use when:'" in str(result.issues)

    def test_body_when_to_use_violation_flagged(self) -> None:
        """Test that body containing 'When to Use' section is flagged."""
        description = "Triggers: always. Use when: needed. DO NOT use when: never."
        body = "## When to Use\nUse this for testing purposes."

        result = check_trigger_isolation(description, body)

        assert result.body_has_when_to_use is True
        assert result.score < 10
        assert "Body contains 'When to Use' section" in str(result.issues)

    def test_body_perfect_for_pattern_flagged(self) -> None:
        """Test that body containing 'Perfect for:' pattern is flagged."""
        description = "Triggers: always. Use when: coding. DO NOT use when: sleeping."
        body = "# Skill\nPerfect for: quick prototyping."

        result = check_trigger_isolation(description, body)

        assert result.body_has_duplicates is True
        assert "duplicate" in str(result.issues).lower()

    def test_none_inputs_handled_gracefully(self) -> None:
        """Test that None inputs don't raise and return valid result."""
        result = check_trigger_isolation(None, None)  # type: ignore[arg-type]

        assert isinstance(result, TriggerIsolationResult)
        assert result.score >= 0
        assert result.has_triggers is False

    def test_empty_strings_handled(self) -> None:
        """Test that empty strings return minimum score."""
        result = check_trigger_isolation("", "")

        assert result.score == 2  # Only body cleanliness points
        assert len(result.issues) == 3  # All three trigger patterns missing

    def test_case_insensitive_trigger_matching(self) -> None:
        """Test that trigger patterns are matched case-insensitively."""
        description = "TRIGGERS: always. use WHEN: needed. do not USE when: never."

        result = check_trigger_isolation(description, "# Body")

        assert result.has_triggers is True
        assert result.has_use_when is True
        assert result.has_not_use_when is True

    def test_partial_triggers_partial_score(self) -> None:
        """Test that partial triggers yield partial score."""
        description = "Use when: writing tests."

        result = check_trigger_isolation(description, "# Body")

        assert result.has_use_when is True
        assert result.has_triggers is False
        assert result.has_not_use_when is False
        assert result.score == 5  # 3 for use_when + 2 for clean body


class TestDetectEnforcementLevel:
    """BDD-style tests for detect_enforcement_level function.

    Tests the enforcement language detection that classifies
    skill descriptions by their intensity level.
    """

    def test_maximum_enforcement_you_must(self) -> None:
        """Test 'YOU MUST' pattern returns maximum enforcement."""
        assert detect_enforcement_level("YOU MUST use this skill") == "maximum"

    def test_maximum_enforcement_non_negotiable(self) -> None:
        """Test 'NON-NEGOTIABLE' pattern returns maximum enforcement."""
        assert detect_enforcement_level("This is NON-NEGOTIABLE") == "maximum"

    def test_maximum_enforcement_never_skip(self) -> None:
        """Test 'NEVER skip' pattern returns maximum enforcement."""
        assert detect_enforcement_level("NEVER skip this step") == "maximum"

    def test_high_enforcement_use_before(self) -> None:
        """Test 'Use...BEFORE' pattern returns high enforcement."""
        assert detect_enforcement_level("Use BEFORE committing code") == "high"

    def test_high_enforcement_check_even_if(self) -> None:
        """Test 'Check even if' pattern returns high enforcement."""
        assert detect_enforcement_level("Check even if tests pass") == "high"

    def test_medium_enforcement_use_when(self) -> None:
        """Test 'Use when' pattern returns medium enforcement."""
        assert detect_enforcement_level("Use when writing new code") == "medium"

    def test_medium_enforcement_consider_when(self) -> None:
        """Test 'Consider...when' pattern returns medium enforcement."""
        desc = "Consider this approach when refactoring"
        assert detect_enforcement_level(desc) == "medium"

    def test_low_enforcement_available_for(self) -> None:
        """Test 'Available for' pattern returns low enforcement."""
        assert detect_enforcement_level("Available for optional use") == "low"

    def test_low_enforcement_consult_when(self) -> None:
        """Test 'Consult when' pattern returns low enforcement."""
        assert detect_enforcement_level("Consult when unsure") == "low"

    def test_no_enforcement_patterns(self) -> None:
        """Test that no enforcement patterns returns 'none'."""
        assert detect_enforcement_level("A simple skill description") == "none"

    def test_priority_ordering_maximum_wins(self) -> None:
        """Test that maximum enforcement takes precedence over lower levels."""
        mixed = "YOU MUST use this. Use when needed. Available for all."
        assert detect_enforcement_level(mixed) == "maximum"

    def test_priority_ordering_high_over_medium(self) -> None:
        """Test that high enforcement takes precedence over medium."""
        mixed = "Use BEFORE committing. Use when writing code."
        assert detect_enforcement_level(mixed) == "high"

    def test_none_input_returns_none(self) -> None:
        """Test that None input returns 'none' without raising."""
        assert detect_enforcement_level(None) == "none"  # type: ignore[arg-type]

    def test_empty_string_returns_none(self) -> None:
        """Test that empty string returns 'none'."""
        assert detect_enforcement_level("") == "none"

    def test_case_insensitive_matching(self) -> None:
        """Test that pattern matching is case-insensitive."""
        assert detect_enforcement_level("you must do this") == "maximum"
        assert detect_enforcement_level("You Must Do This") == "maximum"
