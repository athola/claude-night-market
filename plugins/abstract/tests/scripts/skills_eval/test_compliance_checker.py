"""Tests for compliance checking functionality."""

import json

import pytest

from abstract.skills_eval import ComplianceChecker


class TestComplianceChecker:
    """Test cases for ComplianceChecker."""

    # Test constants
    EXPECTED_TOTAL_SKILLS = 3
    CUSTOM_MAX_TOKENS = 1500

    @pytest.fixture
    def sample_skill_content(self):
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

    def test_checker_initialization(self, temp_skill_dir):
        """Test checker initializes correctly."""
        checker = ComplianceChecker(temp_skill_dir)
        assert checker.skill_root == temp_skill_dir
        assert isinstance(checker.rules, dict)

    def test_check_basic_compliance(self, temp_skill_dir):
        """Test basic compliance checking."""
        checker = ComplianceChecker(temp_skill_dir)
        results = checker.check_compliance()

        assert "compliant" in results
        assert "issues" in results
        assert "warnings" in results
        assert isinstance(results["issues"], list)
        assert isinstance(results["warnings"], list)

    def test_check_missing_frontmatter(self, tmp_path):
        """Test compliance check for missing frontmatter."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter content")

        checker = ComplianceChecker(tmp_path)
        results = checker.check_compliance()

        assert not results["compliant"]
        assert any("frontmatter" in issue.lower() for issue in results["issues"])

    def test_check_required_fields(self, tmp_path):
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

    def test_check_token_limits(self, temp_skill_dir):
        """Test token limit compliance checking."""
        checker = ComplianceChecker(temp_skill_dir)
        # Create a skill that exceeds token limits
        large_content = "# Large Skill\n" + "This is content. " * 1000
        (temp_skill_dir / "test-skill" / "SKILL.md").write_text(large_content)

        results = checker.check_compliance()

        # Should have warnings about token usage
        assert len(results["warnings"]) > 0

    def test_generate_report(self, temp_skill_dir):
        """Test compliance report generation."""
        checker = ComplianceChecker(temp_skill_dir)
        checker.check_compliance()
        report = checker.generate_report()

        assert "Compliance Report" in report
        assert str(temp_skill_dir) in report
        assert "compliant" in report.lower()

    def test_check_multiple_skills(self, tmp_path):
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

    def test_load_custom_rules(self, tmp_path):
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
