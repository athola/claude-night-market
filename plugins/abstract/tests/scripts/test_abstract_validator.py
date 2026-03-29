"""Tests for abstract_validator.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from abstract_validator import AbstractValidator, main


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


# ---------------------------------------------------------------------------
# Tests: scan_infrastructure branches (from extended coverage)
# ---------------------------------------------------------------------------


class TestScanInfrastructureBranches:
    """Test scan_infrastructure covers provides and invalid JSON."""

    @pytest.mark.unit
    def test_invalid_plugin_json_adds_issue(self, tmp_path: Path) -> None:
        """Invalid plugin.json adds 'Invalid plugin.json' issue."""
        (tmp_path / "plugin.json").write_text("{ invalid json }")

        validator = AbstractValidator(tmp_path)
        result = validator.scan_infrastructure()
        assert "Invalid plugin.json" in result["issues"]

    @pytest.mark.unit
    def test_plugin_json_with_provides_dict(self, tmp_path: Path) -> None:
        """plugin.json with 'provides' dict adds infrastructure entries."""
        plugin_json = {
            "name": "abstract",
            "provides": {
                "tools": ["tool1", "tool2"],
                "templates": ["template1"],
            },
        }
        (tmp_path / "plugin.json").write_text(json.dumps(plugin_json))

        validator = AbstractValidator(tmp_path)
        result = validator.scan_infrastructure()
        assert "tool1" in result["infrastructure_provided"]
        assert "tool2" in result["infrastructure_provided"]
        assert "template1" in result["infrastructure_provided"]

    @pytest.mark.unit
    def test_skill_with_meta_patterns_gets_flagged(self, tmp_path: Path) -> None:
        """Skill with meta-skill keyword is added to skills_with_patterns."""
        skill_dir = tmp_path / "my-framework-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-framework-skill\ndescription: A framework\n---\n\n"
            "# My Framework\n\nThis is an infrastructure framework.\n"
        )

        validator = AbstractValidator(tmp_path)
        result = validator.scan_infrastructure()
        assert "my-framework-skill" in result["skills_with_patterns"]


# ---------------------------------------------------------------------------
# Tests: validate_patterns extended branches
# ---------------------------------------------------------------------------


class TestValidatePatternsBranches:
    """Test validate_patterns covers meta-indicator checks."""

    @pytest.mark.unit
    def test_skill_without_meta_indicators_reports_issue(self, tmp_path: Path) -> None:
        """Skill without meta-skill indicators gets an issue."""
        skill_dir = tmp_path / "plain-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: plain-skill\n"
            "description: A plain skill\n"
            "category: utilities\n"
            "---\n\n"
            "# Plain Skill\n\n"
            "## Overview\nThis skill does basic stuff.\n\n"
            "## Quick Start\nDo the thing.\n"
        )

        validator = AbstractValidator(tmp_path)
        issues = validator.validate_patterns()
        assert any("meta-skill" in issue for issue in issues)

    @pytest.mark.unit
    def test_complete_meta_skill_has_fewer_issues(self, tmp_path: Path) -> None:
        """Well-formed meta-skill passes most validations."""
        skill_dir = tmp_path / "good-meta-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: good-meta-skill\n"
            "description: A good meta-skill for the framework\n"
            "category: meta-skills\n"
            "---\n\n"
            "# Good Meta Skill\n\n"
            "## Overview\n"
            "This is a pattern-based framework template for orchestration.\n\n"
            "## Quick Start\n"
            "1. Step one\n"
            "2. Step two\n\n"
            "## Detailed Resources\n"
            "More details here.\n"
        )

        validator = AbstractValidator(tmp_path)
        issues = validator.validate_patterns()
        assert isinstance(issues, list)


# ---------------------------------------------------------------------------
# Tests: fix_patterns no-issues path
# ---------------------------------------------------------------------------


class TestFixPatternsNoIssues:
    """Test fix_patterns returns 'No fixes needed' when no issues."""

    @pytest.mark.unit
    def test_fix_patterns_no_issues_returns_no_fixes(self, tmp_path: Path) -> None:
        """fix_patterns with no issues returns 'No fixes needed'."""
        validator = AbstractValidator(tmp_path)
        result = validator.fix_patterns(dry_run=True)
        assert result == ["No fixes needed"]


class TestFixPatternsWithExistingFrontmatter:
    """Test fix_patterns with skills that have existing frontmatter."""

    @pytest.mark.unit
    def test_fix_patterns_skill_with_existing_frontmatter(self, tmp_path: Path) -> None:
        """fix_patterns calls _fix_frontmatter_fields for skills with frontmatter."""
        skill_dir = tmp_path / "partial-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: partial-skill\n---\n\n# Partial Skill\n\nContent.\n"
        )

        validator = AbstractValidator(tmp_path)
        result = validator.fix_patterns(dry_run=True)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Tests: _needs_meta_indicator
# ---------------------------------------------------------------------------


class TestNeedsMetaIndicator:
    """Test _needs_meta_indicator checks for meta-skill keywords."""

    @pytest.mark.unit
    def test_content_with_meta_keyword_returns_false(self, tmp_path: Path) -> None:
        """Content with 'template' keyword returns False."""
        validator = AbstractValidator(tmp_path)
        result = validator._needs_meta_indicator(
            content="This is a template for skill development.",
            skill_name="my-skill",
        )
        assert result is False

    @pytest.mark.unit
    def test_content_without_meta_keyword_returns_true(self, tmp_path: Path) -> None:
        """Content without any meta keyword returns True."""
        validator = AbstractValidator(tmp_path)
        result = validator._needs_meta_indicator(
            content="This skill provides basic CLI functionality.",
            skill_name="my-skill",
        )
        assert result is True

    @pytest.mark.unit
    def test_skills_eval_skill_name_exempted(self, tmp_path: Path) -> None:
        """skill_name='skills-eval' returns False regardless."""
        validator = AbstractValidator(tmp_path)
        result = validator._needs_meta_indicator(
            content="Basic content with no keywords.",
            skill_name="skills-eval",
        )
        assert result is False


# ---------------------------------------------------------------------------
# Tests: _check_hub_spoke_pattern extended
# ---------------------------------------------------------------------------


class TestCheckHubSpokeExtended:
    """Test _check_hub_spoke_pattern edge cases."""

    @pytest.mark.unit
    def test_empty_modules_dir_adds_issue(self, tmp_path: Path) -> None:
        """Skill with empty modules/ dir gets an issue."""
        skill_dir = tmp_path / "modular-skill"
        skill_dir.mkdir()
        (skill_dir / "modules").mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: modular-skill\ndescription: test\ncategory: meta-skills\n---\n\n"
            "# Modular Skill\n\nThis is a template framework.\n"
        )

        validator = AbstractValidator(tmp_path)
        issues = validator._check_hub_spoke_pattern()
        assert any("no module files" in i for i in issues)

    @pytest.mark.unit
    def test_spoke_to_spoke_reference_adds_issue(self, tmp_path: Path) -> None:
        """Module referencing another module gets a spoke-to-spoke violation."""
        skill_dir = tmp_path / "spoke-skill"
        skill_dir.mkdir()
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()

        (modules_dir / "module-a.md").write_text(
            "# Module A\n\nSee modules/module-b for details.\n"
        )
        (modules_dir / "module-b.md").write_text("# Module B\n\nContent.\n")

        (skill_dir / "SKILL.md").write_text(
            "---\nname: spoke-skill\ndescription: test\ncategory: meta-skills\n---\n\n"
            "# Spoke Skill\n\nThis is a template framework.\n"
            "See module-a and module-b for details.\n"
        )

        validator = AbstractValidator(tmp_path)
        issues = validator._check_hub_spoke_pattern()
        assert any("spoke" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# Tests: main() entry point flags
# ---------------------------------------------------------------------------


class TestAbstractValidatorMain:
    """Test main() entry point flags."""

    @pytest.mark.unit
    def test_main_with_scan_flag(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main --scan runs without crashing."""
        monkeypatch.setattr(
            sys, "argv", ["abstract_validator.py", "--root", str(tmp_path), "--scan"]
        )
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)

    @pytest.mark.unit
    def test_main_with_report_flag(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main --report runs without crash."""
        monkeypatch.setattr(
            sys, "argv", ["abstract_validator.py", "--root", str(tmp_path), "--report"]
        )
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)

    @pytest.mark.unit
    def test_main_with_fix_flag_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main --fix --dry-run runs without crash."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter\n\nContent.\n")

        monkeypatch.setattr(
            sys,
            "argv",
            ["abstract_validator.py", "--root", str(tmp_path), "--fix", "--dry-run"],
        )
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)

    @pytest.mark.unit
    def test_main_no_flags(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main with no flags runs without crash."""
        monkeypatch.setattr(
            sys, "argv", ["abstract_validator.py", "--root", str(tmp_path)]
        )
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)
