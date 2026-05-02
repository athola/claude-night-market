"""Tests for the skill_validator script."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from pathlib import Path as _Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from skill_validator import (
    SkillValidator,
    ValidationResult,
    print_report,
)
from skill_validator import (
    main as validator_main,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_skill(tmp_path: Path, content: str) -> Path:
    """Create a SKILL.md with given content."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content)
    return skill_file


VALID_FRONTMATTER = """\
---
name: test-skill
description: Guides developers through testing practices. Provides clear examples and methodologies. Use when you need to test your code thoroughly.
version: 1.0.0
category: testing
tags:
  - test
estimated_tokens: 800
---

## Overview

This skill guides developers.

## When to Use

Use this skill when you need to test code.

```python
# example
print("hello")
```
"""


# ---------------------------------------------------------------------------
# Tests: ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    """Tests for ValidationResult container."""

    @pytest.mark.unit
    def test_no_errors_on_init(self) -> None:
        """Fresh ValidationResult has no errors."""
        result = ValidationResult()
        assert result.errors == []
        assert result.warnings == []
        assert result.info == []

    @pytest.mark.unit
    def test_add_error(self) -> None:
        """add_error stores message in errors list."""
        result = ValidationResult()
        result.add_error("Something is broken")
        assert "Something is broken" in result.errors
        assert result.has_errors is True

    @pytest.mark.unit
    def test_add_warning(self) -> None:
        """add_warning stores message in warnings list."""
        result = ValidationResult()
        result.add_warning("Minor issue")
        assert "Minor issue" in result.warnings
        assert result.has_warnings is True
        assert result.has_errors is False

    @pytest.mark.unit
    def test_add_info(self) -> None:
        """add_info stores message in info list."""
        result = ValidationResult()
        result.add_info("All good")
        assert "All good" in result.info

    @pytest.mark.unit
    def test_exit_code_no_issues(self) -> None:
        """No issues returns exit code 0."""
        result = ValidationResult()
        assert result.exit_code() == 0

    @pytest.mark.unit
    def test_exit_code_warnings_only(self) -> None:
        """Warnings only returns exit code 1."""
        result = ValidationResult()
        result.add_warning("Minor issue")
        assert result.exit_code() == 1

    @pytest.mark.unit
    def test_exit_code_errors(self) -> None:
        """Errors present returns exit code 2."""
        result = ValidationResult()
        result.add_error("Critical issue")
        assert result.exit_code() == 2


# ---------------------------------------------------------------------------
# Tests: SkillValidator - file existence
# ---------------------------------------------------------------------------


