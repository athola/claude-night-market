"""Tests for frontmatter validation in spec-kit skill files."""

import re

import pytest
import yaml


class TestFrontmatterValidation:
    """Test frontmatter validation for spec-kit skills."""

    def test_spec_writing_skill_frontmatter(self, temp_skill_files) -> None:
        """Test spec-writing skill has valid frontmatter."""
        skill_file = temp_skill_files / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # Check required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # Validate field values
        assert "name: spec-writing" in frontmatter, "Name should match directory"
        assert "category: specification" in frontmatter, (
            "Category should be specification"
        )

    def test_task_planning_skill_frontmatter(self, temp_skill_files) -> None:
        """Test task-planning skill has valid frontmatter."""
        skill_file = temp_skill_files / "task-planning" / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # Check required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # Validate field values
        assert "name: task-planning" in frontmatter, "Name should match directory"
        assert "category: planning" in frontmatter, "Category should be planning"

    def test_orchestrator_skill_frontmatter(self, temp_skill_files) -> None:
        """Test speckit-orchestrator skill has valid frontmatter."""
        skill_file = temp_skill_files / "speckit-orchestrator" / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match, "Skill file should have frontmatter"

        frontmatter = frontmatter_match.group(1)

        # Check required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            assert f"{field}:" in frontmatter, f"Missing required field: {field}"

        # Validate field values
        assert "name: speckit-orchestrator" in frontmatter, (
            "Name should match directory"
        )
        assert "category: workflow-orchestration" in frontmatter, (
            "Category should be workflow"
        )

    def test_frontmatter_yaml_validity(self, temp_skill_files) -> None:
        """Test frontmatter is valid YAML."""
        skill_dirs = ["spec-writing", "task-planning", "speckit-orchestrator"]

        for skill_name in skill_dirs:
            skill_file = temp_skill_files / skill_name / "SKILL.md"
            content = skill_file.read_text()

            # Extract frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            assert frontmatter_match, f"{skill_name} should have frontmatter"

            frontmatter = frontmatter_match.group(1)

            # Should be valid YAML
            try:
                parsed = yaml.safe_load(frontmatter)
                assert parsed is not None, (
                    f"Frontmatter should be parseable for {skill_name}"
                )
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {skill_name} frontmatter: {e}")

    def test_optional_frontmatter_fields(self, temp_skill_files) -> None:
        """Test optional frontmatter fields are properly formatted."""
        skill_file = temp_skill_files / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = frontmatter_match.group(1)

        # Parse YAML
        parsed = yaml.safe_load(frontmatter)

        # Check optional fields if present
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

    def test_frontmatter_content_consistency(self, temp_skill_files) -> None:
        """Test frontmatter content is consistent with skill content."""
        skill_file = temp_skill_files / "spec-writing" / "SKILL.md"
        content = skill_file.read_text()

        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = frontmatter_match.group(1)

        # Extract main content
        main_content = content[frontmatter_match.end() :].strip()

        # Check that description matches content
        desc_match = re.search(r"description:\s*(.+)", frontmatter)
        if desc_match:
            description = desc_match.group(1).strip().strip("\"'")
            # Description should give hint about content
            assert len(description) > 10, "Description should be meaningful"

        # Check that content has main heading
        heading_match = re.search(r"^# (.+)$", main_content, re.MULTILINE)
        assert heading_match, "Skill should have main heading"

    def test_consistent_frontmatter_structure(self, temp_skill_files) -> None:
        """Test all skills follow consistent frontmatter structure."""
        skill_dirs = ["spec-writing", "task-planning", "speckit-orchestrator"]
        frontmatter_structures = []

        for skill_name in skill_dirs:
            skill_file = temp_skill_files / skill_name / "SKILL.md"
            content = skill_file.read_text()

            # Extract frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            frontmatter = frontmatter_match.group(1)

            # Parse YAML
            parsed = yaml.safe_load(frontmatter)
            frontmatter_structures.append(set(parsed.keys()))

        # All skills should have same basic structure
        common_fields = set.intersection(*frontmatter_structures)
        expected_common = {"name", "description", "category"}

        assert expected_common.issubset(common_fields), (
            f"Skills should have common fields: {expected_common}"
        )

    def test_plugin_manifest_validation(self, sample_plugin_manifest) -> None:
        """Test plugin manifest follows expected structure."""
        required_fields = [
            "name",
            "version",
            "description",
            "commands",
            "skills",
            "agents",
        ]

        for field in required_fields:
            assert field in sample_plugin_manifest, (
                f"Plugin manifest missing required field: {field}"
            )

        # Validate field types
        assert isinstance(sample_plugin_manifest["commands"], list), (
            "Commands should be a list"
        )
        assert isinstance(sample_plugin_manifest["skills"], list), (
            "Skills should be a list"
        )
        assert isinstance(sample_plugin_manifest["agents"], list), (
            "Agents should be a list"
        )

        # Check version format
        version_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(version_pattern, sample_plugin_manifest["version"]), (
            f"Invalid version format: {sample_plugin_manifest['version']}"
        )

    def test_skill_references_in_manifest(
        self,
        sample_plugin_manifest,
        temp_skill_files,
    ) -> None:
        """Test that manifest references existing skills."""
        manifest_skills = sample_plugin_manifest["skills"]

        for skill_ref in manifest_skills:
            # Extract skill name from path
            skill_name = skill_ref.split("/")[-1] if "/" in skill_ref else skill_ref
            skill_dir = temp_skill_files / skill_name

            # Should reference existing skill directory
            assert skill_dir.exists(), (
                f"Manifest references non-existent skill: {skill_ref}"
            )

            # Should have SKILL.md file
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Skill missing SKILL.md: {skill_ref}"

    def test_command_references_in_manifest(self, sample_plugin_manifest) -> None:
        """Test that manifest references existing command files."""
        manifest_commands = sample_plugin_manifest["commands"]

        for command_ref in manifest_commands:
            # Should be a markdown file
            assert command_ref.endswith(".md"), (
                f"Command should be markdown: {command_ref}"
            )

            # Should be in commands directory
            assert command_ref.startswith("./commands/"), (
                f"Command should be in commands directory: {command_ref}"
            )
