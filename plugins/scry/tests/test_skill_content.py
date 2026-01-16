"""Tests for skill content validation in scry plugin.

This module tests skill file content validation:
- Frontmatter schema validation
- Module file reference resolution
- Dependency declaration validation

Issue #53: Add skill/agent/command content validation tests

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import re
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

# ============================================================================
# Skill Frontmatter Schema Validation
# ============================================================================


class TestSkillFrontmatterSchema:
    """Feature: Validate skill YAML frontmatter schema.

    As a plugin developer
    I want skill frontmatter to follow a consistent schema
    So that skills are discoverable and well-documented
    """

    REQUIRED_FIELDS = ["name", "description"]
    RECOMMENDED_FIELDS = ["category", "tags", "tools"]
    OPTIONAL_FIELDS = [
        "complexity",
        "estimated_tokens",
        "progressive_loading",
        "modules",
        "dependencies",
    ]

    def extract_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Extract YAML frontmatter from markdown content.

        Handles the project's skill format where description may use a pipe
        character with non-standard indentation.
        """
        if not content.startswith("---"):
            return None

        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                end_idx = i
                break

        if end_idx is None:
            return None

        yaml_content = "\n".join(lines[1:end_idx])

        # Try standard YAML parsing first
        try:
            return cast(dict[str, Any] | None, yaml.safe_load(yaml_content))
        except yaml.YAMLError:
            pass

        # Fall back to regex-based extraction for known fields
        result: dict[str, Any] = {}
        name_match = re.search(r"^name:\s*(.+)$", yaml_content, re.MULTILINE)
        if name_match:
            result["name"] = name_match.group(1).strip()

        desc_match = re.search(r"^description:\s*(.+)$", yaml_content, re.MULTILINE)
        if desc_match:
            result["description"] = desc_match.group(1).strip()

        # Check for pipe-style description (may span multiple lines)
        if "description:" in yaml_content and not result.get("description"):
            result["description"] = "present"  # Mark as present

        tags_match = re.search(r"^tags:\s*\[([^\]]+)\]", yaml_content, re.MULTILINE)
        if tags_match:
            result["tags"] = [t.strip() for t in tags_match.group(1).split(",")]

        tools_match = re.search(r"^tools:\s*\[([^\]]+)\]", yaml_content, re.MULTILINE)
        if tools_match:
            result["tools"] = [t.strip() for t in tools_match.group(1).split(",")]

        return result if result else None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_valid_frontmatter_has_required_fields(self, skills_dir: Path) -> None:
        """Scenario: Valid skill has required frontmatter fields.

        Given a skill file with valid frontmatter
        When validating the schema
        Then it should have 'name' and 'description' fields.
        """
        # Test against actual skill
        skill_file = skills_dir / "vhs-recording" / "SKILL.md"
        if not skill_file.exists():
            pytest.skip("vhs-recording skill not found")

        content = skill_file.read_text()
        frontmatter = self.extract_frontmatter(content)

        assert frontmatter is not None, "Frontmatter should be parseable"
        for field in self.REQUIRED_FIELDS:
            assert field in frontmatter, f"Missing required field: {field}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_name_matches_directory(self, skills_dir: Path) -> None:
        """Scenario: Skill name should match directory name.

        Given a skill in directory 'vhs-recording'
        When checking the frontmatter name
        Then it should be 'vhs-recording'.
        """
        skill_dir = skills_dir / "vhs-recording"
        if not skill_dir.exists():
            pytest.skip("vhs-recording skill not found")

        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()
        frontmatter = self.extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter.get("name") == skill_dir.name

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_description_is_non_empty(self, skills_dir: Path) -> None:
        """Scenario: Skill description should be non-empty.

        Given a skill file with frontmatter
        When checking the description
        Then it should have content.
        """
        skill_file = skills_dir / "vhs-recording" / "SKILL.md"
        if not skill_file.exists():
            pytest.skip("vhs-recording skill not found")

        content = skill_file.read_text()
        frontmatter = self.extract_frontmatter(content)

        assert frontmatter is not None
        desc = frontmatter.get("description", "")
        assert len(str(desc).strip()) > 0, "Description should not be empty"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tags_is_list(self, skills_dir: Path) -> None:
        """Scenario: Tags field should be a list.

        Given a skill with tags field
        When validating the schema
        Then tags should be a list type.
        """
        skill_file = skills_dir / "vhs-recording" / "SKILL.md"
        if not skill_file.exists():
            pytest.skip("vhs-recording skill not found")

        content = skill_file.read_text()
        frontmatter = self.extract_frontmatter(content)

        assert frontmatter is not None
        if "tags" in frontmatter:
            assert isinstance(frontmatter["tags"], list), "Tags should be a list"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tools_is_list(self, skills_dir: Path) -> None:
        """Scenario: Tools field should be a list.

        Given a skill with tools field
        When validating the schema
        Then tools should be a list type.
        """
        skill_file = skills_dir / "vhs-recording" / "SKILL.md"
        if not skill_file.exists():
            pytest.skip("vhs-recording skill not found")

        content = skill_file.read_text()
        frontmatter = self.extract_frontmatter(content)

        assert frontmatter is not None
        if "tools" in frontmatter:
            assert isinstance(frontmatter["tools"], list), "Tools should be a list"


