"""Tests for frontmatter validation in spec-kit skill files."""

import json
import re
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def shipped_skills_dir() -> Path:
    """The plugin's real skills directory, not a fixture copy.

    These tests used a conftest fixture that wrote three minimal SKILL.md
    files into tmp_path, so they checked text the fixture had just
    written and stayed green whatever the shipped skills said.
    """
    return PLUGIN_ROOT / "skills"


@pytest.fixture
def shipped_plugin_manifest() -> dict:
    """The plugin's real ``.claude-plugin/plugin.json``."""
    return json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())


class TestFrontmatterValidation:
    """Test frontmatter validation for spec-kit skills."""

    def test_should_have_valid_frontmatter_when_loading_spec_writing_skill(
        self, shipped_skills_dir
    ) -> None:
        """Test spec-writing skill has valid frontmatter."""
        # Given: a spec-writing skill file
        skill_file = shipped_skills_dir / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # When: extracting frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        # Then: frontmatter should exist
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # And: should have all required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # And: field values should match expectations
        assert "name: spec-writing" in frontmatter, "Name should match directory"
        assert "category: specification" in frontmatter, (
            "Category should be specification"
        )

    def test_should_have_valid_frontmatter_when_loading_task_planning_skill(
        self, shipped_skills_dir
    ) -> None:
        """Test task-planning skill has valid frontmatter."""
        # Given: a task-planning skill file
        skill_file = shipped_skills_dir / "task-planning" / "SKILL.md"
        content = skill_file.read_text()

        # When: extracting frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        # Then: frontmatter should exist
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # And: should have all required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # And: field values should match expectations
        assert "name: task-planning" in frontmatter, "Name should match directory"
        assert "category: planning" in frontmatter, "Category should be planning"

    def test_should_have_valid_frontmatter_when_loading_orchestrator_skill(
        self, shipped_skills_dir
    ) -> None:
        """Test speckit-orchestrator skill has valid frontmatter."""
        # Given: a speckit-orchestrator skill file
        skill_file = shipped_skills_dir / "speckit-orchestrator" / "SKILL.md"
        content = skill_file.read_text()

        # When: extracting frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        # Then: frontmatter should exist
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # And: should have all required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # And: field values should match expectations
        assert "name: speckit-orchestrator" in frontmatter, (
            "Name should match directory"
        )
        assert "category: workflow" in frontmatter, "Category should be workflow"

    def test_should_parse_as_valid_yaml_when_validating_frontmatter(
        self, shipped_skills_dir
    ) -> None:
        """Test frontmatter is valid YAML."""
        # Given: all skill directories
        skill_dirs = ["spec-writing", "task-planning", "speckit-orchestrator"]

        for skill_name in skill_dirs:
            # When: reading skill file frontmatter
            skill_file = shipped_skills_dir / skill_name / "SKILL.md"
            content = skill_file.read_text()

            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            assert frontmatter_match, f"{skill_name} should have frontmatter"

            frontmatter = frontmatter_match.group(1)

            # Then: should be valid YAML
            try:
                parsed = yaml.safe_load(frontmatter)
                assert parsed is not None, (
                    f"Frontmatter should be parseable for {skill_name}"
                )
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {skill_name} frontmatter: {e}")

    def test_should_format_optional_fields_correctly_when_present(
        self, shipped_skills_dir
    ) -> None:
        """Test optional frontmatter fields are properly formatted."""
        # Given: a skill file with frontmatter
        skill_file = shipped_skills_dir / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # When: extracting and parsing frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = frontmatter_match.group(1)
        parsed = yaml.safe_load(frontmatter)

        # Then: optional fields should have correct types if present
        optional_fields = [
            "tags",
            "dependencies",
            "tools",
            "complexity",
            "estimated_tokens",
        ]

        for field in optional_fields:
            if field in parsed:
                value = parsed[field]
                if field in ["tags", "dependencies", "tools"]:
                    assert isinstance(value, list), f"{field} should be a list"
                elif field in ["complexity"]:
                    assert isinstance(value, str), f"{field} should be a string"
                elif field == "estimated_tokens":
                    assert isinstance(value, (int, str)), (
                        f"{field} should be a number or string"
                    )

    def test_should_match_content_when_validating_frontmatter_consistency(
        self, shipped_skills_dir
    ) -> None:
        """Test frontmatter content is consistent with skill content."""
        # Given: a skill file with frontmatter and content
        skill_file = shipped_skills_dir / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # When: extracting frontmatter and content
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = frontmatter_match.group(1)
        main_content = content[frontmatter_match.end() :].strip()

        # Then: description should be meaningful
        desc_match = re.search(r"description:\s*(.+)", frontmatter)
        if desc_match:
            description = desc_match.group(1).strip().strip("\"'")
            assert len(description) > 10, "Description should be meaningful"

        # And: content should have main heading
        heading_match = re.search(r"^# (.+)$", main_content, re.MULTILINE)
        assert heading_match, "Skill should have main heading"

    def test_should_follow_consistent_structure_when_comparing_skills(
        self, shipped_skills_dir
    ) -> None:
        """Test all skills follow consistent frontmatter structure."""
        # Given: all skill directories
        skill_dirs = ["spec-writing", "task-planning", "speckit-orchestrator"]
        frontmatter_structures = []

        # When: extracting frontmatter from each skill
        for skill_name in skill_dirs:
            skill_file = shipped_skills_dir / skill_name / "SKILL.md"
            content = skill_file.read_text()

            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            frontmatter = frontmatter_match.group(1)

            parsed = yaml.safe_load(frontmatter)
            frontmatter_structures.append(set(parsed.keys()))

        # Then: all skills should have same basic structure
        common_fields = set.intersection(*frontmatter_structures)
        expected_common = {"name", "description", "category"}

        assert expected_common.issubset(common_fields), (
            f"Skills should have common fields: {expected_common}"
        )

    def test_should_have_required_fields_when_validating_plugin_manifest(
        self, shipped_plugin_manifest
    ) -> None:
        """Test plugin manifest follows expected structure."""
        # Given: a plugin manifest
        manifest = shipped_plugin_manifest

        # When: checking for required fields
        required_fields = [
            "name",
            "version",
            "description",
            "commands",
            "skills",
            "agents",
        ]

        # Then: all required fields should be present
        for field in required_fields:
            assert field in manifest, f"Plugin manifest missing required field: {field}"

        # And: field types should be correct
        assert isinstance(manifest["commands"], list), "Commands should be a list"
        assert isinstance(manifest["skills"], list), "Skills should be a list"
        assert isinstance(manifest["agents"], list), "Agents should be a list"

        # And: version should follow semantic versioning
        version_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(version_pattern, manifest["version"]), (
            f"Invalid version format: {manifest['version']}"
        )

    def test_should_reference_existing_skills_when_validating_manifest(
        self,
        shipped_plugin_manifest,
        shipped_skills_dir,
    ) -> None:
        # Given: manifest skills and skill files
        manifest_skills = shipped_plugin_manifest["skills"]

        # When: checking each skill reference
        for skill_ref in manifest_skills:
            # Extract skill name from path
            skill_name = skill_ref.split("/")[-1] if "/" in skill_ref else skill_ref
            skill_dir = shipped_skills_dir / skill_name

            # Then: skill directory should exist
            assert skill_dir.exists(), (
                f"Manifest references non-existent skill: {skill_ref}"
            )

            # And: should have SKILL.md file
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Skill missing SKILL.md: {skill_ref}"

    def test_should_reference_markdown_commands_when_validating_manifest(
        self, shipped_plugin_manifest
    ) -> None:
        """Test that manifest references existing command files."""
        # Given: manifest commands
        manifest_commands = shipped_plugin_manifest["commands"]

        # When/Then: each command should follow conventions
        for command_ref in manifest_commands:
            # Should be a markdown file
            assert command_ref.endswith(".md"), (
                f"Command should be markdown: {command_ref}"
            )

            # Should be in commands directory
            assert command_ref.startswith("./commands/"), (
                f"Command should be in commands directory: {command_ref}"
            )

            # And should exist on disk
            assert (PLUGIN_ROOT / command_ref).is_file(), (
                f"Manifest references a missing command: {command_ref}"
            )
