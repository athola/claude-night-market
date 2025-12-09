"""Tests for abstract_validator.py."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from abstract_validator import AbstractValidator


class TestAbstractValidator:
    """Test cases for AbstractValidator."""

    def test_validator_initialization(self, temp_skill_dir) -> None:
        """Test validator initializes correctly."""
        validator = AbstractValidator(temp_skill_dir)
        assert validator.plugin_root == temp_skill_dir
        assert isinstance(validator.skill_files, list)

    def test_scan_infrastructure_basic(
        self, temp_skill_dir, sample_skill_content
    ) -> None:
        """Test basic infrastructure scanning."""
        skill_dir = temp_skill_dir / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_content)

        validator = AbstractValidator(temp_skill_dir)
        result = validator.scan_infrastructure()

        assert "skills_found" in result
        assert "skills_with_patterns" in result
        assert "infrastructure_provided" in result
        assert "issues" in result

    def test_validate_patterns_missing_frontmatter(self, temp_skill_dir) -> None:
        """Test validation catches missing frontmatter."""
        skill_dir = temp_skill_dir / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter content")

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        assert any("Missing frontmatter" in issue for issue in issues)

    def test_validate_patterns_incomplete_frontmatter(self, temp_skill_dir) -> None:
        """Test validation catches incomplete frontmatter."""
        skill_dir = temp_skill_dir / "incomplete-skill"
        skill_dir.mkdir()
        content = """---
name: test
"""
        (skill_dir / "SKILL.md").write_text(content)

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        assert any("Incomplete frontmatter" in issue for issue in issues)

    def test_validate_patterns_missing_required_fields(self, temp_skill_dir) -> None:
        """Test validation catches missing required fields."""
        skill_dir = temp_skill_dir / "missing-fields"
        skill_dir.mkdir()
        content = """---
name: test
---

Content.
"""
        (skill_dir / "SKILL.md").write_text(content)

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        # Should flag missing description and category
        assert any("description" in issue for issue in issues)
        assert any("category" in issue for issue in issues)

    def test_check_progressive_disclosure(self, temp_skill_dir) -> None:
        """Test progressive disclosure validation."""
        skill_dir = temp_skill_dir / "no-overview"
        skill_dir.mkdir()
        content = """---
name: test-skill
description: Test
category: test
---

# No Overview Section

Some content.
"""
        (skill_dir / "SKILL.md").write_text(content)

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        assert any("overview" in issue.lower() for issue in issues)

    def test_check_dependency_cycles(self, temp_skill_dir) -> None:
        """Test dependency cycle detection."""
        # Create skill A depending on B
        skill_a = temp_skill_dir / "skill-a"
        skill_a.mkdir()
        (skill_a / "SKILL.md").write_text("""---
name: skill-a
description: Skill A
category: test
dependencies: [skill-b]
---

Content A.
""")

        # Create skill B depending on A (cycle!)
        skill_b = temp_skill_dir / "skill-b"
        skill_b.mkdir()
        (skill_b / "SKILL.md").write_text("""---
name: skill-b
description: Skill B
category: test
dependencies: [skill-a]
---

Content B.
""")

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        assert any("cycle" in issue.lower() for issue in issues)

    def test_check_hub_spoke_pattern_violation(self, temp_skill_dir) -> None:
        """Test hub-spoke pattern validation."""
        skill_dir = temp_skill_dir / "modular-skill"
        skill_dir.mkdir()
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()

        # Create main skill that doesn't reference modules
        (skill_dir / "SKILL.md").write_text("""---
name: modular-skill
description: Modular skill
category: test
---

Content without module references.
""")

        # Create module that isn't referenced
        (modules_dir / "unreferenced.md").write_text("Module content")

        validator = AbstractValidator(temp_skill_dir)
        issues = validator.validate_patterns()

        assert any("hub-spoke" in issue.lower() for issue in issues)

    def test_generate_report(self, temp_skill_dir, sample_skill_content) -> None:
        """Test report generation."""
        skill_dir = temp_skill_dir / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_content)

        validator = AbstractValidator(temp_skill_dir)
        report = validator.generate_report()

        assert "Abstract Plugin Infrastructure Report" in report
        assert "Plugin Root:" in report
        assert "Skill Files:" in report

    def test_fix_patterns_dry_run(self, temp_skill_dir) -> None:
        """Test fix patterns in dry run mode."""
        skill_dir = temp_skill_dir / "fixable-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("No frontmatter")

        validator = AbstractValidator(temp_skill_dir)
        fixes = validator.fix_patterns(dry_run=True)

        # Should report what would be fixed
        assert len(fixes) > 0
        assert any("frontmatter" in fix.lower() for fix in fixes)

        # File should be unchanged
        content = (skill_dir / "SKILL.md").read_text()
        assert not content.startswith("---")

    def test_fix_patterns_actual_fix(self, temp_skill_dir) -> None:
        """Test actual fixing of patterns."""
        skill_dir = temp_skill_dir / "fixable-skill"
        skill_dir.mkdir()
        original_content = "No frontmatter"
        (skill_dir / "SKILL.md").write_text(original_content)

        validator = AbstractValidator(temp_skill_dir)
        fixes = validator.fix_patterns(dry_run=False)

        # Should have applied fixes
        assert len(fixes) > 0

        # File should now have frontmatter
        content = (skill_dir / "SKILL.md").read_text()
        assert content.startswith("---")
        assert original_content in content