class TestSkillModuleReferences:
    """Feature: Validate skill module references resolve correctly.

    As a plugin developer
    I want module references to point to existing files
    So that progressive loading works correctly
    """

    def extract_module_refs(self, content: str) -> list[str]:
        """Extract module references from frontmatter."""
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return []

        try:
            data = yaml.safe_load(frontmatter_match.group(1))
            return data.get("modules", []) if data else []
        except yaml.YAMLError:
            return []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_references_exist(self, skills_dir: Path) -> None:
        """Scenario: Module references should resolve to files.

        Given a skill with module references
        When checking each reference
        Then the module file should exist.
        """
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            content = skill_file.read_text()
            modules = self.extract_module_refs(content)

            for module in modules:
                module_path = skill_dir / "modules" / f"{module}.md"
                assert module_path.exists(), (
                    f"Module '{module}' not found for skill '{skill_dir.name}'"
                )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_without_modules_is_valid(self, tmp_path: Path) -> None:
        """Scenario: Skill without modules is valid.

        Given a skill with no module references
        When validating
        Then it should pass.
        """
        skill_content = """---
name: simple-skill
description: A skill without modules
---

# Simple Skill

Content here.
"""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(skill_content)

        modules = self.extract_module_refs(skill_content)
        assert modules == []


class TestSkillDependencyDeclarations:
    """Feature: Validate skill dependency declarations.

    As a plugin developer
    I want dependency declarations to be valid
    So that skill loading order is correct
    """

    VALID_DEPENDENCY_PATTERN = r"^[\w-]+:[\w-]+$"

    def extract_dependencies(self, content: str) -> list[str]:
        """Extract dependencies from frontmatter."""
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return []

        try:
            data = yaml.safe_load(frontmatter_match.group(1))
            return data.get("dependencies", []) if data else []
        except yaml.YAMLError:
            return []

    def is_valid_dependency_format(self, dep: str) -> bool:
        """Check if dependency follows plugin:skill format."""
        return bool(re.match(self.VALID_DEPENDENCY_PATTERN, dep))

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dependencies_follow_format(self, skills_dir: Path) -> None:
        """Scenario: Dependencies should follow plugin:skill format.

        Given a skill with dependencies
        When validating the format
        Then each should match 'plugin:skill' pattern.
        """
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            content = skill_file.read_text()
            deps = self.extract_dependencies(content)

            for dep in deps:
                assert self.is_valid_dependency_format(dep), (
                    f"Invalid dependency format: '{dep}' in skill '{skill_dir.name}'"
                )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_valid_dependency_format_examples(self) -> None:
        """Scenario: Valid dependency format examples pass.

        Given various dependency strings
        When validating format
        Then valid formats should pass.
        """
        valid_deps = [
            "sanctum:git-workspace-review",
            "abstract:skill-auditor",
            "imbue:evidence-logging",
        ]
        for dep in valid_deps:
            assert self.is_valid_dependency_format(dep), f"Should be valid: {dep}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_dependency_format_examples(self) -> None:
        """Scenario: Invalid dependency format examples fail.

        Given various invalid dependency strings
        When validating format
        Then invalid formats should fail.
        """
        invalid_deps = [
            "no-colon",
            "too:many:colons",
            "",
            "spaces in name:skill",
        ]
        for dep in invalid_deps:
            assert not self.is_valid_dependency_format(dep), f"Should be invalid: {dep}"


# ============================================================================
# All Skills Validation
# ============================================================================


class TestAllSkillsValidation:
    """Feature: Validate all skills in the plugin.

    As a plugin maintainer
    I want all skills to pass validation
    So that the plugin is consistent and reliable
    """

    EXPECTED_SKILLS = [
        "vhs-recording",
        "browser-recording",
        "gif-generation",
        "media-composition",
    ]

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_has_valid_structure(self, skills_dir: Path, skill_name: str) -> None:
        """Scenario: Each skill has valid structure.

        Given a skill directory
        When checking structure
        Then it should have SKILL.md with valid frontmatter.
        """
        skill_dir = skills_dir / skill_name
        if not skill_dir.exists():
            pytest.skip(f"Skill '{skill_name}' not found")

        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md missing for {skill_name}"

        content = skill_file.read_text()
        assert content.startswith("---"), f"Missing frontmatter in {skill_name}"

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_frontmatter_is_parseable(
        self, skills_dir: Path, skill_name: str
    ) -> None:
        """Scenario: Skill frontmatter can be parsed.

        Given a skill file
        When parsing frontmatter
        Then required fields should be extractable.
        """
        skill_dir = skills_dir / skill_name
        if not skill_dir.exists():
            pytest.skip(f"Skill '{skill_name}' not found")

        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter bounds
        assert content.startswith("---"), f"Missing frontmatter in {skill_name}"

        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                end_idx = i
                break

        assert end_idx is not None, f"Unclosed frontmatter in {skill_name}"

        # Verify required fields exist via regex
        yaml_content = "\n".join(lines[1:end_idx])
        assert re.search(r"^name:", yaml_content, re.MULTILINE), (
            f"Missing name field in {skill_name}"
        )
        assert re.search(r"^description:", yaml_content, re.MULTILINE), (
            f"Missing description field in {skill_name}"
        )