class TestSkillValidatorFileExistence:
    """Tests for SKILL.md existence checks."""

    @pytest.mark.unit
    def test_missing_skill_file_adds_error(self, tmp_path: Path) -> None:
        """Missing SKILL.md adds an error."""
        skill_file = tmp_path / "SKILL.md"
        v = SkillValidator(skill_file)
        result = v.validate()
        assert result.has_errors
        assert any("SKILL.md not found" in e for e in result.errors)

    @pytest.mark.unit
    def test_wrong_filename_adds_warning(self, tmp_path: Path) -> None:
        """File not named SKILL.md adds a warning."""
        skill_file = tmp_path / "skill.md"
        skill_file.write_text(VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("SKILL.md" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Tests: SkillValidator - _read_file exception path
# ---------------------------------------------------------------------------


class TestReadFileException:
    """Tests for _read_file handling read errors."""

    @pytest.mark.unit
    def test_unreadable_file_adds_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """File that cannot be read adds error and returns None."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("valid content")

        validator = SkillValidator(skill_file)
        validator._check_file_exists()

        original_read_text = _Path.read_text

        def raising_read_text(self, *args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(_Path, "read_text", raising_read_text)
        try:
            result = validator._read_file()
        finally:
            monkeypatch.setattr(_Path, "read_text", original_read_text)

        assert result is None
        assert validator.result.has_errors


# ---------------------------------------------------------------------------
# Tests: SkillValidator - frontmatter validation
# ---------------------------------------------------------------------------


class TestSkillValidatorFrontmatter:
    """Tests for YAML frontmatter validation."""

    @pytest.mark.unit
    def test_missing_frontmatter_adds_error(self, tmp_path: Path) -> None:
        """No frontmatter adds an error."""
        skill_file = _make_skill(tmp_path, "# Just a heading\nNo frontmatter.\n")
        v = SkillValidator(skill_file)
        result = v.validate()
        assert result.has_errors

    @pytest.mark.unit
    def test_invalid_yaml_adds_error(self, tmp_path: Path) -> None:
        """Malformed YAML in frontmatter adds error."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test\n\tinvalid: yaml: here:\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert result.has_errors

    @pytest.mark.unit
    def test_missing_required_field_adds_error(self, tmp_path: Path) -> None:
        """Missing required field (version) adds error."""
        content = (
            "---\nname: test-skill\ndescription: A skill.\n"
            "category: testing\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("version" in e for e in result.errors)

    @pytest.mark.unit
    def test_valid_frontmatter_no_errors(self, tmp_path: Path) -> None:
        """Valid frontmatter with all required fields has no errors."""
        skill_file = _make_skill(tmp_path, VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert not result.has_errors

    @pytest.mark.unit
    def test_invalid_name_adds_error(self, tmp_path: Path) -> None:
        """Name with uppercase letters adds an error."""
        content = (
            "---\nname: InvalidName\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Name must be lowercase" in e for e in result.errors)

    @pytest.mark.unit
    def test_name_with_leading_hyphen_adds_error(self, tmp_path: Path) -> None:
        """Name starting with hyphen adds an error."""
        content = (
            "---\nname: -bad-name\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("cannot start or end with hyphen" in e for e in result.errors)

    @pytest.mark.unit
    def test_name_not_string_adds_error(self, tmp_path: Path) -> None:
        """Name as integer adds error about string type."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: 123\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("string" in e.lower() for e in result.errors)

    @pytest.mark.unit
    def test_name_too_long_adds_error(self, tmp_path: Path) -> None:
        """Name longer than MAX_NAME_LENGTH adds error."""
        long_name = "a" * 65
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {long_name}\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("too long" in e.lower() for e in result.errors)

    @pytest.mark.unit
    def test_name_with_consecutive_hyphens_adds_warning(self, tmp_path: Path) -> None:
        """Name with -- adds warning about consecutive hyphens."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my--skill\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("consecutive hyphens" in w for w in result.warnings)

    @pytest.mark.unit
    def test_invalid_version_adds_error(self, tmp_path: Path) -> None:
        """Invalid version format adds an error."""
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 'bad'\n"
            "category: testing\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Version" in e and "invalid" in e for e in result.errors)

    @pytest.mark.unit
    def test_version_as_integer_adds_error(self, tmp_path: Path) -> None:
        """Version as integer (not string) adds error."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: test\nversion: 1\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert result.has_errors

    @pytest.mark.unit
    def test_non_list_tags_adds_error(self, tmp_path: Path) -> None:
        """Tags that are not a list add an error."""
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: not-a-list\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Tags must be a list" in e for e in result.errors)

    @pytest.mark.unit
    def test_empty_tags_adds_warning(self, tmp_path: Path) -> None:
        """Empty tags list adds a warning."""
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("No tags" in w for w in result.warnings)

    @pytest.mark.unit
    def test_negative_estimated_tokens_adds_error(self, tmp_path: Path) -> None:
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: []\nestimated_tokens: -1\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("must be positive" in e for e in result.errors)

    @pytest.mark.unit
    def test_high_token_estimate_adds_warning(self, tmp_path: Path) -> None:
        """Very high estimated_tokens adds a warning."""
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 1.0.0\n"
            "category: testing\ntags: []\nestimated_tokens: 10000\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("modularization" in w.lower() for w in result.warnings)

    @pytest.mark.unit
    def test_first_person_description_adds_error(self, tmp_path: Path) -> None:
        """Description with 'I' in first sentence adds an error."""
        content = (
            "---\nname: test-skill\n"
            "description: I help you do things. Use when you want help.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("first/second person" in e for e in result.errors)

    @pytest.mark.unit
    def test_non_string_category_adds_error(self, tmp_path: Path) -> None:
        content = (
            "---\nname: test-skill\ndescription: A skill.\nversion: 1.0.0\n"
            "category: 123\ntags: []\nestimated_tokens: 100\n---\n# Skill\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Category" in e for e in result.errors)

    @pytest.mark.unit
    def test_description_not_string_adds_error(self, tmp_path: Path) -> None:
        """Description as list adds error about type."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription:\n  - item one\n  - item two\n"
            "version: 1.0.0\ncategory: tools\ntags: [test]\nestimated_tokens: 100\n"
            "---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert result.has_errors

    @pytest.mark.unit
    def test_description_too_long_adds_error(self, tmp_path: Path) -> None:
        """Description exceeding MAX_DESC_LENGTH adds error."""
        very_long_desc = "x " * 600
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            f"---\nname: my-skill\ndescription: {very_long_desc}\n"
            "version: 1.0.0\ncategory: tools\ntags: [test]\nestimated_tokens: 100\n"
            "---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("too long" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Tests: SkillValidator - body validation
# ---------------------------------------------------------------------------


class TestSkillValidatorBody:
    """Tests for skill body content validation."""

    @pytest.mark.unit
    def test_missing_overview_section_adds_warning(self, tmp_path: Path) -> None:
        content = (
            "---\nname: test-skill\n"
            "description: Guides you through things. Use when needed.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n"
            "## When to Use\n\nSome content.\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Overview" in w for w in result.warnings)

    @pytest.mark.unit
    def test_no_code_examples_adds_warning(self, tmp_path: Path) -> None:
        """No code blocks adds a warning."""
        content = (
            "---\nname: test-skill\n"
            "description: Guides you through things. Use when needed.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n"
            "## Overview\n\nContent.\n\n## When to Use\n\nSome.\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("code examples" in w for w in result.warnings)

    @pytest.mark.unit
    def test_broken_local_reference_adds_error(self, tmp_path: Path) -> None:
        """Broken local file link adds an error."""
        content = (
            "---\nname: test-skill\n"
            "description: Guides developers. Use when testing.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n"
            "## Overview\n\n[Link](nonexistent.md)\n\n## When to Use\n\nHere.\n\n```\ncode\n```\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("Broken reference" in e for e in result.errors)

    @pytest.mark.unit
    def test_http_links_not_broken(self, tmp_path: Path) -> None:
        """HTTP links are not checked for existence."""
        content = (
            "---\nname: test-skill\n"
            "description: Guides developers. Use when testing.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n"
            "## Overview\n\n[Link](https://example.com)\n\n## When to Use\n\nHere.\n\n```\ncode\n```\n"
        )
        skill_file = _make_skill(tmp_path, content)
        v = SkillValidator(skill_file)
        result = v.validate()
        broken_ref_errors = [e for e in result.errors if "Broken reference" in e]
        assert len(broken_ref_errors) == 0

    @pytest.mark.unit
    def test_normal_line_count_adds_info(self, tmp_path: Path) -> None:
        """Normal-length body adds info about line count."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n"
            "# Skill\n\nContent.\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("line count" in i.lower() for i in result.info)


# ---------------------------------------------------------------------------
# Tests: SkillValidator - modules
# ---------------------------------------------------------------------------


class TestSkillValidatorModules:
    """Tests for module file validation."""

    @pytest.mark.unit
    def test_empty_modules_dir_adds_warning(self, tmp_path: Path) -> None:
        """Empty modules/ directory adds a warning."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "modules").mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("empty" in w for w in result.warnings)

    @pytest.mark.unit
    def test_valid_module_files_ok(self, tmp_path: Path) -> None:
        """Module with correct line count is OK."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir()
        module = modules_dir / "core.md"
        module.write_text("# Core\n" + "Content.\n" * 149)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert not any("core.md" in e for e in result.errors)

    @pytest.mark.unit
    def test_referenced_module_missing_adds_error(self, tmp_path: Path) -> None:
        """Reference to non-existent module adds an error."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        content = (
            "---\nname: test-skill\n"
            "description: Guides developers. Use when testing.\n"
            "version: 1.0.0\ncategory: testing\ntags: [test]\n"
            "estimated_tokens: 800\n---\n"
            "## Overview\n\nSee `modules/missing.md`.\n\n## When to Use\n\nHere.\n\n```\ncode\n```\n"
        )
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)
        v = SkillValidator(skill_file)
        result = v.validate()
        assert any("modules/" in e for e in result.errors)

    @pytest.mark.unit
    def test_references_modules_without_dir_adds_error(self, tmp_path: Path) -> None:
        """SKILL.md references modules/ but dir does not exist adds error."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n"
            "# Skill\n\nSee `modules/details.md`.\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert result.has_errors

    @pytest.mark.unit
    def test_modules_dir_with_missing_referenced_module_adds_error(
        self, tmp_path: Path
    ) -> None:
        """modules/ dir exists but referenced module is absent adds error."""
        skill_file = tmp_path / "SKILL.md"
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        (modules_dir / "other.md").write_text("# Other\n\n" + "Line.\n" * 120)

        skill_file.write_text(
            "---\nname: my-skill\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n"
            "# Skill\n\nSee `modules/missing.md`.\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert any("missing.md" in e for e in result.errors)

    @pytest.mark.unit
    def test_module_read_error_adds_error(self, tmp_path: Path) -> None:
        """Module that cannot be read (directory instead of file) adds error."""
        skill_file = tmp_path / "SKILL.md"
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        bad_module = modules_dir / "bad.md"
        bad_module.mkdir()

        skill_file.write_text(
            "---\nname: my-skill\ndescription: test\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n# Skill\n"
        )
        validator = SkillValidator(skill_file)
        result = validator.validate()
        assert result.has_errors


# ---------------------------------------------------------------------------
# Tests: print_report
# ---------------------------------------------------------------------------


class TestPrintReport:
    """Tests for print_report output."""

    @pytest.mark.unit
    def test_print_report_no_crash(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """print_report does not crash with mixed results."""
        skill_file = _make_skill(tmp_path, VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = v.validate()
        result.add_warning("test warning")
        result.add_info("test info")
        print_report(v, result)

    @pytest.mark.unit
    def test_print_report_with_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """print_report with errors does not crash."""
        skill_file = _make_skill(tmp_path, VALID_FRONTMATTER)
        v = SkillValidator(skill_file)
        result = ValidationResult()
        result.add_error("Critical error")
        print_report(v, result)


# ---------------------------------------------------------------------------
# Tests: main() entry point
# ---------------------------------------------------------------------------


class TestSkillValidatorMain:
    """Tests for main() entry point."""

    @pytest.mark.unit
    def test_main_exits_2_for_missing_skill(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() with nonexistent skill exits 2."""
        missing = tmp_path / "SKILL.md"
        monkeypatch.setattr(sys, "argv", ["skill_validator.py", "--path", str(missing)])
        with pytest.raises(SystemExit) as exc_info:
            validator_main()
        assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_main_strict_with_warnings_exits_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main --strict with warnings-only skill exits 1 or 2."""
        skill_file = tmp_path / "SKILL.md"
        long_desc = "Guides and teaches developers through testing workflows. " * 4
        skill_file.write_text(
            f"---\nname: my-skill\ndescription: {long_desc}\nversion: 1.0.0\n"
            "category: tools\ntags: [test]\nestimated_tokens: 100\n---\n\n"
            "# Skill\n\n## Overview\n\nContent.\n\n## When to Use\n\nUse when needed.\n\n"
            "```\ncode\n```\n"
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["skill_validator.py", "--path", str(skill_file), "--strict"],
        )
        with pytest.raises(SystemExit) as exc_info:
            validator_main()
        assert exc_info.value.code in (1, 2)

    @pytest.mark.unit
    def test_main_default_cwd_no_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() with no --path uses cwd/SKILL.md, exits 2 if missing."""
        monkeypatch.setattr(sys, "argv", ["skill_validator.py"])
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc_info:
                validator_main()
            assert exc_info.value.code == 2
        finally:
            os.chdir(original)
